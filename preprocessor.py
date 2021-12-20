# Nov. 27th, 2021
# Molly Jacobsen
# Comp550 - Final Project

# preprocessor.py
# a few methods to preprocess data for a text classifier

import os
import json
import csv
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import preprocessing
import difflib
import numpy as np
from scipy import sparse
import gensim


def tagsToTargets(revisions):
    # revisions should be passed as an list/series of revisions
    targets = []
    reverted = False
    rollback = False
    for r in revisions:
        t = r['tags']
        for q in t:
            if q == 'mw-reverted' or q == 'Reverted':
                reverted = True
    #        if q == 'mw-rollback':
    #            rollback = True
    #    if rollback:
    #        user = revisions[revisions.index(r) - 1]['userid']
    #        i = revisions.index(r) - 1
    #        while i >= 0 and revisions[i]['userid'] == user:
    #            targets[i] = 1
    #            i -= 1
        if reverted:
            targets.append(1)
        else:
            targets.append(0)
        rollback = False
        reverted = False
    return targets


def contentToNgramVectors(content, n, N):
    # content should be passed as an list/series of strings
    v = CountVectorizer(ngram_range=(n, N))
    data = v.fit_transform(content)
    scaler = preprocessing.StandardScaler(with_mean=False).fit(data)
    data_scaled = scaler.transform(data)
    return data_scaled


def timesToDiff(times):
    # takes a list or series of datetime objects
    # returns list of ints (difference in seconds)
    diffTimes = []
    for i, t in enumerate(times):
        if i == len(revs):
            break
        delta = t - times[i+1]
        diffTimes.append[delta.total_seconds()]
    return diffTimes


def buildProcessedVocabulary(text_field):
    vocab_dir = os.fsencode(".\\processed-vocab")
    text = []

    for f in os.listdir(vocab_dir):
        curf = open(os.path.join(vocab_dir, f))
        curd = json.load(curf)
        try:
            for rev in curd["revisions"]:
                text.append(rev[text_field])
        except:
            continue
        del curd
        curf.close()

    v_1 = CountVectorizer(ngram_range=(1, 2))
    v_1.fit_transform(text)
    del text
    vocab = v_1.vocabulary_
    del v_1
    return vocab


def tagged_document(list_of_list_of_words):
   for i, list_of_words in enumerate(list_of_list_of_words):
      yield gensim.models.doc2vec.TaggedDocument(list_of_words, [i])


def d2vVectorizer():
    vocab_dir = os.fsencode(".\\processed-vocab")
    text = []

    for f in os.listdir(vocab_dir):
        curf = open(os.path.join(vocab_dir, f))
        curd = json.load(curf)
        try:
            for rev in curd["revisions"]:
                text.append(list(rev["content-diff"]))
        except:
            continue
        del curd
        curf.close()

    training_text = list(tagged_document(text))
    del text
    model = gensim.models.doc2vec.Doc2Vec(vector_size=25, min_count=2, epochs=30)
    model.build_vocab(training_text)
    model.train(training_text, total_examples=model.corpus_count, epochs=model.epochs)
    del training_text
    return model


def saveProcessed():

    vocab = buildProcessedVocabulary("content-diff")

    for i in range(2):
        file_name = "processed_vectorized-" + str(i) + ".npz"
        if os.path.isfile(file_name):
            print("Dataset " + str(i) + " was already saved")
        else:
            targets = []
            content = []

            directory_name = ".\\basic-processed-" + str(i)
            directory = os.fsencode(directory_name)
            print("Processing data from directory " + str(i))

            for file in os.listdir(directory):
                path = os.path.join(directory, file)
                size = os.path.getsize(path)
                if size > 200000000:
                    continue
                    # temporary measure to ensure I can vectorize at least a couple datasets
                cur_f = open(path)
                d = json.load(cur_f)
                for r in d["revisions"]:
                    try:
                        targets.append(r["reverted"])
                        content.append(r["content-diff"])
                    except:
                        continue
                del d
                cur_f.close()

            if len(targets) > len(content):
                targets = targets[:len(content)]
            elif len(content) > len(targets):
                content = content[:len(targets)]

            vectorizer = CountVectorizer(vocabulary=vocab, ngram_range=(1, 2))
            data = vectorizer.fit_transform(content)
            del content
            scaler = preprocessing.StandardScaler(with_mean=False).fit(data)
            data_scaled = scaler.transform(data)
            del data
            del scaler
            print("Processed dataset " + str(i) + " Vectorized")

            # saves vectorized data by dataset subdirectory
            sparse.save_npz(file_name, data_scaled)
            del data_scaled
            # saves targets as rows in a csv
            #with open("processed_targets.csv", 'a') as f:
            #    writer = csv.writer(f)
            #    writer.writerow(targets)
            #    del writer
            del targets
            print("Processed dataset " + str(i) + " saved")


def saveDoc2Vec():

    doc2vecModel = d2vVectorizer()
    print("Doc2Vec model built")

    for i in range(2):
        file_name = "d2v_vectorized-" + str(i) + ".npz"
        if os.path.isfile(file_name):
            print("Dataset " + str(i) + " was already saved")
        else:
            targets = []
            vectors = []

            directory_name = ".\\basic-processed-" + str(i)
            directory = os.fsencode(directory_name)
            print("Processing data from directory " + str(i))

            for file in os.listdir(directory):
                path = os.path.join(directory, file)
                size = os.path.getsize(path)
                if size > 200000000:
                    continue
                    # temporary measure to ensure I can vectorize at least a couple datasets
                cur_f = open(path)
                d = json.load(cur_f)
                for r in d["revisions"]:
                    try:
                        targets.append(r["reverted"])
                        vectors.append(doc2vecModel.infer_vector(list(r["content-diff"])))
                    except:
                        continue
                del d
                cur_f.close()

            if len(targets) > len(vectors):
                targets = targets[:len(vectors)]
            elif len(vectors) > len(targets):
                vectors = vectors[:len(targets)]

            #vectorizer = CountVectorizer(vocabulary=vocab, ngram_range=(1, 2))
            #data = vectorizer.fit_transform(content)
            #del content
            #scaler = preprocessing.StandardScaler(with_mean=False).fit(data)
            #data_scaled = scaler.transform(data)
            #del data
            #del scaler
            print("Processed dataset " + str(i) + " Vectorized")

            # saves vectorized data by dataset subdirectory
            data = sparse.csr_matrix(vectors)
            del vectors
            sparse.save_npz(file_name, data)
            # saves targets as rows in a csv
            #with open("processed_targets.csv", 'a') as f:
            #    writer = csv.writer(f)
            #    writer.writerow(targets)
            #    del writer
            del targets
            print("Processed dataset " + str(i) + " saved")


if __name__ == "__main__":

    os.chdir('dataset')

    processed = input("Doc2Vec? (y/n) ")

    if processed == 'y':
        saveDoc2Vec()
    else:
        saveProcessed()

    print("Vectoriztion completed")
