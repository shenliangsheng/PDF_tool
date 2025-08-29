import streamlit as st
from streamlit_sortables import sort_items
from utils import merge_pdfs_with_adjust, resize_pdf_to_a4_keep_scale
import io
import fitz
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(page_title="PDF 工具箱", layout="wide")
st.markdown("""
<style>
.main{background-color:#f0f8ff;}
h1,h2{color:#1E90FF;}
</style>""", unsafe_allow_html=True)

st.title("📄 PDF 合并 & 拆分工具")
mode = st.sidebar.selectbox("功能", ["合并 PDF", "拆分 PDF"])

# ---------- 合并 ----------
if mode == "合并 PDF":
    st.header("合并 PDF")
    files = st.file_uploader("上传 PDF（可多选）", type=["pdf"], accept_multiple_files=True)

    if files:
        names = [f.name for f in files]
        ordered = sort_items(names)
        default_name = ordered[0].replace(".pdf", "") if ordered else "merged"
        new_name = st.text_input("合并后文件名", value=default_name)

        resize_a4 = st.checkbox("统一 A4（居中不拉伸）", value=True)

        # 生成预览字节流
        sorted_files = [next(f for f in files if f.name == n) for n in ordered]
        preview_bytes = merge_pdfs_with_adjust(
            sorted_files,
            resize_a4=resize_a4,
            rotations=st.session_state.get("rotations", {})
        )

        # ---------- 交互预览 ----------
        if preview_bytes:
            with fitz.open("pdf", preview_bytes) as doc:
                total_pages = len(doc)
                st.write(f"共 **{total_pages}** 页")
                page_idx = st.slider("选择页码", 0, total_pages - 1, 0)

                col1, col2 = st.columns([1, 3])

                with col1:
                    # 缩略图
                    pix = doc[page_idx].get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                    st.image(pix.tobytes("png"), caption=f"第 {page_idx + 1} 页")

                with col2:
                    # 高清大图
                    pix = doc[page_idx].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    st.image(pix.tobytes("png"), use_column_width=True)

                # 旋转按钮
                angle = st.selectbox("旋转角度", [0, 90, 180, 270], key=f"rot_{page_idx}")
                if st.button("应用旋转"):
                    rots = st.session_state.get("rotations", {})
                    rots[page_idx] = angle
                    st.session_state["rotations"] = rots
                    st.rerun()

        # ---------- 下载 ----------
        if st.button("确认并下载合并文件"):
            final_bytes = merge_pdfs_with_adjust(
                sorted_files,
                resize_a4=resize_a4,
                rotations=st.session_state.get("rotations", {})
            )
            st.download_button("⬇ 下载合并文件", data=final_bytes,
                               file_name=f"{new_name}.pdf", mime="application/pdf")

        if st.button("重置"):
            st.session_state.pop("rotations", None)
            st.rerun()

# ---------- 拆分 ----------
else:
    st.header("拆分 PDF")
    up_file = st.file_uploader("上传 PDF", type=["pdf"])
    if up_file:
        reader = PdfReader(up_file)
        total = len(reader.pages)
        st.write(f"共 **{total}** 页")
        split_type = st.radio("拆分方式", ["每页拆分", "按页数拆分"])
        if split_type == "按页数拆分":
            per = st.number_input("每份页数", 1, total, 1)

        if st.button("生成并下载拆分包"):
            part = 1
            outputs = []
            writer = PdfWriter()
            for idx, page in enumerate(reader.pages, 1):
                writer.add_page(page)
                if split_type == "每页拆分" or idx % per == 0 or idx == total:
                    buf = io.BytesIO()
                    writer.write(buf)
                    buf.seek(0)
                    outputs.append((f"{up_file.name}_part_{part}.pdf", buf.read()))
                    part += 1
                    writer = PdfWriter()

            for name, data in outputs:
                st.download_button(f"⬇ {name}", data=data,
                                   file_name=name, mime="application/pdf")

        if st.button("重置"):
            st.rerun()
