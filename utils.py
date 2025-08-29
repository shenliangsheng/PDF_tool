import io
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter

def resize_pdf_to_a4_keep_scale(pdf_bytes: bytes) -> bytes:
    """
    把每页居中缩放到 A4，不旋转、不变形
    """
    src = fitz.open("pdf", pdf_bytes)
    dst = fitz.open()
    a4_rect = fitz.paper_rect("a4")

    for page in src:
        new_page = dst.new_page(width=a4_rect.width, height=a4_rect.height)
        # 计算缩放比例，保持原比例居中
        src_rect = page.rect
        zoom = min(a4_rect.width / src_rect.width,
                   a4_rect.height / src_rect.height)
        matrix = fitz.Matrix(zoom, zoom)
        new_page.show_pdf_page(new_page.rect, src, page.number, matrix=matrix)

    out = io.BytesIO()
    dst.save(out)
    dst.close()
    src.close()
    out.seek(0)
    return out.read()

def merge_pdfs_with_adjust(file_objs, resize_a4=False, rotations=None):
    """
    合并 + 可选 A4 缩放 + 可选逐页旋转
    rotations: dict {page_index: angle(90,180,270)}
    """
    writer = PdfWriter()
    idx = 0
    for f in file_objs:
        reader = PdfReader(f)
        for p in reader.pages:
            if rotations and idx in rotations:
                p.rotate(rotations[idx])
            writer.add_page(p)
            idx += 1

    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()
