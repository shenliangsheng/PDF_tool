import streamlit as st
from streamlit_sortables import sort_items
from utils import merge_pdfs, resize_pdf_bytes_to_a4
import io
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(page_title="PDF 工具箱", layout="wide")
st.markdown("""
<style>
.main {background-color:#f0f8ff;}
h1,h2 {color:#1E90FF;}
</style>""", unsafe_allow_html=True)

st.title("📄 PDF 合并 & 拆分工具")

mode = st.sidebar.selectbox("选择功能", ["合并 PDF", "拆分 PDF"])

# ---------- 合并 ----------
if mode == "合并 PDF":
    st.header("合并 PDF")
    files = st.file_uploader("上传 PDF（可多选）", type=["pdf"], accept_multiple_files=True)

    if files:
        names = [f.name for f in files]
        ordered = sort_items(names)

        default_name = ordered[0].replace(".pdf", "") if ordered else "merged"
        new_name = st.text_input("合并后文件名", value=default_name)
        a4_switch = st.checkbox("一键设为 A4 大小", value=True)

        if st.button("预览并下载合并文件"):
            # 按顺序重组文件对象
            sorted_files = [next(f for f in files if f.name == n) for n in ordered]
            merged_bytes = merge_pdfs(sorted_files, resize_to_a4=a4_switch)
            st.success("合并完成！")
            st.download_button("⬇ 下载合并文件", data=merged_bytes,
                               file_name=f"{new_name}.pdf", mime="application/pdf")

        if st.button("重置"):
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
            per = st.number_input("每份页数", min_value=1, max_value=total, value=1)

        if st.button("生成并下载拆分文件"):
            part = 1
            writer = PdfWriter()
            outputs = []

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
