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


pp.performance("Logistic Regression Model", revisions, results, t_test)
