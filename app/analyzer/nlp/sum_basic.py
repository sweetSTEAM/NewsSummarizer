from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.sum_basic import SumBasicSummarizer
from sumy.parsers.plaintext import PlaintextParser
from .normalization import STOP_WORDS, stemmer


def sum_basic(text, config={'summary_length': 1}):
    summarizer = SumBasicSummarizer(stemmer.lemmatize)
    summarizer.stop_words = STOP_WORDS
    parser = PlaintextParser.from_string(text, Tokenizer('english'))
    summary = summarizer(parser.document, config['summary_length'])
    return ' '.join([str(s) for s in summary])
