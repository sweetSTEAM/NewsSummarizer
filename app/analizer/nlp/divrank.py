import sys
import nltk
import getopt
import codecs
import collections
import numpy
import networkx
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import pairwise_distances
import networkx as nx
from networkx.exception import NetworkXError
from .normalization import TEXT_PIPELINE


def divrank(text, config={'summary_length': 5}):
    '''
    Args:
      text: text to be summarized (unicode string)
      sent_limit: summary length (the number of sentences)

    Returns:
      list of extracted sentences
    '''
    sentences = list(nltk.sent_tokenize(text))
    scores, sim_mat = lexrank(sentences)
    sum_scores = sum(scores.values())
    acc_scores = 0.0
    indexes = set()
    num_sent, num_char = 0, 0
    for i in sorted(scores, key=lambda i: scores[i], reverse=True):
        num_sent += 1
        num_char += len(sentences[i])
        if num_sent > config['summary_length']:
            break
        indexes.add(i)
        acc_scores += scores[i]

    if len(indexes) > 0:
        summary_sents = [sentences[i] for i in sorted(indexes)]
    else:
        summary_sents = ['']

    return ' '.join(summary_sents)


def lexrank(sentences, continuous=True, sim_threshold=0.1, alpha=0.9,
            divrank_alpha=0.25):
    '''
    compute centrality score of sentences.

    Args:
      sentences: [u'こんにちは．', u'私の名前は飯沼です．', ... ]
      continuous: if True, apply continuous LexRank. (see reference)
      sim_threshold: if continuous is False and smilarity is greater or
        equal to sim_threshold, link the sentences.
      alpha: the damping factor of PageRank and DivRank
      divrank_alpha: strength of self-link [0.0-1.0]

    Returns: tuple
      (
        {
          # sentence index -> score
          0: 0.003,
          1: 0.002,
          ...
        },
        similarity_matrix
      )
    
    Reference:
      Günes Erkan and Dragomir R. Radev.
      LexRank: graph-based lexical centrality as salience in text
      summarization. (section 3)
      http://www.cs.cmu.edu/afs/cs/project/jair/pub/volume22/erkan04a-html/erkan04a.html
    '''
    # configure ranker
    ranker_params = {'max_iter': 1000}
    ranker = divrank_internal
    ranker_params['alpha'] = divrank_alpha
    ranker_params['d'] = alpha

    graph = networkx.DiGraph()

    # sentence -> tf
    sent_tf_list = []
    for sent in sentences:
        words = TEXT_PIPELINE(sent).split()
        tf = collections.Counter(words)
        sent_tf_list.append(tf)

    sent_vectorizer = DictVectorizer(sparse=True)
    sent_vecs = sent_vectorizer.fit_transform(sent_tf_list)

    # compute similarities between senteces
    sim_mat = 1 - pairwise_distances(sent_vecs, sent_vecs, metric='cosine')

    if continuous:
        linked_rows, linked_cols = numpy.where(sim_mat > 0)
    else:
        linked_rows, linked_cols = numpy.where(sim_mat >= sim_threshold)

    # create similarity graph
    graph.add_nodes_from(range(sent_vecs.shape[0]))
    for i, j in zip(linked_rows, linked_cols):
        if i == j:
            continue
        weight = sim_mat[i,j] if continuous else 1.0
        graph.add_edge(i, j, weight=weight)

    scores = ranker(graph, **ranker_params)
    return scores, sim_mat


def divrank_internal(G, alpha=0.25, d=0.85, personalization=None,
            max_iter=100, tol=1.0e-6, nstart=None, weight='weight',
            dangling=None):
    '''
    Returns the DivRank (Diverse Rank) of the nodes in the graph.
    This code is based on networkx.pagerank.

    Args: (diff from pagerank)
      alpha: controls strength of self-link [0.0-1.0]
      d: the damping factor

    Reference:
      Qiaozhu Mei and Jian Guo and Dragomir Radev,
      DivRank: the Interplay of Prestige and Diversity in Information Networks,
      http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.174.7982
    '''

    if len(G) == 0:
        return {}

    if not G.is_directed():
        D = G.to_directed()
    else:
        D = G

    # Create a copy in (right) stochastic form
    W = nx.stochastic_graph(D, weight=weight)
    N = W.number_of_nodes()

    # self-link
    for n in W.nodes():
        for n_ in W.nodes():
            if n != n_ :
                if n_ in W[n]:
                    W[n][n_][weight] *= alpha
            else:
                if n_ not in W[n]:
                    W.add_edge(n, n_)
                W[n][n_][weight] = 1.0 - alpha

    # Choose fixed starting vector if not given
    if nstart is None:
        x = dict.fromkeys(W, 1.0 / N)
    else:
        # Normalized nstart vector
        s = float(sum(nstart.values()))
        x = dict((k, v / s) for k, v in nstart.items())

    if personalization is None:
        # Assign uniform personalization vector if not given
        p = dict.fromkeys(W, 1.0 / N)
    else:
        missing = set(G) - set(personalization)
        if missing:
            raise NetworkXError('Personalization dictionary '
                                'must have a value for every node. '
                                'Missing nodes %s' % missing)
        s = float(sum(personalization.values()))
        p = dict((k, v / s) for k, v in personalization.items())

    if dangling is None:
        # Use personalization vector if dangling vector not specified
        dangling_weights = p
    else:
        missing = set(G) - set(dangling)
        if missing:
            raise NetworkXError('Dangling node dictionary '
                                'must have a value for every node. '
                                'Missing nodes %s' % missing)
        s = float(sum(dangling.values()))
        dangling_weights = dict((k, v/s) for k, v in dangling.items())
    dangling_nodes = [n for n in W if W.out_degree(n, weight=weight) == 0.0]

    # power iteration: make up to max_iter iterations
    for _ in range(max_iter):
        xlast = x
        x = dict.fromkeys(xlast.keys(), 0)
        danglesum = d * sum(xlast[n] for n in dangling_nodes)
        for n in x:
            D_t = sum(W[n][nbr][weight] * xlast[nbr] for nbr in W[n])
            for nbr in W[n]:
                #x[nbr] += d * xlast[n] * W[n][nbr][weight]
                x[nbr] += (
                    d * (W[n][nbr][weight] * xlast[nbr] / D_t) * xlast[n]
                )
            x[n] += danglesum * dangling_weights[n] + (1.0 - d) * p[n]

        # check convergence, l1 norm
        err = sum([abs(x[n] - xlast[n]) for n in x])
        if err < N*tol:
            return x
    raise NetworkXError('divrank: power iteration failed to converge '
                        'in %d iterations.' % max_iter)
