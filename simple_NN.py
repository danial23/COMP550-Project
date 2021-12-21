import os
import json
#import preprocessor as pp
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from keras.backend import clear_session
from keras.models import Sequential
from keras import layers
from keras import metrics
import numpy as np

def load_files(directory):
    revisions = []
    for file in os.listdir(directory):

        cur_f = open(os.path.join(directory, file))
        d = json.load(cur_f)
        try:
            for r in d["revisions"]:
                revisions.append(r)
                #print(r)
            print(file)

        except:

            continue
        cur_f.close()
    #print(revisions)
    return revisions



def simpletagstovec(tags):
    targets = []
    for t in tags:
        revert = False
        for q in t:
            if q == 'mw-reverted' or q == 'Reverted' or q == 'mw-manual-revert':
                revert = True
        if revert == True:
            targets.append(1)
        else:
            targets.append(0)
    targets = np.array(targets)
    return targets


if __name__ == "__main__":
    revisions = load_files(os.fsencode("./dataset/temp_dataset"))
    tags = []
    content = []
    cont_diff = []

    for r in revisions:
        try:
            #print(r)
            tag = r["tags"]
            #conte = r["slots"]["main"]["content"]
            conte = r["content"]
            conte_dif = r["content-diff"]
            tags.append(tag)
            content.append(conte)
            cont_diff.append(conte_dif)
        except:
            #print(r)
            continue
    print(len(content))
    print(len(tags))
    targets = simpletagstovec(tags)
    print(len(targets))
    #data = pp.contentToNgramVectors(content, 1, 2)
    # print(content[777])

    rivis_train, rivis_test, y_train, y_test = train_test_split(content, targets, test_size=0.25, random_state=1112)
    del content
    del targets
    print(len(rivis_test))
    print(len(y_test))

    vectorizer = CountVectorizer()
    vectorizer.fit(rivis_train)
    X_train = vectorizer.transform(rivis_train)
    X_test = vectorizer.transform(rivis_test)

    print(len(vectorizer.vocabulary_))
    print(type(X_train))

    print(type(y_train))

    print(X_train.shape)
    #print(X_train.toarray())
    print(X_train.shape[1])
    input_dim = X_train.shape[1]

    clear_session()

    model = Sequential()
    model.add(layers.Dense(20, input_dim=input_dim, activation='relu'))
    model.add(layers.Dense(10, input_dim=input_dim, activation='relu'))
    model.add(layers.Dense(5, input_dim=input_dim, activation='relu'))
    model.add(layers.Dense(1, activation='sigmoid'))
    model.compile(loss='mean_squared_error', optimizer='adam', metrics=[metrics.BinaryAccuracy(), metrics.TruePositives(), metrics.TrueNegatives(), metrics.FalseNegatives(), metrics.FalsePositives()])
    model.summary()

    history = model.fit(X_train, y_train, epochs=20, verbose=True, validation_data=(X_test, y_test), batch_size=10)
    #loss, accuracy, recall, percision = model.evaluate(X_train, y_train, verbose=True)
    #print("Training Accuracy: {:.4f}".format(accuracy))
    #print("Recall = " + str(recall))
    #print("Precision = " + str(percision))
    loss, accuracy, TruePositives, TrueNegatives, FalseNegatives, FalsePositives = model.evaluate(X_test, y_test, verbose=True)
    print("Testing Accuracy:  {:.4f}".format(accuracy))
    print("TruePositives = " + str(TruePositives))
    print("TrueNegatives = " + str(TrueNegatives))
    print("FalseNegatives = " + str(FalseNegatives))
    print("FalsePositives = " + str(FalsePositives))




