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


def vectorsAppend(matrix, list):
    # matrix and list should have same size
    for v, x in zip(matrix, list):
        v.append(x)


def performance(mname, revs, predictions, goals):
    print(mname + " performance: ")
    tp, fp, tn, fn = 0, 0, 0, 0
    for g, p in zip(goals, predictions):
        if p != g:
            if p == 1:
                fp += 1
                print('Non-reverted revision with comment "' + revs[goals.index(g)]["comment"] + '" was predicted to be reverted.')
            else:
                fn += 1
                print('Reverted revision with comment "' + revs[goals.index(g)]["comment"] + '" was missed.')
        else:
            if p == 1:
                tp += 1
            else:
                tn += 1
    print("Total false positives: " + str(fp))
    print("Total true positives: " + str(tp))
    print("Total false negatives: " + str(fn))
    print("Total true negatives: " + str(tn))
    print("Total mistakes: " + str(fp + fn))
    accuracy = (tp+tn)/(fp+fn+tp+tn)
    print("Accuracy: " + str(accuracy * 100) + "%")
    precision = tp/(fp+tp)
    print("Precision: " + str(precision * 100) + "%")
    recall = tp/(fn+tp)
    print("Recall: " + str(recall * 100) + "%")
    specificity = tn/(fp+tn)
    print("Specificity: " + str(specificity * 100) + "%")
    print("F1: " + str(((2*precision*recall)/(precision+recall)) * 100) + "%")
