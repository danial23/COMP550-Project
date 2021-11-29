import pandas as pd
import os
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import preprocessor as pp

df = pd.DataFrame()

## assuming our data is stored in csv files is some dir "dataset"
for file in os.listdir("./dataset/"):
    curdf = pd.read_csv(file)
    df.append(curdf)

targets = pp.tagsToTargets(df['tags'])
diffData = pp.contentToDiff(df['content'])
data = pp.contentToNgramVectors(diffData, 1, 2)

d_train, d_test, t_train, t_test = train_test_split(data, targets, test_size=0.15)

clf = LogisticRegression(random_state=0, max_iter=1000)
clf.fit(d_train, t_train)
