from docx import Document

doc = Document("Chapter 2.docx")

with open("chapter2_extracted.txt", "w", encoding="utf-8") as f:
    for para in doc.paragraphs:
        f.write(para.text + "\n")

print("Chapter 2 extracted to chapter2_extracted.txt")
