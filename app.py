import os
import sys
import re
import random
import time
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import nltk
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    LEMMATIZER = WordNetLemmatizer()
    STOP_WORDS = set(stopwords.words('english'))
except Exception as e:
    print(f"Warning: NLTK initialization failed: {e}")
    LEMMATIZER = None
    STOP_WORDS = set()

# Initialize Flask App
SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
app = Flask(__name__, static_folder=str(SRC_DIR / 'static'), template_folder=str(SRC_DIR / 'static'))
CORS(app)

# Load Models & Vectorizers
def get_models_dir():
    src_models = SRC_DIR / 'models'
    base_models = BASE_DIR / 'models'
    if (src_models / 'complement_nb.pkl').exists():
        return src_models
    return base_models

MODELS_DIR = get_models_dir()
CLEAN_MODEL_PATH = MODELS_DIR / 'complement_nb.pkl'
CLEAN_VEC_PATH = MODELS_DIR / 'tfidf_vectorizer.pkl'
NOISY_MODEL_PATH = MODELS_DIR / 'noisy_complement_nb.pkl'
NOISY_VEC_PATH = MODELS_DIR / 'noisy_tfidf_vectorizer.pkl'

models = {
    'clean_model': None,
    'clean_vec': None,
    'noisy_model': None,
    'noisy_vec': None
}

def load_all_models():
    try:
        current_dir = get_models_dir()
        clean_m = current_dir / 'complement_nb.pkl'
        clean_v = current_dir / 'tfidf_vectorizer.pkl'
        noisy_m = current_dir / 'noisy_complement_nb.pkl'
        noisy_v = current_dir / 'noisy_tfidf_vectorizer.pkl'

        if clean_m.exists() and clean_v.exists():
            models['clean_model'] = joblib.load(clean_m)
            models['clean_vec'] = joblib.load(clean_v)
            print(f"Loaded Clean ComplementNB Model & TF-IDF Vectorizer from {current_dir}.")
        else:
            print(f"Warning: Clean model files missing in {current_dir}")

        if noisy_m.exists() and noisy_v.exists():
            models['noisy_model'] = joblib.load(noisy_m)
            models['noisy_vec'] = joblib.load(noisy_v)
            print(f"Loaded Noisy ComplementNB Model & TF-IDF Vectorizer from {current_dir}.")
        else:
            print(f"Warning: Noisy model files missing in {current_dir}")
    except Exception as e:
        print(f"Error loading models: {e}")

load_all_models()

# Advanced NLP Preprocessing
def clean_text_advanced(text):
    if not text or not isinstance(text, str):
        return ''
    text = text.lower()
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = text.split()
    if LEMMATIZER and STOP_WORDS:
        tokens = [LEMMATIZER.lemmatize(t) for t in tokens
                  if t not in STOP_WORDS and len(t) > 2]
    else:
        tokens = [t for t in tokens if len(t) > 2]
    return ' '.join(tokens)

# Noise Generation Function
def add_noise(text, noise_level=0.1, noise_types=None):
    if not text or not isinstance(text, str) or not text.strip():
        return text
    
    if noise_types is None:
        noise_types = ['swap', 'drop_char', 'drop_word']
    
    words = text.split()
    noisy_words = []
    
    for word in words:
        if random.random() < noise_level and len(word) > 3:
            choice = random.choice(noise_types)
            if choice == 'swap':
                idx = random.randint(0, len(word) - 2)
                word = word[:idx] + word[idx+1] + word[idx] + word[idx+2:]
                noisy_words.append(word)
            elif choice == 'drop_char':
                idx = random.randint(0, len(word) - 1)
                word = word[:idx] + word[idx+1:]
                noisy_words.append(word)
            elif choice == 'drop_word':
                continue
            else:
                noisy_words.append(word)
        else:
            noisy_words.append(word)
            
    return ' '.join(noisy_words)

