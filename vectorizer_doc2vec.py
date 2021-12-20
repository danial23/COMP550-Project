import gensim
import os
import pathlib
import json
import nltk
import helpers
import tqdm
import itertools


_DOC2VEC_PATH = pathlib.Path(__file__).parent.joinpath("doc2vec")


def _diff_tokenize(rev):
    return nltk.word_tokenize(rev["content-diff"])


def _tag_content_plaintext(i, rev):
    words = _diff_tokenize(rev)
    return gensim.models.doc2vec.TaggedDocument(words, [i])


def main():
    filenames = os.listdir("basic-processed")[0:100] # only do the first 100 pages, for example
    dataset_path = pathlib.Path(__file__).parent.joinpath("basic-processed")
    
    corpus = helpers.Corpus(filenames, dataset_path)

    training_set = itertools.starmap(_tag_content_plaintext, corpus)
    
    model = gensim.models.doc2vec.Doc2Vec()
    model.build_vocab(tqdm.tqdm(training_set, unit=" rev"))

    _DOC2VEC_PATH.mkdir(exist_ok=True)
    os.chdir(_DOC2VEC_PATH)

    model.save("doc2vec.model")



if __name__=="__main__":
    main()