from pathlib import Path
import sys
import warnings
import joblib
from sklearn.metrics import accuracy_score, f1_score

# Ensure src is in sys.path
SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from main_pipeline import load_and_merge_datasets, combine_features, preprocess_dataframe, split_data

warnings.filterwarnings('ignore')

def evaluate_models():
    print("Loading Noisy Dataset...")
    noisy_fake = BASE_DIR / 'data' / 'processed' / 'Noisy_Fake.csv'
    noisy_true = BASE_DIR / 'data' / 'processed' / 'Noisy_True.csv'
    
    df = load_and_merge_datasets(str(noisy_fake), str(noisy_true))
    df = combine_features(df)
    df = preprocess_dataframe(df)
    
    # Use exact stratified 80/20 train-test split to evaluate on the holdout test set
    # without data contamination from the training distribution
    _, X_test_text, _, y_test = split_data(df)
    
    print("\n--- Evaluating CLEAN Model on NOISY Data ---")
    clean_vec_path = BASE_DIR / 'models' / 'tfidf_vectorizer.pkl'
    clean_model_path = BASE_DIR / 'models' / 'complement_nb.pkl'
    try:
        clean_vec = joblib.load(clean_vec_path)
        clean_model = joblib.load(clean_model_path)
        
        X_test_clean_vec = clean_vec.transform(X_test_text)
        y_pred_clean = clean_model.predict(X_test_clean_vec)
        
        acc_clean = accuracy_score(y_test, y_pred_clean)
        f1_clean = f1_score(y_test, y_pred_clean, average='macro')
        print(f"Clean Model Accuracy: {acc_clean:.4f}")
        print(f"Clean Model F1-Macro: {f1_clean:.4f}")
    except Exception as e:
        print(f"Error evaluating clean model: {e}")
        acc_clean = 0.0
        f1_clean = 0.0
    
    print("\n--- Evaluating NOISY Model on NOISY Data ---")
    noisy_vec_path = BASE_DIR / 'models' / 'noisy_tfidf_vectorizer.pkl'
    noisy_model_path = BASE_DIR / 'models' / 'noisy_complement_nb.pkl'
    try:
        noisy_vec = joblib.load(noisy_vec_path)
        noisy_model = joblib.load(noisy_model_path)
        
        X_test_noisy_vec = noisy_vec.transform(X_test_text)
        y_pred_noisy = noisy_model.predict(X_test_noisy_vec)
        
        acc_noisy = accuracy_score(y_test, y_pred_noisy)
        f1_noisy = f1_score(y_test, y_pred_noisy, average='macro')
        print(f"Noisy Model Accuracy: {acc_noisy:.4f}")
        print(f"Noisy Model F1-Macro: {f1_noisy:.4f}")
    except Exception as e:
        print(f"Error evaluating noisy model: {e}")
        acc_noisy = 0.0
        f1_noisy = 0.0
    
    print("\n================ FINAL COMPARISON ================")
    print(f"Model          | Accuracy | F1-Score (Macro)")
    print(f"--------------------------------------------------")
    print(f"Clean Model    |  {acc_clean:.4f}  |  {f1_clean:.4f}")
    print(f"Noisy Model    |  {acc_noisy:.4f}  |  {f1_noisy:.4f}")
    print("==================================================")

if __name__ == "__main__":
    evaluate_models()