# Feature Contribution Analysis (Explainable AI)
def get_top_contributing_words(vectorizer, model, cleaned_text, top_n=8):
    if not vectorizer or not model or not cleaned_text:
        return {'fake_indicators': [], 'real_indicators': []}
    
    try:
        tfidf_vec = vectorizer.transform([cleaned_text])
        feature_names = vectorizer.get_feature_names_out()
        nonzero_indices = tfidf_vec.nonzero()[1]
        
        if len(nonzero_indices) == 0:
            return {'fake_indicators': [], 'real_indicators': []}
        
        if hasattr(model, 'feature_log_prob_'):
            log_prob_0 = model.feature_log_prob_[0] # Real complement log weight
            log_prob_1 = model.feature_log_prob_[1] # Fake complement log weight
            
            words_info = []
            for idx in nonzero_indices:
                word = feature_names[idx]
                val = tfidf_vec[0, idx]
                # Log weight difference weighted by TF-IDF value
                score = (log_prob_0[idx] - log_prob_1[idx]) * val
                words_info.append({'word': word, 'weight': float(val), 'score': float(score)})
            
            fake_sorted = sorted([w for w in words_info if w['score'] > 0], key=lambda x: x['score'], reverse=True)[:top_n]
            real_sorted = sorted([w for w in words_info if w['score'] < 0], key=lambda x: x['score'])[:top_n]
            
            return {
                'fake_indicators': [{'word': item['word'], 'impact': round(abs(item['score']), 4)} for item in fake_sorted],
                'real_indicators': [{'word': item['word'], 'impact': round(abs(item['score']), 4)} for item in real_sorted]
            }
    except Exception as e:
        print(f"Error in feature analysis: {e}")
    
    return {'fake_indicators': [], 'real_indicators': []}

# Predict Function Helper
def predict_single(model, vectorizer, title, text):
    combined = (title or '') + ' ' + (text or '')
    cleaned = clean_text_advanced(combined)
    
    if not cleaned:
        return {
            'prediction': 'UNKNOWN',
            'label': 0,
            'probability_fake': 0.5,
            'probability_real': 0.5,
            'confidence': 50.0,
            'cleaned_text': '',
            'indicators': {'fake_indicators': [], 'real_indicators': []}
        }
        
    vec = vectorizer.transform([cleaned])
    pred_label = int(model.predict(vec)[0])
    
    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(vec)[0]
        prob_real = float(probs[0])
        prob_fake = float(probs[1])
    else:
        prob_fake = 1.0 if pred_label == 1 else 0.0
        prob_real = 1.0 - prob_fake
        
    confidence = max(prob_real, prob_fake) * 100.0
    label_str = "FAKE" if pred_label == 1 else "REAL"
    
    indicators = get_top_contributing_words(vectorizer, model, cleaned)
    
    return {
        'prediction': label_str,
        'label': pred_label,
        'probability_fake': round(prob_fake, 4),
        'probability_real': round(prob_real, 4),
        'confidence': round(confidence, 2),
        'cleaned_text': cleaned,
        'token_count': len(cleaned.split()),
        'indicators': indicators
    }

# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/')
def index():
    return send_from_directory(str(SRC_DIR / 'static'), 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(str(SRC_DIR / 'static'), filename)

@app.route('/outputs/<path:filename>')
def serve_output_images(filename):
    return send_from_directory(str(BASE_DIR / 'outputs'), filename)

@app.route('/docs/<path:filename>')
def serve_docs(filename):
    return send_from_directory(str(BASE_DIR / 'docs'), filename)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'clean_model_available': models['clean_model'] is not None,
        'noisy_model_available': models['noisy_model'] is not None,
        'metrics': {
            'clean_accuracy': 0.9589,
            'clean_f1_macro': 0.9588,
            'noisy_accuracy': 0.9596,
            'noisy_f1_macro': 0.9595,
            'dataset_size': 44898,
            'vocab_size': 10000
        }
    })

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.json or {}
    title = data.get('title', '')
    text = data.get('text', '')
    mode = data.get('mode', 'both')
    
    results = {}
    
    if mode in ['clean', 'both']:
        if models['clean_model'] and models['clean_vec']:
            results['clean_model'] = predict_single(
                models['clean_model'], models['clean_vec'], title, text
            )
        else:
            results['clean_model'] = {'error': 'Clean model not loaded'}
            
    if mode in ['noisy', 'both']:
        if models['noisy_model'] and models['noisy_vec']:
            results['noisy_model'] = predict_single(
                models['noisy_model'], models['noisy_vec'], title, text
            )
        else:
            results['noisy_model'] = {'error': 'Noisy model not loaded'}
            
    return jsonify(results)

