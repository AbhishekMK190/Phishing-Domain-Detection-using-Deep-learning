# save as resume_checker.py
# Usage:
#   pip install pdfplumber python-docx language-tool-python pyspellchecker
#   python resume_checker.py /path/to/resume.pdf

import sys
import os
from spellchecker import SpellChecker
import language_tool_python
import pdfplumber
import docx

def extract_text_from_pdf(path):
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)

def extract_text_from_docx(path):
    doc = docx.Document(path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(path)
    else:
        # fallback: read as plain text
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

def spell_and_grammar_check(text, max_problems=100):
    # Spell check (word-by-word)
    spell = SpellChecker()
    words = []
    for w in text.split():
        w_clean = ''.join(ch for ch in w if ch.isalpha()).lower()
        if w_clean:
            words.append(w_clean)
    misspelled = spell.unknown(words)
    
    # LanguageTool for grammar & context-aware spelling
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    # filter matches to common mistakes and spelling-related ones
    spelling_matches = [m for m in matches if 'spelling' in m.ruleId.lower() or m.ruleId.lower().startswith('missp')]
    
    # Prepare results
    results = {
        "simple_misspelled": sorted(list(misspelled))[:max_problems],
        "language_tool_matches": [{
            "message": m.message,
            "offset": m.offset,
            "length": m.errorLength,
            "context": text[max(0, m.offset-30): m.offset + m.errorLength + 30]
        } for m in matches[:max_problems]]
    }
    return results

def main(path):
    if not os.path.isfile(path):
        print("File not found:", path); return
    text = extract_text(path)
    print("---- Extracted text (first 600 chars) ----")
    print(text[:600])
    print("\nRunning spelling & grammar checks...")
    results = spell_and_grammar_check(text)
    print("\nSimple (fast) misspelled words (sample):")
    print(results["simple_misspelled"][:50])
    print("\nLanguageTool suggestions (sample):")
    for m in results["language_tool_matches"][:10]:
        print("-", m["message"])
        print("  context:", repr(m["context"]))
    print("\nDone. Want full JSON output? Save results to a file - I can modify script to export it.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resume_checker.py /path/to/resume.pdf")
    else:
        main(sys.argv[1])
