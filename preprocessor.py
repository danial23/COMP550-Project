# Nov. 27th, 2021
# Molly Jacobsen
# Comp550 - Final Project

# preprocessor.py
# a few methods to preprocess data for a text classifier

import os
import json
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import preprocessing
import difflib
import numpy as np
from scipy import sparse


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
            if q == 'mw-rollback':
                rollback = True
        if rollback:
            user = revisions[revisions.index(r) - 1]['userid']
            i = revisions.index(r) - 1
            while i >= 0 and revisions[i]['userid'] == user:
                targets[i] = 1
                i -= 1
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


def contentToDiff(content):
    # content should be passed as an list/series of strings
    # assuming order new(low index) -> old
    # returns an list of strings which only show the differences between the strings
    diff = difflib.Differ()
    contentDiff = []
    for i, s in enumerate(content):
        if i == len(content)-1:
            break   # don't process last line
        diffstring = ""
        sdiff = diff.compare(s.split(". "), content[i+1].split(". "))
        for line in sdiff:
            if line[0] != ' ':
                diffstring += line + '\n'
        contentDiff.append(diffstring)
    return contentDiff


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
    fixed_data = np.ndarray(shape=fixed_shape, dtype=int)
    for i, d in enumerate(data.toarray()):
        time = [times[i].minute, times[i].hour, times[i].day, times[i].month, times[i].year]
        fixed_data[i] = numpy.append(d, np.array(time))
    return fixed_data
    

def vectorsAppend(matrix, vector):
    # matrix and list should have same size
    return sparse.hstack((matrix, np.array(vector)[:,None]))


if __name__ == "__main__":

    revisions = []

    with open('titles.json', "r") as f:
        titles = json.load(f)

    os.chdir('dataset')

    try:
        with open('titles_fetched.json', 'r') as f:
            titles_fetched = json.load(f)
    except FileNotFoundError:
        titles_fetched = {}

    ## assuming our data is stored in json files numbered as they are in tites_fetched.json
    for index, title in enumerate(titles):

        if title not in titles_fetched:
            continue

        try:
            cur_f = open(str(index) + ".json")
            d = json.load(cur_f)
            for r in d["revisions"]:
                revisions.append(r)
        except:
            continue

    content = []
    times = []

    for r in revisions:
        try:
            content.append(r["slots"]["main"]["content"])
            times.append(datetime.strptime(r["timestamp"], '%Y-%m-%dT%H:%M:%SZ'))
        except:
            continue


    if len(times) > len(content):
        times = times[:len(content)]
    elif len(content) > len(times):
        content = content[:len(times)]

    
    data = contentToNgramVectors(content, 1, 2)
    print("Data Vectorized")
    sparse.save_npz("vectorized_data.npz", data)
    print("Data saved")

    #data_with_times = addTimeData(data, times)
