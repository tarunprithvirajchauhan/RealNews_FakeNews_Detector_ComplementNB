import os
from pathlib import Path
import random
import time
import pandas as pd

NOISE_LEVEL = 0.1  # 10% probability per word to be noisy

def add_noise(text):
    if not isinstance(text, str) or not text.strip():
        return text
    
    words = text.split()
    noisy_words = []
    
    for word in words:
        if random.random() < NOISE_LEVEL and len(word) > 3:
            noise_type = random.choice(['swap', 'drop_char', 'drop_word'])
            if noise_type == 'swap':
                # Swap two random adjacent characters
                idx = random.randint(0, len(word) - 2)
                word = word[:idx] + word[idx+1] + word[idx] + word[idx+2:]
                noisy_words.append(word)
            elif noise_type == 'drop_char':
                # Drop a random character
                idx = random.randint(0, len(word) - 1)
                word = word[:idx] + word[idx+1:]
                noisy_words.append(word)
            elif noise_type == 'drop_word':
                # Drop the word entirely
                continue
        else:
            noisy_words.append(word)
            
    return ' '.join(noisy_words)

def apply_noise_to_df(df_path, out_path):
    print(f"Loading {df_path}...")
    df = pd.read_csv(df_path)
    
    print(f"Injecting noise into titles and text (this may take a moment)...")
    start = time.time()
    
    # Fill missing values properly before applying noise to avoid literal 'nan' strings
    df['title'] = df['title'].fillna('').astype(str).apply(add_noise)
    df['text'] = df['text'].fillna('').astype(str).apply(add_noise)
    
    print(f"Noise injection complete in {time.time() - start:.2f} seconds.")
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved noisy dataset to {out_path}\n")

if __name__ == "__main__":
    random.seed(42)
    base_dir = Path(__file__).resolve().parent.parent
    raw_fake = base_dir / 'data' / 'raw' / 'Fake.csv'
    raw_true = base_dir / 'data' / 'raw' / 'True.csv'
    out_fake = base_dir / 'data' / 'processed' / 'Noisy_Fake.csv'
    out_true = base_dir / 'data' / 'processed' / 'Noisy_True.csv'
    
    apply_noise_to_df(str(raw_fake), str(out_fake))
    apply_noise_to_df(str(raw_true), str(out_true))
