import pdfplumber
from transformers import pipeline
from fpdf import FPDF
import random
import re

# Load summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# -------------------------
# READ FILE TEXT (PDF / TXT)
# -------------------------
def read_file_text(path):

    # If file is PDF
    if path.lower().endswith(".pdf"):

        text = ""

        with pdfplumber.open(path) as pdf:

            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        return text

    # If file is TXT
    else:

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


# -------------------------
# GENERATE SUMMARY
# -------------------------
def generate_summary(text):

    text = text.replace("\n", " ")

    result = summarizer(
        text[:1200],
        max_length=180,
        min_length=60,
        do_sample=False
    )

    return result[0]["summary_text"]


# -------------------------
# GENERATE MCQS
# -------------------------
def generate_mcqs(text):

    sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.split()) > 6][:5]

    mcqs = []

    for i, sentence in enumerate(sentences):

        words = sentence.split()

        correct = words[-1].replace(",", "").replace(":", "")

        wrong_pool = [w for w in words if w != correct and len(w) > 4]

        wrong = random.sample(wrong_pool, min(3, len(wrong_pool)))

        while len(wrong) < 3:
            wrong.append("None of the above")

        options = wrong + [correct]

        random.shuffle(options)

        labels = ["A", "B", "C", "D"]

        question = f"Q{i+1}: {sentence}?\n"

        for label, opt in zip(labels, options):
            question += f"{label}) {opt}\n"

        mcqs.append(question)

    return "\n".join(mcqs)


# -------------------------
# CLEAN TEXT FOR PDF
# -------------------------
def clean_text(text):

    return text.encode("latin-1", "ignore").decode("latin-1")


# -------------------------
# CREATE PDF
# -------------------------
def text_to_pdf(summary, mcqs, output):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "EDUSUMMERIZER REPORT", ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Summary", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, clean_text(summary))

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "MCQs", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, clean_text(mcqs))

    pdf.output(output)