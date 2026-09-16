from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Read the revised text
with open("Chapter_2_Revised.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Create document
doc = Document()

# Add title
title = doc.add_heading('Chapter 2', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Add student names
doc.add_paragraph('Prominance Fungurayi\t\tR251946T')
doc.add_paragraph('Ashton Kahlari\t\t\tR252989W')
doc.add_paragraph()  # Empty line

# Parse and add content
lines = content.split('\n')
current_heading = None

for line in lines:
    line = line.strip()
    if not line:
        doc.add_paragraph()
        continue
    
    # Check for headings
    if line.startswith('2.') and ('.' in line[3:]) or line.startswith('Chapter 2:'):
        if line.startswith('Chapter 2:'):
            doc.add_heading(line, level=1)
        elif line.startswith('2.'):
            # Determine heading level
            if line.count('.') == 1:  # 2.1, 2.2, etc.
                doc.add_heading(line, level=1)
            elif line.count('.') == 2:  # 2.1.1, 2.2.1, etc.
                doc.add_heading(line, level=2)
            elif line.count('.') == 3:  # 2.4.1.1, etc.
                doc.add_heading(line, level=3)
        else:
            doc.add_heading(line, level=1)
    elif line.startswith('Table 2.1:'):
        doc.add_heading(line, level=2)
    elif line.startswith('|'):
        # Table row
        cells = [cell.strip() for cell in line.split('|')]
        cells = [c for c in cells if c]  # Remove empty cells
        if cells:
            # This is a simplified table handling
            p = doc.add_paragraph(' | '.join(cells))
            p.style = 'Normal'
    elif line.startswith('[') and line.endswith(']'):
        # Reference
        p = doc.add_paragraph(line)
        p.style = 'Normal'
        p.runs[0].font.size = Pt(9)
    else:
        # Regular paragraph
        p = doc.add_paragraph(line)
        p.style = 'Normal'

# Save document
doc.save('Chapter_2_Revised.docx')
print("Chapter 2 revised saved as Chapter_2_Revised.docx")
