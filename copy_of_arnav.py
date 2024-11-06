# -*- coding: utf-8 -*-
"""Copy of Arnav.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1FnxGo30xNXDs__O_OyLjAAt5Z5Vr0L08
"""



import pandas as pd
import numpy as np

import pandas as pd

df = pd.read_csv('/content/spamham (1).csv', encoding='latin1')
df.head()
# df.drop(['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4'], axis=1, inplace=True)
# df.head()

df.columns = ['label', 'message']
df.head()

df.info()

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.metrics import classification_report
from imblearn.over_sampling import RandomOverSampler
import nltk
from nltk.corpus import stopwords
import string
import re
import scipy

nltk.download('stopwords')

def preprocess_text(text):

    text = text.lower()

    text = text.translate(str.maketrans('', '', string.punctuation))

    stop_words = set(stopwords.words('english'))
    text = ' '.join(word for word in text.split() if word not in stop_words)
    return text
df['message'] = df['message'].apply(preprocess_text)
df['message_length'] = df['message'].apply(len)
df['special_characters'] = df['message'].apply(lambda x: 1 if re.search(r'[!@#$%^&*(),.?":{}|<>]', x) else 0)
df['has_numbers'] = df['message'].apply(lambda x: 1 if re.search(r'\d', x) else 0)
df['label'] = df['label'].map({'ham': 0, 'spam': 1})

X = df[['message', 'message_length', 'special_characters', 'has_numbers']]
y = df['label']

vectorizer = TfidfVectorizer(ngram_range=(1, 2))
X_tfidf = vectorizer.fit_transform(df['message'])

X_additional_features = df[['message_length', 'special_characters', 'has_numbers']].values
X_combined = scipy.sparse.hstack([X_tfidf, X_additional_features])

X_train, X_test, y_train, y_test = train_test_split(X_combined, y, test_size=0.2, random_state=42)

ros = RandomOverSampler(random_state=42)
X_resampled, y_resampled = ros.fit_resample(X_train, y_train)

rf_model = RandomForestClassifier(random_state=42)

xgb_model = XGBClassifier(random_state=42, eval_metric='logloss')

svc_model = SVC(probability=True, random_state=42)

voting_clf = VotingClassifier(estimators=[
    ('rf', rf_model),
    ('xgb', xgb_model),
    ('svc', svc_model)],
    voting='soft')

voting_clf.fit(X_resampled, y_resampled)

y_pred = voting_clf.predict(X_test)
print(classification_report(y_test, y_pred, target_names=['ham', 'spam']))

train_accuracy = voting_clf.score(X_resampled, y_resampled)

test_accuracy = voting_clf.score(X_test, y_test)
print(f"Training Accuracy: {train_accuracy:.4f}")
print(f"Testing Accuracy: {test_accuracy:.4f}")

spam_example = ["Congratulations! You've won a free entry into a prize draw. Call now to claim your reward!"]


spam_example_tfidf = vectorizer.transform(spam_example)


spam_example_length = [len(spam_example[0])]
spam_example_special_chars = [1 if re.search(r'[!@#$%^&*(),.?":{}|<>]', spam_example[0]) else 0]
spam_example_has_numbers = [1 if re.search(r'\d', spam_example[0]) else 0]


spam_example_additional_features = scipy.sparse.csr_matrix([spam_example_length + spam_example_special_chars + spam_example_has_numbers])
spam_example_combined = scipy.sparse.hstack([spam_example_tfidf, spam_example_additional_features])


probabilities = voting_clf.predict_proba(spam_example_combined)


print(f"Probability of ham: {probabilities[0][0]:.4f}")
print(f"Probability of spam: {probabilities[0][1]:.4f}")

!pip install optuna

import optuna
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from optuna.samplers import TPESampler


