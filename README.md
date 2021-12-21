# COMP550-Project
COMP550 Project

Binary Text Classifier for Reverted Wikipedia Edits
Contrubuters:
Molly Jacobsen


To vectorize data, run the preprocessor.py script. It will prompt "Doc2Vec?", enter y to vectorize the data with doc2vec vectorization, otherwise will use CountVectorizer with ngram range (1, 2). To change the data fields that are vectorized or the vectorization method you must manually edit the code. This script expects data to be stored in datsets basic-processed-0 and basic-processed-1 and will save vectorizations in NPZ files vectorized-0.npz and vectorized-1.npz, and targets in targets.csv.
Linear classifiers are run in the main.py, which will take the vectors stored in vectorized-0.npz and vectorized-1.npz and the targets stored in targets.csv and train an SGDClassifier and MultinomialNB model on the data. It will then test these models on 10% of the data and report back on the results of each model. If vectorized-0 and vectorized-1 contain doc2vec vectorization, the Naive Bayes code must be commented out before running.
