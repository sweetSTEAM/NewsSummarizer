# Normalization functions
from nltk.corpus import stopwords
from stop_words import get_stop_words
from functools import lru_cache
from pymystem3 import Mystem
en_sw = get_stop_words('en')
ru_sw = get_stop_words('ru')
STOP_WORDS = set(en_sw) | set(ru_sw)
STOP_WORDS = STOP_WORDS | set(
    stopwords.words('russian')) | set(stopwords.words('english'))
STOP_WORDS = STOP_WORDS | set(['лента', 'новость', 'риа', 'тасс',
                               'редакция', 'газета', 'корра', 'daily',
                               'village', 'интерфакс', 'reuters'])

stemmer = Mystem()


class Pipeline(object):

    def __init__(self, *args):
        self.transformations = args

    def __call__(self, x):
        res = x
        for f in self.transformations:
            res = f(res)
        return res


def get_lower(text):
    return str(text).lower().strip()


def remove_punctuation(text):
    return ''.join([c if c.isalpha() or c in ['-', "'"] else ' ' for c in text])


@lru_cache(maxsize=None)
def get_word_normal_form(word):
    return ''.join(stemmer.lemmatize(word)).strip().replace('ё', 'е').strip('-')


def lemmatize_words(text):
    res = []
    for word in text.split():
        norm_form = get_word_normal_form(word)
        if len(norm_form) > 2 and norm_form not in STOP_WORDS:
            res.append(norm_form)
    return ' '.join(res)


TEXT_PIPELINE = Pipeline(get_lower, remove_punctuation, lemmatize_words)