def objective(trial):

    rf_n_estimators = trial.suggest_int('rf_n_estimators', 50, 300)
    rf_max_depth = trial.suggest_int('rf_max_depth', 5, 20)
    rf_min_samples_split = trial.suggest_int('rf_min_samples_split', 2, 20)


    xgb_n_estimators = trial.suggest_int('xgb_n_estimators', 50, 300)
    xgb_max_depth = trial.suggest_int('xgb_max_depth', 3, 10)
    xgb_learning_rate = trial.suggest_float('xgb_learning_rate', 0.01, 0.3)


    rf_model = RandomForestClassifier(
        n_estimators=rf_n_estimators,
        max_depth=rf_max_depth,
        min_samples_split=rf_min_samples_split,
        random_state=42
    )

    xgb_model = XGBClassifier(
        n_estimators=xgb_n_estimators,
        max_depth=xgb_max_depth,
        learning_rate=xgb_learning_rate,
        random_state=42,
        eval_metric='logloss'
    )


    voting_clf = VotingClassifier(estimators=[
        ('rf', rf_model),
        ('xgb', xgb_model)],
        voting='soft')


    voting_clf.fit(X_resampled, y_resampled)


    y_pred = voting_clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    return accuracy


study = optuna.create_study(direction='maximize', sampler=TPESampler())
study.optimize(objective, n_trials=50)


best_trial = study.best_trial
print(f"Best trial accuracy: {best_trial.value}")
print("Best hyperparameters:")
for key, value in best_trial.params.items():
    print(f"{key}: {value}")


best_rf_model = RandomForestClassifier(
    n_estimators=best_trial.params['rf_n_estimators'],
    max_depth=best_trial.params['rf_max_depth'],
    min_samples_split=best_trial.params['rf_min_samples_split'],
    random_state=42
)

best_xgb_model = XGBClassifier(
    n_estimators=best_trial.params['xgb_n_estimators'],
    max_depth=best_trial.params['xgb_max_depth'],
    learning_rate=best_trial.params['xgb_learning_rate'],
    random_state=42,
    eval_metric='logloss'
)


best_voting_clf = VotingClassifier(estimators=[
    ('rf', best_rf_model),
    ('xgb', best_xgb_model)],
    voting='soft')

best_voting_clf.fit(X_resampled, y_resampled)

y_pred = best_voting_clf.predict(X_test)
final_accuracy = accuracy_score(y_test, y_pred)
print(f"Final model accuracy: {final_accuracy:.4f}")

train_accuracy = best_voting_clf.score(X_resampled, y_resampled)


test_accuracy = best_voting_clf.score(X_test, y_test)


print(f"Training Accuracy: {train_accuracy:.4f}")
print(f"Testing Accuracy: {test_accuracy:.4f}")

spam_example = ["Congratulations! You've won a free entry into a prize draw. Call now to claim your reward!"]


spam_example_tfidf = vectorizer.transform(spam_example)


spam_example_length = [len(spam_example[0])]
spam_example_special_chars = [1 if re.search(r'[!@#$%^&*(),.?":{}|<>]', spam_example[0]) else 0]
spam_example_has_numbers = [1 if re.search(r'\d', spam_example[0]) else 0]


spam_example_additional_features = scipy.sparse.csr_matrix([spam_example_length + spam_example_special_chars + spam_example_has_numbers])
spam_example_combined = scipy.sparse.hstack([spam_example_tfidf, spam_example_additional_features])


probabilities = best_voting_clf.predict_proba(spam_example_combined)


print(f"Probability of ham: {probabilities[0][0]:.4f}")
print(f"Probability of spam: {probabilities[0][1]:.4f}")

import matplotlib.pyplot as plt
import numpy as np
import re
import scipy

messages = [
    "Hey, are we still on for lunch tomorrow?",
    "Just checking in to see how you are doing.",
    "Exclusive deal just for you! Click here to claim your cash prize!"
]

probabilities_list = []
for msg in messages:

    msg_tfidf = vectorizer.transform([msg])


    msg_length = [len(msg)]
    msg_special_chars = [1 if re.search(r'[!@#$%^&*(),.?":{}|<>]', msg) else 0]
    msg_has_numbers = [1 if re.search(r'\d', msg) else 0]


    msg_additional_features = scipy.sparse.csr_matrix([msg_length + msg_special_chars + msg_has_numbers])
    msg_combined = scipy.sparse.hstack([msg_tfidf, msg_additional_features])


    probabilities = best_voting_clf.predict_proba(msg_combined)
    probabilities_list.append(probabilities[0])