@app.route('/api/simulate-noise', methods=['POST'])
def api_simulate_noise():
    data = request.json or {}
    text = data.get('text', '')
    title = data.get('title', '')
    noise_level = float(data.get('noise_level', 0.15))
    noise_types = data.get('noise_types', ['swap', 'drop_char', 'drop_word'])
    
    noisy_title = add_noise(title, noise_level, noise_types)
    noisy_text = add_noise(text, noise_level, noise_types)
    
    orig_clean_pred = predict_single(models['clean_model'], models['clean_vec'], title, text) if models['clean_model'] else {}
    orig_noisy_pred = predict_single(models['noisy_model'], models['noisy_vec'], title, text) if models['noisy_model'] else {}
    
    corrupted_clean_pred = predict_single(models['clean_model'], models['clean_vec'], noisy_title, noisy_text) if models['clean_model'] else {}
    corrupted_noisy_pred = predict_single(models['noisy_model'], models['noisy_vec'], noisy_title, noisy_text) if models['noisy_model'] else {}
    
    return jsonify({
        'noisy_title': noisy_title,
        'noisy_text': noisy_text,
        'noise_level': noise_level,
        'original_clean_pred': orig_clean_pred,
        'original_noisy_pred': orig_noisy_pred,
        'corrupted_clean_pred': corrupted_clean_pred,
        'corrupted_noisy_pred': corrupted_noisy_pred
    })

@app.route('/api/batch-predict', methods=['POST'])
def api_batch_predict():
    data = request.json or {}
    items = data.get('items', [])
    mode = data.get('mode', 'clean')
    
    selected_model = models['clean_model'] if mode == 'clean' else models['noisy_model']
    selected_vec = models['clean_vec'] if mode == 'clean' else models['noisy_vec']
    
    if not selected_model or not selected_vec:
        return jsonify({'error': 'Selected model is not available'}), 400
        
    results = []
    fake_count = 0
    real_count = 0
    
    for item in items[:100]:
        res = predict_single(selected_model, selected_vec, item.get('title', ''), item.get('text', ''))
        if res['prediction'] == 'FAKE':
            fake_count += 1
        elif res['prediction'] == 'REAL':
            real_count += 1
            
        results.append({
            'id': item.get('id'),
            'title': item.get('title', '')[:80] + ('...' if len(item.get('title', '')) > 80 else ''),
            'prediction': res['prediction'],
            'confidence': res['confidence'],
            'probability_fake': res['probability_fake'],
            'probability_real': res['probability_real'],
            'token_count': res['token_count']
        })
        
    return jsonify({
        'results': results,
        'summary': {
            'total': len(results),
            'fake_count': fake_count,
            'real_count': real_count,
            'fake_percentage': round((fake_count / len(results) * 100) if results else 0, 1),
            'real_percentage': round((real_count / len(results) * 100) if results else 0, 1)
        }
    })

@app.route('/api/samples', methods=['GET'])
def api_samples():
    return jsonify([
        {
            'id': 'real_politics',
            'category': 'Official News (REAL)',
            'title': 'WASHINGTON (Reuters) - U.S. Senate passes bipartisan budget resolution',
            'text': 'WASHINGTON (Reuters) - The United States Senate voted on Thursday to approve a bipartisan budget framework, clearing the way for lawmakers to begin drafting legislation on infrastructure spending. The measure passed with a 68-32 vote, receiving support from both Republican and Democratic members after weeks of intensive negotiations. White House officials commended the legislative progress, stating that the agreement marks a crucial step toward upgrading federal transportation networks and renewable energy infrastructure.'
        },
        {
            'id': 'fake_conspiracy',
            'category': 'Sensational Clickbait (FAKE)',
            'title': 'SHOCKING BREAKING: Leaked Documents Prove Secret Lunar Base Discovered By Whistleblower!',
            'text': 'UNBELIEVABLE! Top secret government files leaked online today reveal that high-ranking officials have been operating a secret underground lunar city for over three decades! Insiders claim mainstream media is hiding the true alien technology powering this classified project. Share this video before it gets taken down by the shadow government state censorship committee immediately!'
        },
        {
            'id': 'satire_humor',
            'category': 'Satire & Parody (FAKE)',
            'title': 'Local Man Wins Argument With Commenter On Social Media, World Achieves Peace',
            'text': 'A local resident made history early Tuesday morning by convincing an anonymous user in an online comment section to change their political view. Witnesses report that after presenting a well-structured argument with cited academic sources, the opposing commenter replied "You know what, you are totally right, my bad." Global leaders were reportedly so inspired by the exchange that hostilities across three continents instantly ceased.'
        },
        {
            'id': 'noisy_post',
            'category': 'Noisy Social Media Rumor (NOISY / FAKE)',
            'title': 'BREAKNG!! Scraest rumor surfasin online bout secret govment bio-labs!!',
            'text': 'U wont believ what just leakd online! A huge sciencist whistleblwer expose how the govment is hiding top secrt expariments in secret labs. Evryone need to share dis immediately before Facebook deletes dis post! Spread de truth now before its 2 late!!'
        }
    ])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Fake News Detection Web Server on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
