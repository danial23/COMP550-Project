import pandas as pd
import os
import json
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import preprocessor as pp
import mediawiki_extractor as mwe

revisions = []
directory = os.fsencode("./dataset/")

## assuming our data is stored in json files in some dir "dataset"
for file in os.listdir(directory):
    cur_f = open(os.path.join(directory, file))
    d = json.load(cur_f)
    try:
        for r in d["revisions"]:
            revisions.append(r)
    except:
        continue


tags = []
content = []

for r in revisions:
    try:
        tags.append(r["tags"])
        content.append(r["slots"]["main"]["content"])
    except:
        continue

targets = pp.tagsToTargets(revisions)

if len(targets) > len(content):
    targets = targets[:len(content)]
elif len(content) > len(targets):
    content = content[:len(targets)]

data = pp.contentToNgramVectors(content, 1, 2)

d_train, d_test, t_train, t_test = train_test_split(data, targets, test_size=0.15)

clf = LogisticRegression(random_state=0, max_iter=1000)
clf.fit(d_train, t_train)

results = clf.predict(d_test)


def predictionResults(predictions, goals):
    tp, fp, tn, fn = 0, 0, 0, 0
    for i, p in enumerate(predictions):
        if p != goals[i]:
            if p == 1:
                fp += 1
                print('Non-reverted revision with comment "' + revisions[i]["comment"] + '" was predicted to be reverted.')
            else:
                fn += 1
                print('Reverted revision with comment "' + revisions[i]["comment"] + '" was missed.')
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



predictionResults(results, t_test)
