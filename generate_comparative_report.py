import os
from fpdf import FPDF

class ComparativePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(41, 128, 185)
        self.cell(0, 10, 'Fake News Detection System: Comparative Analysis Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + ' / {nb}', 0, 0, 'C')

    def chapter_title(self, num, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(220, 230, 240)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f'{num}. {title}', 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, body)
        self.ln()

    def add_side_by_side_images(self, img1, title1, img2, title2, width=90):
        # Y position before images
        start_y = self.get_y()
        
        # Titles
        self.set_font('Arial', 'B', 11)
        self.set_xy(10, start_y)
        self.cell(width, 6, title1, 0, 0, 'C')
        
        self.set_xy(110, start_y)
        self.cell(width, 6, title2, 0, 1, 'C')
        
        # Images
        if os.path.exists(img1) and os.path.exists(img2):
            self.image(img1, x=10, y=self.get_y(), w=width)
            self.image(img2, x=110, y=self.get_y(), w=width)
            # Advance Y past the images (approx 70 units depending on aspect ratio, let's just advance 75)
            self.ln(75)
        else:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, '[Images not found]', 0, 1, 'C')
            self.ln(10)

def create_comparative_report():
    pdf = ComparativePDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. Experiment Overview
    pdf.chapter_title(1, 'Experiment Overview: Clean vs. Noisy Data')
    body = (
        "This report provides a side-by-side comparison of two distinct training pipelines within the Fake News Detection System.\n\n"
        "1. Clean Pipeline: Trained on the original dataset (44k articles).\n"
        "2. Noisy Pipeline: Trained on a dataset where 10% of all words were deliberately corrupted (character swaps, omitted characters, omitted words) to simulate real-world messy data such as social media posts.\n\n"
        "The objective was to evaluate the robustness of the system architecture and determine if explicit training on noisy data yields a significantly more resilient model."
    )
    pdf.chapter_body(body)

    # 2. Evaluation Metrics Comparison
    pdf.chapter_title(2, 'Evaluation Metrics Comparison (on Noisy Test Data)')
    body = (
        "Both the original Clean Model and the new Noisy Model were evaluated against a 20% holdout set of the Noisy Dataset. The results demonstrate the inherent robustness of the TF-IDF and Naive Bayes architecture."
    )
    pdf.chapter_body(body)
    
    metrics_text = (
        "===============================================================\n"
        " Model          | Accuracy | Precision | Recall | F1-Score \n"
        "---------------------------------------------------------------\n"
        " Clean Model    |  95.89%  |   95.87%  | 95.91% |  0.9588  \n"
        " Noisy Model    |  95.96%  |   95.95%  | 95.98% |  0.9595  \n"
        "===============================================================\n"
    )
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Courier', '', 10)
    pdf.multi_cell(0, 5, metrics_text, 0, 'L', 1)
    pdf.ln(5)

    body_conclusion = (
        "Conclusion: The original Clean Model (which never saw typos during training) performed remarkably well, only dropping slightly in accuracy. The Noisy Model performed marginally better (by ~0.07%), indicating that explicitly training on typographical errors provides a small robustness boost, but the baseline TF-IDF architecture is already exceptionally resilient to noise."
    )
    pdf.chapter_body(body_conclusion)

    # 3. Visual Comparisons
    pdf.add_page()
    pdf.chapter_title(3, 'Visual Comparisons: Clean vs Noisy')
    
    pdf.add_side_by_side_images(
        'outputs/confusion_matrix.png', 'Clean Model (Test: Clean)',
        'outputs/noisy_confusion_matrix.png', 'Noisy Model (Test: Noisy)'
    )
    
    pdf.add_side_by_side_images(
        'outputs/roc_curve.png', 'ROC Curve (Clean)',
        'outputs/noisy_roc_curve.png', 'ROC Curve (Noisy)'
    )
    
    pdf.add_page()
    pdf.add_side_by_side_images(
        'outputs/learning_curve.png', 'Learning Curve (Clean)',
        'outputs/noisy_learning_curve.png', 'Learning Curve (Noisy)'
    )
    
    pdf.add_side_by_side_images(
        'outputs/wordcloud_fake.png', 'Fake Word Cloud (Clean)',
        'outputs/noisy_wordcloud_fake.png', 'Fake Word Cloud (Noisy)'
    )

    os.makedirs('docs', exist_ok=True)
    pdf.output('docs/Comparative_Report.pdf')
    print("Comparative PDF generated successfully at docs/Comparative_Report.pdf")

if __name__ == "__main__":
    create_comparative_report()
