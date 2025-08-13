import os
from dotenv import load_dotenv
import streamlit as st
from io import StringIO
from docx import Document
import PyPDF2
from openai import OpenAI
import re

# -------------------
# Load environment variables from .env file
# -------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("API key not found. Please set OPENAI_API_KEY in your .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

# -------------------
# Clause Keywords
# -------------------
commercial_clauses = {
    "Payment Terms": ["payment terms", "terms of payment", "payment schedule"],
    "IP": ["intellectual property", "IP rights", "ownership of work"],
    "Delivery Terms": ["delivery terms", "delivery schedule", "shipment terms"],
    "Warranties and Representations": ["warranties", "representations", "guarantees"]
}

legal_clauses = {
    "Indemnification": ["indemnification", "hold harmless"],
    "Termination": ["termination", "end of agreement", "contract termination"],
    "Confidentiality": ["confidentiality", "non-disclosure", "nda"],
    "Limitation of Liability": ["limitation of liability", "liability cap", "liability limit"]
}

def check_clauses(text, clause_dict):
    results = {}
    text_lower = text.lower()
    for clause, keywords in clause_dict.items():
        results[clause] = any(re.search(r"\b" + re.escape(keyword) + r"\b", text_lower) for keyword in keywords)
    return results

# -------------------
# File extraction functions
# -------------------
def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)

def extract_text(file) -> str:
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    elif file.type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file.type.startswith("text/"):
        stringio = StringIO(file.getvalue().decode("utf-8"))
        return stringio.read()
    else:
        return None

# -------------------
# GPT functions
# -------------------
def summarize(document: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You're an exceptional lawyer skilled at distilling long contracts into short paragraphs that are easy to understand and digest."},
            {"role": "user", "content": f"Provide an executive summary for the following contract: {document}"}
        ]
    )
    return response.choices[0].message.content

def get_obligations(document: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"Highlight the key obligations from the following contract: {document}"}
        ]
    )
    return response.choices[0].message.content

def extract_important_dates(document: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"Find all important dates and deadlines in this contract: {document}"}
        ]
    )
    return response.choices[0].message.content

def extract_termination_clauses(document: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"Highlight the termination clauses in this contract: {document}"}
        ]
    )
    return response.choices[0].message.content

def highlight_confidentiality_noncompete(document: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"Identify confidentiality and non-compete clauses in this contract: {document}"}
        ]
    )
    return response.choices[0].message.content

# -------------------
# Streamlit UI
# -------------------
def main():
    st.title("📜 Contract Analyzer with Clause Checker")

    uploaded_file = st.file_uploader("Upload your contract file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

    if uploaded_file is not None:
        with st.spinner("Extracting text from file..."):
            text = extract_text(uploaded_file)

        if not text:
            st.error("Unsupported file type or unable to extract text.")
            return

        st.subheader("📄 Contract Text Preview")
        st.write(text[:2000] + ("..." if len(text) > 2000 else ""))

        if st.button("🔍 Analyze Contract"):
            with st.spinner("Analyzing..."):
                # GPT Outputs
                summary = summarize(text)
                obligations = get_obligations(text)
                dates = extract_important_dates(text)
                termination = extract_termination_clauses(text)
                confidentiality = highlight_confidentiality_noncompete(text)

                # Clause Checker
                commercial_results = check_clauses(text, commercial_clauses)
                legal_results = check_clauses(text, legal_clauses)

            # Display GPT Outputs
            st.subheader("📌 Executive Summary")
            st.write(summary)

            st.subheader("📌 Key Obligations")
            st.write(obligations)

            st.subheader("📌 Important Dates / Deadlines")
            st.write(dates)

            st.subheader("📌 Termination Clauses")
            st.write(termination)

            st.subheader("📌 Confidentiality and Non-Compete Clauses")
            st.write(confidentiality)

            # Display Clause Checker
            st.subheader("Clause Presence Checker")

            st.markdown("###  Commercial Clauses 🛒")
            for clause, exists in commercial_results.items():
                st.write(f"{clause}: {'✅ Yes' if exists else '❌ No'}")

            st.markdown("### Legal Clauses ⚖️")
            for clause, exists in legal_results.items():
                st.write(f"{clause}: {'✅ Yes' if exists else '❌ No'}")

if __name__ == "__main__":
    main()
