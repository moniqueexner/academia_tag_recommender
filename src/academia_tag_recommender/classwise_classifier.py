"""This module handles classifier calculation."""
from academia_tag_recommender.definitions import MODELS_PATH
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, roc_auc_score, accuracy_score
from sklearn.model_selection import StratifiedKFold
from joblib import dump, load
from pathlib import Path
import numpy as np
import time

DATA_FOLDER = Path(MODELS_PATH) / 'classifier' / 'multi-label' / 'classwise'

RANDOM_STATE = 0
scorer = make_scorer(accuracy_score)
k_fold = StratifiedKFold(shuffle=True, random_state=RANDOM_STATE)


class ClasswiseClassifier:
    """This classifier models holds the actual classifier, along with evaluation statistics.
    """

    def __init__(self, classifier_options):
        self.classifier_options = classifier_options

    def fit(self, X, y):
        """Fit classifier to given data.

        :param X: The X data
        :param y: The y data
        """
        self._clfs = []
        for y_i, _ in enumerate(y[0]):
            y_train = y[:, y_i]
            clf = self._choose_classifier(X, y_train)
            path = self._dump_clf(clf, y_i)
            self._clfs.append(path)
        return self

    def _choose_classifier(self, X, y):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, stratify=y, test_size=0.25, random_state=RANDOM_STATE)
        clfs = [self._fit_clf(clf_option, X_train, y_train)
                for clf_option in self.classifier_options]
        clf = self._get_best_clf(clfs, X_test, y_test)
        return clf

    def _fit_clf(self, clf_option, X, y):
        if clf_option.grid_search:
            return GridSearchCV(clf_option.clf, clf_option.parameter, cv=k_fold, scoring=scorer).fit(X, y).best_estimator_
        else:
            return clf_option.clf.fit(X, y)

    def _get_best_clf(self, clfs, X, y):
        clf_scores = [(clf, self._score_clf(clf, X, y)) for clf in clfs]
        clf = sorted(clf_scores, key=lambda x: x[1], reverse=True)[0][0]
        return clf

    def _score_clf(self, clf, X, y):
        prediction = clf.predict(X)
        score = accuracy_score(y, prediction)
        return score

    def predict(self, X):
        """

        :param X: The X data
        """
        prediction = []
        for path in self._clfs:
            clf = load(path)
            prediction.append(clf.predict(X))
        return np.transpose(prediction)

    def _dump_clf(self, clf, i):
        path = DATA_FOLDER / ('classifier_' + str(i) + '.joblib')
        dump(clf, path)
        return path

    def _load_clf(self, i):
        path = DATA_FOLDER / ('classifier_' + str(i) + '.joblib')
        return load(path)

    def __str__(self):
        return 'ClasswiseClassifier'


class ClassifierOption:
    def __init__(self, clf, grid_search=False, parameter={}):
        self.clf = clf
        self.grid_search = grid_search
        self.parameter = parameter