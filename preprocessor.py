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
from torchtext.data.utils import get_tokenizer
from torchtext.vocab import build_vocab_from_iterator


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

def addTimeData(data, times):
    ## WIP
    with data.toarray().shape as (n, m):
        fixed_shape = (n, m+5)
    fixed_data = np.ndarray(shape=fixed_shape, dtype=int)   #can't allocate this much space
    for i, d in enumerate(data.toarray()):
        time = [times[i].minute, times[i].hour, times[i].day, times[i].month, times[i].year]
        fixed_data[i] = numpy.append(d, np.array(time))
    return fixed_data
    

def vectorsAppend(matrix, vector):
    # matrix and list should have same size
    return sparse.hstack((matrix, np.array(vector)[:,None]))


def buildVocabulary():
    vocab_dir = os.fsencode(".\\vocab_set")
    text = []

    for f in os.listdir(vocab_dir):
        curf = open(os.path.join(vocab_dir, f))
        curd = json.load(curf)
        try:
            for rev in curd["revisions"]:
                text.append(rev["slots"]["main"]["content"])
        except:
            continue
        del curd
        curf.close()

    v = CountVectorizer(ngram_range=(1, 2))
    v.fit_transform(text)
    del text
    print("Vocab Built")
    return v.vocabulary_

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


def saveUnprocessed():
    vocab = buildVocabulary()

    for i in range(6):
        file_name = "vectorized_data-" + str(i) + ".npz"
        if os.path.isfile(file_name):
            print("Dataset " + str(i) + " was already saved")
        else:
            revisions = []
            content = []

            directory_name = ".\dataset-" + str(i)
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
                        revisions.append(r)
                        content.append(r["slots"]["main"]["content"])
                    except:
                        continue
                del d
                cur_f.close()

            targets = tagsToTargets(revisions)
            del revisions

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
            print("Dataset " + str(i) + " Vectorized")

            # saves vectorized data by dataset subdirectory
            sparse.save_npz(file_name, data_scaled)
            del data_scaled
            # saves targets as rows in a csv
            with open("targets.csv", 'a') as f:
                writer = csv.writer(f)
                writer.writerow(targets)
                del writer
            del targets
            print("Dataset " + str(i) + " saved")


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


if __name__ == "__main__":

    os.chdir('dataset')

    processed = input("Processed data? (y/n) ")

    if processed == 'n':
        saveUnprocessed()
    else:
        saveProcessed()

    print("Vectoriztion completed")
