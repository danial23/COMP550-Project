import pandas as pd
import os
import json
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import preprocessor as pp
from scipy import sparse


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

    data = sparse.load_npz("vectorized_data.npz")

    targets = pp.tagsToTargets(revisions)
    #content is always 1 element shorter than tags
    targets.pop()   

    d_train, d_test, t_train, t_test = train_test_split(data, targets, test_size=0.15)

    clf = LogisticRegression(random_state=0, max_iter=1000)
    clf.fit(d_train, t_train)

    results = clf.predict(d_test)

    performance("Logistic Regression Model", revisions, results, t_test)
