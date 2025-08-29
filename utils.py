import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
import io

def resize_to_a4(pdf_bytes):
    """将PDF所有页面调整为A4大小"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    a4_width, a4_height = fitz.paper_size("a4")
    
    for page in doc:
        rect = page.rect
        if abs(rect.width - a4_width) > 1 or abs(rect.height - a4_height) > 1:
            page.set_cropbox(fitz.Rect(0, 0, a4_width, a4_height))
    
    output = io.BytesIO()
    doc.save(output)
    doc.close()
    output.seek(0)
    return output.read()

def merge_pdfs(file_list, names):
    """合并PDF并保持顺序"""
    writer = PdfWriter()
    for file in file_list:
        reader = PdfReader(file)
        for page in reader.pages:
            writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    writer.close()
    output.seek(0)
    return output.read()
