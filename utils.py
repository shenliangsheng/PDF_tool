import io
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter

def resize_pdf_bytes_to_a4(pdf_bytes: bytes) -> bytes:
    """把整份 PDF 所有页面统一成 A4（595×842 pt）并返回新的 bytes"""
    src = fitz.open("pdf", pdf_bytes)
    dst = fitz.open()
    a4_rect = fitz.paper_rect("a4")

    for page in src:
        new_page = dst.new_page(width=a4_rect.width, height=a4_rect.height)
        # 保持原页面比例，居中缩放
        new_page.show_pdf_page(new_page.rect, src, page.number)

    out = io.BytesIO()
    dst.save(out)
    dst.close()
    src.close()
    out.seek(0)
    return out.read()

def merge_pdfs(file_list, resize_to_a4=False):
    """合并若干上传文件，返回 bytes"""
    writer = PdfWriter()
    for f in file_list:
        data = f.read()
        if resize_to_a4:
            data = resize_pdf_bytes_to_a4(data)
        reader = PdfReader(io.BytesIO(data))
        for page in reader.pages:
            writer.add_page(page)

    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()
