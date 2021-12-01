import pandas as pd
import os
import json
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import preprocessor as pp
import mediawiki_extractor as mwe

revisions = []

## assuming our data is stored in json files in some dir "dataset"
for file in os.listdir("./dataset/"):
    cur_f = open(file)
    d = json.load(cur_f)
    for r in d:
        revisions.append(r)


tags = []
content = []

for i, r in enumerate(revisions):
    tags.append(r["tags"])
    content.append(r["slots"]["main"]["content"])

targets = pp.tagsToTargets(tags)
data = pp.contentToNgramVectors(content, 1, 2)

d_train, d_test, t_train, t_test = train_test_split(data, targets, test_size=0.15)

clf = LogisticRegression(random_state=0, max_iter=1000)
clf.fit(d_train, t_train)

score = clf.score(d_test, t_test)
print(score)
