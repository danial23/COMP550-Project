# Nov. 27th, 2021
# Molly Jacobsen
# Comp550 - Final Project

# preprocessor.py
# a few methods to preprocess data for a text classifier


import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import preprocessing
import difflib


def tagsToTargets(revisions):
    # revisions should be passed as an list/series of revisions
    targets = []
    reverted = False
    rollback = False
    for r in revisions:
        t = r['tags']
        for q in t:
            if q == 'mw-reverted' or q == 'Reverted' or q == 'mw-manual-revert':
                reverted = True
            if q == 'mw-rollback':
                rollback = True
        if rollback:
            i = revisions.index(r) - 1
            user = revisions[i]['userid']
            while i >= 0 and revisions[i]['userid'] == user:
                targets[i] = 1
                i -= 1
        if reverted:
            targets.append(1)
        else:
            targets.append(0)
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
        if i == len(times):
            break
        delta = t - times[i+1]
        diffTimes.append[delta.total_seconds()]
    return diffTimes


def vectorsAppend(matrix, list):
    # matrix and list should have same size
    for v, x in zip(matrix, list):
        v.append(x)


def timesToDiff(times):
    # takes a list or series of datetime objects
    # returns list of ints (difference in seconds)
    diffTimes = []
    for i, t in enumerate(times):
        if i == len(times):
            break
        delta = t - times[i+1]
        diffTimes.append[delta.total_seconds()]
    return diffTimes


def vectorsAppend(matrix, list):
    # matrix and list should have same size
    for v, x in zip(matrix, list):
        v.append(x)
