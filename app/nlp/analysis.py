import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import datetime
from .normalization import TEXT_PIPELINE
from . import sum_basic, divrank
from sklearn.cluster import KMeans, MiniBatchKMeans
import time
import numpy as np
import pytz
import os

TZ = pytz.timezone('Europe/Moscow')


class Analyzer():

    """ Class-wrapper for nlp data-processing """

    def __init__(self, config={
            'kmeans': {
                'proximity_coeff': 0.6, 'n_clusters_coeff': 4,
                'batch_size': 32, 'n_init': 10, 'max_iter': 100
            },
            'append_titles': True,
            'svm_path': './models/SVM_classifier.bin',
            'svm_labels_path': './models/LabelEncoder.bin',
            'tfidf_path': './models/TFIDF_vectorizer.bin',
            'max_news_distance_secs': 24*60*60,
            'drop_duplicates': False,
            'sumbasic': {
                'summary_length': 5
            },
            'divrank': {
                'summary_length': 5
            }
        }):
        print(os.getcwd())
        print(os.listdir(os.getcwd()))
        self.config = config
        self._data = pd.DataFrame([])
        self._last_time = 0
        self._first_time = 0
        self._clusters = []
        self._output = []
        self._count = 0
        self.SVM = None
        self.labels = None
        self.TFIDF = None
        self._load_models()

    def fit(self, news_list):
        if not news_list:
            return
        # Cleaning and classifying new data
        new_data = self._norimalize(news_list)
        self._vectorize(new_data)
        self._classify(new_data)
        # Adding new data to existing data
        self._data = pd.concat([new_data, self._data])
        # Sorting just to be sure
        self._data.sort_values('date', inplace=True, ascending=False)
        # Saving most recent news date for next update
        self._last_time = self._data.iloc[0].date
        self._first_time = self._data.iloc[-1].date
        # Dropping all data older then 24 hours
        self._data = self._data[self._data.date >= self._last_time - self.config['max_news_distance_secs']]
        self._count = self._data.shape[0]
        # Clusterize all data every time new data is coming
        clusters_no_sum = self._clusterize()
        self._clusters = self._summirize(clusters_no_sum)
        self._form_output()

    def get_events(self):
        return self._output

    def get_last_time(self):
        return self._form_date(self._last_time)

    def get_count(self):
        return self._count

    def _norimalize(self, news_list):
        # Converting data to pandas table
        data = pd.DataFrame(news_list)
        data = data[['media', 'url', 'title', 'text', 'topic', 'date']]
        data.date = data.date.apply(int)
        data.sort_values('date', inplace=True, ascending=False)
        if self.config['drop_duplicates']:
            data.drop_duplicates(subset='url', inplace=True)
        # Append text_norm, title_norm columns to data w/ normalized text
        data.title = data.title.apply(lambda x: x.strip())
        data['text_norm'] = data.text.apply(TEXT_PIPELINE)
        data['title_norm'] = data.title.apply(TEXT_PIPELINE)
        return data

    def _vectorize(self, data):
        if self.config['append_titles']:
            trainX = data['title_norm']
        else:
            trainX = data['title_norm'] + ' ' + data['text_norm']
        trainX = trainX.values
        data['tfidf_vector'] = list(self.TFIDF.transform(trainX).toarray())

    def _classify(self, data):
        data['svm_class'] = list(self.SVM.predict(data['tfidf_vector'].tolist()))
        data['svm_class'] = data.apply(
            lambda row:
                self._class_to_str(row['svm_class']),
            axis=1)

    def _clusterize(self):
        config = self.config['kmeans']
        tfidf_matrix = self._data['tfidf_vector'].tolist()
        kmeans = MiniBatchKMeans(
            n_clusters=self._count // config['n_clusters_coeff'],
            batch_size=config['batch_size'],
            n_init=config['n_init'],
            max_iter=config['max_iter']
        ).fit(tfidf_matrix)
        clusters_raw = kmeans.predict(tfidf_matrix)
        clusters = [[] for _ in range(len(clusters_raw))]
        for i, cluster in enumerate(clusters_raw):
            tfidf_news = np.array(tfidf_matrix[i]).reshape(1, -1)
            if cosine_similarity(tfidf_news,
                kmeans.cluster_centers_[cluster].reshape(1, -1))[0][0] >= self.config['kmeans']['proximity_coeff']:
                clusters[cluster].append(i)
        return self._sort_clusters(clusters)

    def _summirize(self, clusters):
        clusters_summed = []
        for news_ids in clusters:
            text = '\n'.join([self._data.iloc[id]['text'] for id in news_ids])
            clusters_summed.append({
                'sumbasic': sum_basic(text, self.config['sumbasic']), 'divrank': divrank(text, self.config['divrank']),
                'content': news_ids
            })
        return clusters_summed

    def _load_models(self):
        with open(self.config['svm_path'], 'rb') as pickle_file:
            self.SVM = pickle.load(pickle_file)
        with open(self.config['svm_labels_path'], 'rb') as pickle_file:
            self.labels = pickle.load(pickle_file)
        with open(self.config['tfidf_path'], 'rb') as pickle_file:
            self.TFIDF = pickle.load(pickle_file)

    def _form_output(self):
        """ Creating a json output for server """
        self._output = []
        for i, cluster in enumerate(self._clusters):
            form_cluster = cluster.copy()
            form_cluster['content'] = []
            self._output.append(form_cluster)
            for id in cluster['content']:
                self._output[i]['content'].append({
                    'media': self._data.iloc[id].media,
                    'title': self._data.iloc[id].title,
                    'url': self._data.iloc[id].url,
                    'text': self._cut_text(self._data.iloc[id].text),
                    'labels': {
                        'SVM': self._data.iloc[id]['svm_class']
                    },
                    'date': self._date_to_str(self._data.iloc[id].date),
                })

    def _form_date(self, ts):
        return datetime.datetime.utcfromtimestamp(ts).replace(
            tzinfo=pytz.utc).astimezone(TZ)

    def _get_avg_time(self, group):
        avg = 0
        for n in group:
            avg += self._data.iloc[n]['date']
        return avg // len(group)

    def _sort_clusters(self, clusters):
        cs_filtered = filter(lambda x: len(x) > 1, clusters)
        # Sort by date of event
        cs_sorted = sorted(cs_filtered, key=lambda x: self._get_avg_time(x), reverse=True)
        # Sort news im cluster by time
        cs_sorted = list(map(lambda x: sorted(x,
                                           key=lambda y: self._data.iloc[y].date, reverse=True), cs_sorted))
        return cs_sorted

    def _class_to_str(self, class_num):
        """ Converting number of predicted class to string """
        return self.labels.inverse_transform(class_num)

    def _cut_text(self, text):
        """ Returns first paragraph of text """
        ps = []
        for p in text.split('\n'):
            if p != '':
                if len(p) > 500:
                    ps.append(p[:500].strip() + '...')
                    return "\n".join(ps)
                else:
                    ps.append(p.strip())
                if len(ps) == 1:
                    return "\n".join(ps)
        return ''

    def _date_to_str(self, date):
        return datetime.datetime.utcfromtimestamp(date).replace(
            tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Moscow')).strftime('%a %H:%M')