probabilities_array = np.array(probabilities_list)


labels = ['Message 1: Ham', 'Message 2: Ham', 'Message 3: Spam']
x = np.arange(len(labels))

plt.bar(x - 0.2, probabilities_array[:, 0], 0.4, label='Probability of Ham', color='lightblue')
plt.bar(x + 0.2, probabilities_array[:, 1], 0.4, label='Probability of Spam', color='salmon')


plt.xticks(x, labels)
plt.ylabel('Probability')
plt.title('Probabilities of Messages being Ham or Spam')
plt.ylim(0, 1)
plt.legend()


plt.tight_layout()
plt.show()

import matplotlib.pyplot as plt
import numpy as np
import re
import scipy

spam_messages = [
    "Congratulations! You've won a free gift card!",
    "Click here to claim your reward of $1000!",
    "Dear user, your account has been compromised. Verify your identity to secure your account.",
    "Your PayPal account is under review. Please confirm your details immediately.",
    "Looking for ways to earn easy money from home? Join our online seminar!"
]


probabilities_list = []
for msg in spam_messages:

    msg_tfidf = vectorizer.transform([msg])


    msg_length = [len(msg)]
    msg_special_chars = [1 if re.search(r'[!@#$%^&*(),.?":{}|<>]', msg) else 0]
    msg_has_numbers = [1 if re.search(r'\d', msg) else 0]


    msg_additional_features = scipy.sparse.csr_matrix([msg_length + msg_special_chars + msg_has_numbers])
    msg_combined = scipy.sparse.hstack([msg_tfidf, msg_additional_features])


    probabilities = best_voting_clf.predict_proba(msg_combined)
    probabilities_list.append(probabilities[0])


probabilities_array = np.array(probabilities_list)


labels = [f'Message {i+1}' for i in range(len(spam_messages))]
x = np.arange(len(labels))


plt.bar(x - 0.2, probabilities_array[:, 0], 0.4, label='Probability of Ham', color='lightblue')
plt.bar(x + 0.2, probabilities_array[:, 1], 0.4, label='Probability of Spam', color='salmon')


plt.xticks(x, labels)
plt.ylabel('Probability')
plt.title('Probabilities of Increasingly Difficult Spam Messages')
plt.ylim(0, 1)
plt.legend()


plt.tight_layout()
plt.show()

import matplotlib.pyplot as plt
import numpy as np
import re
import scipy


banking_spam_message = "Dear Customer, we noticed unusual activity in your account. Please log in immediately to verify your identity and secure your account: [phishing link]. Failure to do so may result in account suspension."


msg_tfidf = vectorizer.transform([banking_spam_message])


msg_length = [len(banking_spam_message)]
msg_special_chars = [1 if re.search(r'[!@#$%^&*(),.?":{}|<>]', banking_spam_message) else 0]
msg_has_numbers = [1 if re.search(r'\d', banking_spam_message) else 0]


msg_additional_features = scipy.sparse.csr_matrix([msg_length + msg_special_chars + msg_has_numbers])
msg_combined = scipy.sparse.hstack([msg_tfidf, msg_additional_features])


probabilities = best_voting_clf.predict_proba(msg_combined)

labels = ['Probability of Ham', 'Probability of Spam']
x = np.arange(len(labels))

plt.bar(x, probabilities[0], 0.4, color=['lightblue', 'salmon'])

plt.xticks(x, labels)
plt.ylabel('Probability')
plt.title('Probability of Tough Banking Spam Message')
plt.ylim(0, 1)

plt.tight_layout()
plt.show()

print(f"Probability of Ham: {probabilities[0][0]:.4f}")
print(f"Probability of Spam: {probabilities[0][1]:.4f}")