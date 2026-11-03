from docx import Document
from docx.shared import Inches
import string
import os

folder = r"C:\Academics\Minor_Project_Final\Frontend\media\asl"

doc = Document()

columns = 5
letters = string.ascii_lowercase

images = [
    os.path.join(folder, f"{letter}.jpeg")
    for letter in letters
]

for start in range(0, len(images), columns):

    group = images[start:start + columns]

    # Label row + image row
    table = doc.add_table(rows=2, cols=columns)
    table.style = "Table Grid"

    for col, image_path in enumerate(group):

        letter = letters[start + col].upper()

        # Label: A B C D E
        label_cell = table.cell(0, col)
        label_cell.text = letter
        label_cell.paragraphs[0].alignment = 1

        # Image: a.jpeg b.jpeg c.jpeg ...
        image_cell = table.cell(1, col)
        paragraph = image_cell.paragraphs[0]
        paragraph.alignment = 1

        if os.path.exists(image_path):
            run = paragraph.add_run()
            run.add_picture(
                image_path,
                width=Inches(1.3)
            )

    doc.add_paragraph()

doc.save("ASL_Images.docx")

print("ASL_Images.docx created successfully.")