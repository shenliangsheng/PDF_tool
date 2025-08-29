import streamlit as st
from utils import merge_pdfs, resize_to_a4
from streamlit_sortables import sort_items
import os
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(page_title="PDF工具箱", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f0f8ff; }
    h1, h2 { color: #1E90FF; }
</style>
""", unsafe_allow_html=True)

st.title("📄 PDF合并与拆分工具")

mode = st.sidebar.selectbox("选择功能", ["合并PDF", "拆分PDF"])

# ---------------- 合并功能 ----------------
if mode == "合并PDF":
    st.header("合并PDF")
    uploaded = st.file_uploader("上传PDF文件", type=["pdf"], accept_multiple_files=True)
    
    if uploaded:
        names = [f.name for f in uploaded]
        ordered = sort_items(names)
        
        st.write("拖拽调整顺序：")
        
        default_name = ordered[0].replace(".pdf", "") if ordered else "merged"
        custom_name = st.text_input("合并后文件名", value=default_name)
        
        a4_resize = st.checkbox("一键设为A4大小", value=True)
        
        if st.button("预览合并"):
            sorted_files = [next(f for f in uploaded if f.name == n) for n in ordered]
            if a4_resize:
                sorted_files = [io.BytesIO(resize_to_a4(f.read())) for f in sorted_files]
            merged = merge_pdfs(sorted_files, ordered)
            st.success("合并完成！")
            st.download_button("下载合并文件", data=merged, file_name=f"{custom_name}.pdf")
        
        if st.button("重置"):
            st.rerun()

# ---------------- 拆分功能 ----------------
else:
    st.header("拆分PDF")
    file = st.file_uploader("上传PDF", type=["pdf"])
    
    if file:
        reader = PdfReader(file)
        total = len(reader.pages)
        
        st.write(f"共 {total} 页")
        split_type = st.radio("拆分方式", ["每页拆分", "自定义页数"])
        
        if split_type == "自定义页数":
            pages_per_file = st.number_input("每份页数", min_value=1, max_value=total, value=1)
        
        if st.button("开始拆分"):
            writer = PdfWriter()
            outputs = []
            for i, page in enumerate(reader.pages, 1):
                writer.add_page(page)
                if split_type == "每页拆分" or i % pages_per_file == 0 or i == total:
                    output = io.BytesIO()
                    writer.write(output)
                    writer = PdfWriter()
                    output.seek(0)
                    outputs.append((f"{file.name}_part_{i//pages_per_file+1}.pdf", output.read()))
            
            for name, data in outputs:
                st.download_button(f"下载 {name}", data=data, file_name=name)
        
        if st.button("重置"):
            st.rerun()
