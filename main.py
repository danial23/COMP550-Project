# Nov. 27th, 2021
# Molly Jacobsen
# Comp550 - Final Project

# main.py
# main method for training and testing linear models
# requires vectorized data to be stored in files named vectorized-0.npz and vectorized-1.npz
# if using doc2vec vectorization, comment out nb code

import pandas as pd
import os
import csv
import json
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from scipy import sparse


def performance(mname, predictions, goals):
    print(mname + " performance: ")
    tp, fp, tn, fn = 0, 0, 0, 0
    for g, p in zip(goals, predictions):
        if p != g:
            if p == '1' or p == 'True':
                fp += 1
            else:
                fn += 1
        else:
            if p == '1' or p == 'True':
                tp += 1
            else:
                tn += 1
    print("Total false positives: " + str(fp))
    print("Total true positives: " + str(tp))
    print("Total false negatives: " + str(fn))
    print("Total true negatives: " + str(tn))
    print("Total mistakes: " + str(fp + fn))
    try:
        accuracy = (tp+tn)/(fp+fn+tp+tn)
        print("Accuracy: " + str(accuracy * 100) + "%")
        precision = tp/(fp+tp)
        print("Precision: " + str(precision * 100) + "%")
        recall = tp/(fn+tp)
        print("Recall: " + str(recall * 100) + "%")
        specificity = tn/(fp+tn)
        print("Specificity: " + str(specificity * 100) + "%")
        print("F1: " + str(((2*precision*recall)/(precision+recall)) * 100) + "%")
    except ZeroDivisionError:
        print("Division by zero")


if __name__ == "__main__":

    os.chdir("dataset")

    nb = MultinomialNB()
    sgd = SGDClassifier()

    with open("targets.csv", "r") as f:
        targetreader = list(csv.reader(f))

    test_data = []
    test_targets = []

    for i in range(2):
        file_name = "vectorized-" + str(i) + ".npz"
        if os.path.isfile(file_name):
            data = sparse.load_npz(file_name)
            targets = targetreader[2 * i]   # targets are separated with empty line

            m = data.get_shape()[0]
            if m < len(targets):
                targets = targets[:m]

            train_d, test_d, train_t, test_t = train_test_split(data, targets, test_size=0.10)
            test_data.append(test_d)
            test_targets += test_t
            nb.partial_fit(train_d, train_t, classes=['True', 'False'])
            sgd.partial_fit(train_d, train_t, classes=['True', 'False'])

    nb_results = []
    sgd_results = []
    for data in test_data:
        nb_results += list(nb.predict(data))
        sgd_results += list(sgd.predict(data))

    performance("Multinomial Naive Bayes Model", nb_results, test_targets)
    print('\n')
    performance("SGD Classifier", sgd_results, test_targets)
