import os
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Title
        self.set_text_color(41, 128, 185) # Blue color
        self.cell(0, 10, 'Fake News Detection System: Technical Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + ' / {nb}', 0, 0, 'C')

    def chapter_title(self, num, title):
        # Arial 12
        self.set_font('Arial', 'B', 14)
        # Background color
        self.set_fill_color(200, 220, 255)
        self.set_text_color(0, 0, 0)
        # Title
        self.cell(0, 8, f'{num}. {title}', 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        # Read text file
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        # Output justified text
        self.multi_cell(0, 6, body)
        self.ln()

    def add_image(self, img_path, title, w=160):
        if os.path.exists(img_path):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, title, 0, 1, 'C')
            self.image(img_path, x=(210-w)/2, w=w)
            self.ln(5)
        else:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, f'[Image not found: {img_path}]', 0, 1, 'C')

def create_report():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. Project Architecture
    pdf.chapter_title(1, 'Project Architecture & Setup')
    body = (
        "The project is built as an end-to-end Machine Learning pipeline entirely in Python, utilizing standard data science and ML libraries:\n"
        "- Data Manipulation: pandas, numpy\n"
        "- Natural Language Processing (NLP): nltk, re (Regex)\n"
        "- Machine Learning Engine: scikit-learn\n"
        "- Visualization: matplotlib, seaborn, wordcloud\n\n"
        "The workflow follows a sequential architecture:\n"
        "Data Ingestion -> Feature Engineering -> Preprocessing -> TF-IDF Vectorization -> Model Training & Tuning -> Evaluation."
    )
    pdf.chapter_body(body)

    # 2. Data Preprocessing
    pdf.chapter_title(2, 'Data Preprocessing Techniques')
    body = (
        "Since raw news articles contain noise (like URLs, punctuation, and varying casing), the text goes through a rigorous NLP cleaning process before feeding it to the model.\n\n"
        "1. Feature Merging: The article 'title' and 'text' (body) are concatenated into a single string. This is crucial because fake news often relies on sensational clickbait titles.\n"
        "2. URL & HTML Stripping: Regular expressions (Regex) are used to remove web links and residual HTML tags.\n"
        "3. Lowercasing & Punctuation Removal: All text is converted to lowercase, and non-alphanumeric characters are stripped out.\n"
        "4. Stopword Removal: Common English words that do not carry significant meaning (e.g., 'the', 'is', 'in') are removed using the NLTK library.\n"
        "5. Lemmatization: Words are reduced to their dictionary root form (e.g., 'running' becomes 'run'). This normalizes the vocabulary."
    )
    pdf.chapter_body(body)

    # 3. Data Splitting & TF-IDF
    pdf.chapter_title(3, 'Data Splitting & TF-IDF Vectorization')
    body = (
        "Once the text is cleaned, it must be converted into numbers because ML models cannot read text natively.\n\n"
        "- Data Split: The dataset (44,898 articles) is split into a Train Set (80%) and a Test Set (20%). A stratified split is used to ensure the exact same ratio of Real to Fake news exists in both sets.\n"
        "- TF-IDF Vectorization (Term Frequency-Inverse Document Frequency): The training text is converted into a massive mathematical matrix (35,911 rows x 10,000 columns).\n"
        "  * TF: Counts how often a word appears in an article.\n"
        "  * IDF: Penalizes words that appear across almost all articles.\n"
        "  * N-Grams: The vectorizer looks at single words (Unigrams) and pairs of words (Bigrams)."
    )
    pdf.chapter_body(body)

    # 4. Training
    pdf.chapter_title(4, 'Model Training, Epochs, & Time')
    body = (
        "How many Epochs?\n"
        "The concept of 'epochs' applies to Neural Networks (like Deep Learning models), which iteratively loop over the dataset to update weights. Naive Bayes models do not use epochs. Instead, they calculate probabilities algebraically in a single pass over the dataset. This makes them significantly faster and highly efficient.\n\n"
        "Training Process:\n"
        "1. MultinomialNB (Baseline): Trained in a single pass.\n"
        "2. ComplementNB: Trained as our primary model. It handles class imbalances better.\n"
        "3. Hyperparameter Tuning: We used GridSearchCV combined with 5-Fold Cross-Validation. The model trained itself 5 different times on different subsets across various smoothing parameters (alpha). It automatically discovered that alpha=0.01 yielded the best results.\n\n"
        "Training Time:\n"
        "Because Naive Bayes relies on simple probability counting rather than complex matrix backpropagation, it is blazingly fast. The entire pipeline took approximately 3 minutes and 50 seconds running entirely on a standard CPU. The actual model training portion of that time was completed in just a few seconds."
    )
    pdf.chapter_body(body)

    # 5. Behind the scenes
    pdf.chapter_title(5, 'How the ML Models Work Behind the Scenes')
    body = (
        "We used Naive Bayes, which is rooted in Bayes' Theorem of probability.\n\n"
        "1. The 'Naive' Assumption\n"
        "It assumes that every word in an article is completely independent of the others. Even though this is linguistically false, it mathematically works incredibly well for text classification.\n\n"
        "2. Calculating Probabilities (Learning)\n"
        "During training, the model simply counts word frequencies and calculates probabilities (e.g., probability of 'Shocking' given it is Fake news).\n\n"
        "3. Making Predictions (Inference)\n"
        "When a brand new article is passed into the model, it breaks the article down into its individual words. It then calculates two final scores by multiplying known probabilities together. Whichever score is mathematically higher wins, and the model confidently labels the article as Fake or Real!"
    )
    pdf.chapter_body(body)

    # 6. Results
    pdf.add_page()
    pdf.chapter_title(6, 'Results & Visualizations')
    
    # Terminal Output Metrics
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Final Model Comparison (Terminal Output)', 0, 1, 'L')
    
    terminal_output = (
        "============================================================\n"
        "           MultinomialNB  ComplementNB  Best ComplementNB\n"
        "accuracy          0.9556        0.9566             0.9616\n"
        "precision         0.9554        0.9563             0.9613\n"
        "recall            0.9555        0.9567             0.9617\n"
        "f1                0.9555        0.9565             0.9615\n"
        "roc_auc           0.9897        0.9897             0.9919\n"
        "============================================================"
    )
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Courier', '', 10)
    pdf.multi_cell(0, 5, terminal_output, 0, 'L', 1)
    pdf.ln(5)

    body = (
        "The Best ComplementNB model achieved an Accuracy of 96.16%, Precision of 96.13%, Recall of 96.17%, F1-Score of 0.9615, and ROC-AUC of 0.9919. Below are the visual evaluation matrices and graphs."
    )
    pdf.chapter_body(body)
    
    # Images
    pdf.add_image('outputs/confusion_matrix.png', 'Confusion Matrix (Error Pattern Analysis)', w=140)
    pdf.add_image('outputs/roc_curve.png', 'ROC Curve & AUC Scores', w=140)
    
    pdf.add_page()
    pdf.add_image('outputs/learning_curve.png', 'Learning Curve', w=150)
    pdf.add_image('outputs/wordcloud_fake.png', 'Word Cloud: Fake News', w=160)
    
    pdf.add_page()
    pdf.add_image('outputs/wordcloud_real.png', 'Word Cloud: Real News', w=160)

    # Save
    os.makedirs('docs', exist_ok=True)
    pdf.output('docs/Project_Report.pdf')
    print("PDF generated successfully at docs/Project_Report.pdf")

if __name__ == "__main__":
    create_report()
