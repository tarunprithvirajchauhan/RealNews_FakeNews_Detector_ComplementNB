"""
Project Beta: Fake News Detection
Team: Beta (4 Members)
Model: Naive Bayes (ComplementNB + MultinomialNB)
Dataset: Kaggle - emineyetm/fake-news-detection-datasets
Pipeline: Load -> Merge -> Preprocess -> TF-IDF -> Train -> Evaluate -> Visualize -> Export
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import nltk
import warnings
import joblib
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from wordcloud import WordCloud
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, learning_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                              confusion_matrix, classification_report, roc_curve, auc,
                              roc_auc_score)

warnings.filterwarnings('ignore')
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

# Module-level NLP objects initialized once for high-throughput preprocessing
LEMMATIZER = WordNetLemmatizer()
STOP_WORDS = set(stopwords.words('english'))

# ============================================================
# CONFIGURATION
# ============================================================
RANDOM_STATE = 42
TEST_SIZE = 0.2
MAX_FEATURES = 10000
NGRAM_RANGE = (1, 2)
CV_FOLDS = 5

# ============================================================
# STEP 1: DATASET LOADING & MERGING
# ============================================================
def load_and_merge_datasets(fake_path, true_path, drop_duplicates=False):
    """
    Load Fake.csv and True.csv, assign labels, and merge.
    label: 0 = Real, 1 = Fake
    """
    fake_df = pd.read_csv(fake_path)
    true_df = pd.read_csv(true_path)

    fake_df['label'] = 1
    true_df['label'] = 0

    df = pd.concat([fake_df, true_df], axis=0, ignore_index=True)
    df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    print('=' * 60)
    print('DATASET OVERVIEW')
    print('=' * 60)
    print(f'Total Shape: {df.shape}')
    print(f'Columns: {list(df.columns)}')
    print('\nClass Distribution:')
    print(df['label'].value_counts())
    print('\nMissing Values:')
    print(df.isnull().sum())
    
    dup_count = df.duplicated().sum()
    print(f'\nDuplicate Rows: {dup_count}')
    if drop_duplicates and dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        print(f'Dropped {dup_count} duplicate rows. Remaining: {len(df)}')
        
    return df

# ============================================================
# STEP 2: FEATURE ENGINEERING - TITLE + BODY
# ============================================================
def combine_features(df):
    """Combine title and text for richer features."""
    df = df.copy()
    df['title_text'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
    print(f"\nCombined title_text length: {df['title_text'].str.len().mean():.1f} chars (avg)")
    return df

# ============================================================
# STEP 3: ADVANCED TEXT PREPROCESSING
# ============================================================
def clean_text_advanced(text):
    """
    Advanced cleaning for news articles:
    1. URL removal
    2. Lowercase
    3. Special character removal
    4. Lemmatization
    5. Stopword removal
    6. Whitespace normalization
    """
    if pd.isna(text):
        return ''

    text = text.lower()
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = text.split()
    tokens = [LEMMATIZER.lemmatize(t) for t in tokens
              if t not in STOP_WORDS and len(t) > 2]
    return ' '.join(tokens)

def preprocess_dataframe(df, text_col='title_text', label_col='label'):
    """Apply advanced cleaning to entire DataFrame."""
    df = df.copy()
    print('\nPreprocessing text... (this may take a moment)')
    df['cleaned_text'] = df[text_col].apply(clean_text_advanced)
    df = df[df['cleaned_text'].str.len() > 0].reset_index(drop=True)
    print(f'After cleaning: {len(df)} samples remain')
    return df

# ============================================================
# STEP 4: TRAIN-TEST SPLIT
# ============================================================
def split_data(df, text_col='cleaned_text', label_col='label'):
    """Stratified split to maintain class balance."""
    X = df[text_col]
    y = df[label_col]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f'\nTrain set: {len(X_train)} samples')
    print(f'Test set: {len(X_test)} samples')
    return X_train, X_test, y_train, y_test

# ============================================================
# STEP 5: TF-IDF VECTORIZATION
# ============================================================
def vectorize_text(X_train, X_test):
    """Convert text to TF-IDF features."""
    vectorizer = TfidfVectorizer(
        ngram_range=NGRAM_RANGE,
        max_features=MAX_FEATURES,
        min_df=2,
        max_df=0.90,
        stop_words='english',
        sublinear_tf=True
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    print(f'\nTF-IDF Matrix Shape: {X_train_tfidf.shape}')
    print(f'Vocabulary Size: {len(vectorizer.vocabulary_)}')
    return vectorizer, X_train_tfidf, X_test_tfidf

# ============================================================
# STEP 6: MODEL TRAINING
# ============================================================
def train_models(X_train_tfidf, y_train):
    """Train baseline and primary models with CV."""

    print('\n' + '=' * 60)
    print('TRAINING: MultinomialNB (Baseline)')
    print('=' * 60)
    mnb = MultinomialNB(alpha=1.0)
    mnb.fit(X_train_tfidf, y_train)
    mnb_cv = cross_val_score(mnb, X_train_tfidf, y_train, cv=CV_FOLDS, scoring='f1_macro')
    print(f'5-Fold CV F1-Macro: {mnb_cv.mean():.4f} (+/- {mnb_cv.std():.4f})')

    print('\n' + '=' * 60)
    print('TRAINING: ComplementNB (Primary)')
    print('=' * 60)
    cnb = ComplementNB(alpha=1.0)
    cnb.fit(X_train_tfidf, y_train)
    cnb_cv = cross_val_score(cnb, X_train_tfidf, y_train, cv=CV_FOLDS, scoring='f1_macro')
    print(f'5-Fold CV F1-Macro: {cnb_cv.mean():.4f} (+/- {cnb_cv.std():.4f})')

    print('\n' + '=' * 60)
    print('HYPERPARAMETER TUNING: GridSearchCV (alpha)')
    print('=' * 60)
    param_grid = {'alpha': [0.01, 0.1, 0.5, 1.0, 2.0, 5.0]}
    grid = GridSearchCV(ComplementNB(), param_grid, cv=CV_FOLDS,
                         scoring='f1_macro', n_jobs=-1)
    grid.fit(X_train_tfidf, y_train)
    best_model = grid.best_estimator_
    print(f'Best Alpha: {grid.best_params_["alpha"]}')
    print(f'Best CV F1-Macro: {grid.best_score_:.4f}')

    return mnb, cnb, best_model, grid

# ============================================================
# STEP 7: MODEL EVALUATION
# ============================================================
def evaluate_model(model, X_test_tfidf, y_test, model_name, class_names=['Real', 'Fake']):
    """Comprehensive evaluation with all metrics."""
    y_pred = model.predict(X_test_tfidf)
    y_prob = model.predict_proba(X_test_tfidf)[:, 1]

    print('\n' + '=' * 60)
    print(f'EVALUATION: {model_name}')
    print('=' * 60)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='macro')
    rec = recall_score(y_test, y_pred, average='macro')
    f1 = f1_score(y_test, y_pred, average='macro')
    roc_auc = roc_auc_score(y_test, y_prob)

    print(f'Accuracy:  {acc:.4f}')
    print(f'Precision: {prec:.4f}')
    print(f'Recall:    {rec:.4f}')
    print(f'F1-Score:  {f1:.4f}')
    print(f'ROC-AUC:   {roc_auc:.4f}')
    print(f'\nClassification Report:')
    print(classification_report(y_test, y_pred, target_names=class_names))

    return y_pred, y_prob, {'accuracy': acc, 'precision': prec, 'recall': rec,
                             'f1': f1, 'roc_auc': roc_auc}

# ============================================================
# STEP 8: VISUALIZATION
# ============================================================
def plot_confusion_matrix(y_test, y_pred, class_names=['Real', 'Fake'], save_path='outputs/noisy_confusion_matrix.png'):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix - Fake News Detection', fontsize=14, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'\nConfusion Matrix saved: {save_path}')

def plot_roc_curve(y_test, y_prob_mnb, y_prob_cnb, y_prob_best, save_path='outputs/noisy_roc_curve.png'):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.figure(figsize=(10, 8))
    for y_prob, name, color in [(y_prob_mnb, 'MultinomialNB', 'orange'),
                                 (y_prob_cnb, 'ComplementNB', 'green'),
                                 (y_prob_best, 'Best ComplementNB', 'blue')]:
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, color=color, lw=2, label=f'{name} (AUC = {roc_auc:.3f})')

    plt.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--', label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title('ROC Curve Comparison - Fake News Detection', fontsize=14, fontweight='bold')
    plt.legend(loc='lower right', fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'ROC Curve saved: {save_path}')

def plot_learning_curve(model, X, y, model_name, save_path='outputs/noisy_learning_curve.png'):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    train_sizes, train_scores, test_scores = learning_curve(
        model, X, y, cv=CV_FOLDS, n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 10), scoring='f1_macro'
    )
    train_mean = train_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    test_mean = test_scores.mean(axis=1)
    test_std = test_scores.std(axis=1)

    plt.figure(figsize=(10, 6))
    plt.plot(train_sizes, train_mean, 'o-', color='blue', label='Training Score')
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
    plt.plot(train_sizes, test_mean, 'o-', color='green', label='Cross-Validation Score')
    plt.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, alpha=0.1, color='green')
    plt.xlabel('Training Set Size', fontsize=12)
    plt.ylabel('F1-Macro Score', fontsize=12)
    plt.title(f'Learning Curve - {model_name}', fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Learning Curve saved: {save_path}')

def plot_wordclouds(df, text_col='cleaned_text', label_col='label',
                     save_fake='outputs/noisy_wordcloud_fake.png', save_real='outputs/noisy_wordcloud_real.png'):
    os.makedirs(os.path.dirname(save_fake), exist_ok=True)
    os.makedirs(os.path.dirname(save_real), exist_ok=True)
    fake_text = ' '.join(df[df[label_col] == 1][text_col].dropna())
    real_text = ' '.join(df[df[label_col] == 0][text_col].dropna())

    wc_fake = WordCloud(width=800, height=400, background_color='white', colormap='Reds').generate(fake_text)
    plt.figure(figsize=(12, 6))
    plt.imshow(wc_fake, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud - FAKE News Articles', fontsize=16, fontweight='bold', color='darkred')
    plt.tight_layout()
    plt.savefig(save_fake, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Fake Word Cloud saved: {save_fake}')

    wc_real = WordCloud(width=800, height=400, background_color='white', colormap='Blues').generate(real_text)
    plt.figure(figsize=(12, 6))
    plt.imshow(wc_real, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud - REAL News Articles', fontsize=16, fontweight='bold', color='darkblue')
    plt.tight_layout()
    plt.savefig(save_real, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Real Word Cloud saved: {save_real}')

# ============================================================
# STEP 9: MODEL EXPORT
# ============================================================
def export_model(model, vectorizer, model_path='models/noisy_complement_nb.pkl', vec_path='models/noisy_tfidf_vectorizer.pkl'):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    os.makedirs(os.path.dirname(vec_path), exist_ok=True)
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vec_path)
    print(f'\nModel exported: {model_path}')
    print(f'Vectorizer exported: {vec_path}')

# ============================================================
# MAIN EXECUTION PIPELINE
# ============================================================
def main_pipeline(fake_path, true_path):
    """End-to-end execution."""
    df = load_and_merge_datasets(fake_path, true_path)
    df = combine_features(df)
    df = preprocess_dataframe(df)

    X_train, X_test, y_train, y_test = split_data(df)
    vectorizer, X_train_tfidf, X_test_tfidf = vectorize_text(X_train, X_test)
    mnb, cnb, best_model, grid = train_models(X_train_tfidf, y_train)

    y_pred_mnb, y_prob_mnb, metrics_mnb = evaluate_model(mnb, X_test_tfidf, y_test, "MultinomialNB")
    y_pred_cnb, y_prob_cnb, metrics_cnb = evaluate_model(cnb, X_test_tfidf, y_test, "ComplementNB")
    y_pred_best, y_prob_best, metrics_best = evaluate_model(best_model, X_test_tfidf, y_test, "Best ComplementNB")

    plot_confusion_matrix(y_test, y_pred_best)
    plot_roc_curve(y_test, y_prob_mnb, y_prob_cnb, y_prob_best)
    plot_learning_curve(best_model, X_train_tfidf, y_train, "Best ComplementNB")
    plot_wordclouds(df)

    export_model(best_model, vectorizer)

    print('\n' + '=' * 60)
    print('FINAL MODEL COMPARISON')
    print('=' * 60)
    comparison = pd.DataFrame({
        'MultinomialNB': metrics_mnb,
        'ComplementNB': metrics_cnb,
        'Best ComplementNB': metrics_best
    })
    print(comparison.round(4))

    return best_model, vectorizer, metrics_best

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    fake_csv = base_dir / 'data' / 'processed' / 'Noisy_Fake.csv'
    true_csv = base_dir / 'data' / 'processed' / 'Noisy_True.csv'
    best_model, vectorizer, metrics = main_pipeline(
        fake_path=str(fake_csv),
        true_path=str(true_csv)
    )
