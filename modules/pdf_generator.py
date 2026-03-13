from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_pdf(text, path):

    c = canvas.Canvas(path, pagesize=letter)

    width, height = letter
    y = height - 50

    for line in text.split("\n"):

        c.drawString(50, y, line)

        y -= 20

        if y < 50:
            c.showPage()
            y = height - 50

    c.save()