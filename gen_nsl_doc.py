from docx import Document
from docx.shared import Inches
import os

folder = r"C:\Academics\Minor_Project_Final\Frontend\media\nsl"

nepali_letters = [
    "क", "ख", "ग", "घ", "ङ", "च",
    "छ", "ज", "झ", "ञ", "ट", "ठ",
    "ड", "ढ", "ण", "त", "थ", "द",
    "ध", "न", "प", "फ", "ब", "भ",
    "म", "य", "र", "ल", "व", "श",
    "ष", "स", "ह", "क्ष", "त्र", "ज्ञ"
]

doc = Document()

columns = 6

for start in range(0, len(nepali_letters), columns):

    group = nepali_letters[start:start + columns]

    table = doc.add_table(rows=2, cols=columns)
    table.style = "Table Grid"

    for col, letter in enumerate(group):

        index = start + col

        # Label row
        label_cell = table.cell(0, col)
        label_cell.text = letter
        label_cell.paragraphs[0].alignment = 1

        # Image row
        image_cell = table.cell(1, col)
        paragraph = image_cell.paragraphs[0]
        paragraph.alignment = 1

        image_path = os.path.join(folder, f"{index}.jpg")

        if os.path.exists(image_path):
            run = paragraph.add_run()
            run.add_picture(
                image_path,
                width=Inches(1.2)
            )
        else:
            paragraph.add_run("Not found")

    doc.add_paragraph()

doc.save("Nepali_Alphabet_Images.docx")

print("Created Nepali_Alphabet_Images.docx")