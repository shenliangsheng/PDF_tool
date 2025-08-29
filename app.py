import streamlit as st
import PyPDF2
import io
from PIL import Image
import fitz  # PyMuPDF
import os
from pathlib import Path
import base64
import tempfile
from streamlit_sortables import sort_items
import time

# 设置页面配置
st.set_page_config(
    page_title="PDF工具箱 - 合并与拆分",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #42A5F5;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1565C0;
        color: white;
    }
    .file-uploader {
        border: 2px dashed #64B5F6;
        border-radius: 10px;
        padding: 2rem;
        background-color: #E3F2FD;
        text-align: center;
    }
    .success-message {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
    }
    .warning-message {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF9800;
    }
    .file-item {
        background-color: #E3F2FD;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border: 1px solid #BBDEFB;
    }
    .preview-container {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'merged_pdf' not in st.session_state:
    st.session_state.merged_pdf = None
if 'split_pdf' not in st.st.session_state:
    st.session_state.split_pdf = None
if 'file_order' not in st.session_state:
    st.session_state.file_order = []

def convert_to_a4(pdf_bytes):
    """将PDF转换为A4大小"""
    try:
        input_pdf = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        output_pdf = PyPDF2.PdfWriter()
        
        for page_num in range(len(input_pdf.pages)):
            page = input_pdf.pages[page_num]
            # A4尺寸: 595 x 842 points
            page.mediabox.upper_right = (595, 842)
            output_pdf.add_page(page)
        
        output_buffer = io.BytesIO()
        output_pdf.write(output_buffer)
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"转换A4大小时出错: {str(e)}")
        return pdf_bytes

def merge_pdfs(files, output_filename):
    """合并PDF文件"""
    try:
        merger = PyPDF2.PdfMerger()
        
        for file_info in files:
            file_data = file_info['data']
            if st.session_state.get('convert_to_a4', False):
                file_data = convert_to_a4(file_data)
            merger.append(io.BytesIO(file_data))
        
        output_buffer = io.BytesIO()
        merger.write(output_buffer)
        merger.close()
        
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"合并PDF时出错: {str(e)}")
        return None

def split_pdf(pdf_bytes, split_option='each_page'):
    """拆分PDF文件"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(pdf_reader.pages)
        split_files = []
        
        if split_option == 'each_page':
            # 每页拆分为一个文件
            for page_num in range(total_pages):
                pdf_writer = PyPDF2.PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])
                
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                split_files.append({
                    'name': f'page_{page_num + 1}.pdf',
                    'data': output_buffer.getvalue()
                })
        
        elif split_option == 'custom':
            # 自定义拆分逻辑（这里可以扩展）
            st.info("自定义拆分功能待实现")
        
        return split_files
    except Exception as e:
        st.error(f"拆分PDF时出错: {str(e)}")
        return []

def get_pdf_preview(pdf_bytes, page_number=0):
    """获取PDF预览图"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
        img_data = pix.tobytes("png")
        doc.close()
        return img_data
    except:
        return None

def display_pdf_preview(pdf_bytes, title="PDF预览"):
    """显示PDF预览"""
    img_data = get_pdf_preview(pdf_bytes)
    if img_data:
        st.image(img_data, caption=title, use_column_width=True)
    else:
        st.warning("无法生成预览")

def main():
    # 页面标题
    st.markdown('<div class="main-header">📄 PDF工具箱 - 合并与拆分</div>', unsafe_allow_html=True)
    
    # 创建选项卡
    tab1, tab2 = st.tabs(["📁 PDF合并", "✂️ PDF拆分"])
    
    with tab1:
        st.markdown('<div class="sub-header">PDF文件合并工具</div>', unsafe_allow_html=True)
        
        # 文件上传区域
        st.markdown('<div class="file-uploader">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "拖拽或选择PDF文件",
            type="pdf",
            accept_multiple_files=True,
            help="支持多选PDF文件"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            # 处理新上传的文件
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in [f['name'] for f in st.session_state.uploaded_files]:
                    file_data = uploaded_file.getvalue()
                    st.session_state.uploaded_files.append({
                        'name': uploaded_file.name,
                        'data': file_data,
                        'size': len(file_data)
                    })
            
            # 显示文件列表和排序功能
            if st.session_state.uploaded_files:
                st.markdown("### 📋 文件列表（可拖拽排序）")
                
                # 创建可排序的文件列表
                file_items = []
                for i, file_info in enumerate(st.session_state.uploaded_files):
                    file_items.append({
                        'id': i,
                        'content': f"📄 {file_info['name']} ({file_info['size'] // 1024} KB)"
                    })
                
                # 使用sortable组件（需要安装streamlit-sortables）
                try:
                    sorted_items = sort_items(file_items, direction="vertical")
                    if sorted_items != file_items:
                        # 更新文件顺序
                        new_order = [item['id'] for item in sorted_items]
                        st.session_state.uploaded_files = [st.session_state.uploaded_files[i] for i in new_order]
                except:
                    # 如果sortable不可用，显示普通列表
                    for i, file_info in enumerate(st.session_state.uploaded_files):
                        st.markdown(f'<div class="file-item">📄 {file_info["name"]}</div>', unsafe_allow_html=True)
                
                # 合并选项
                col1, col2 = st.columns(2)
                with col1:
                    default_name = st.session_state.uploaded_files[0]['name'].replace('.pdf', '') + '_合并.pdf'
                    output_filename = st.text_input(
                        "输出文件名",
                        value=default_name,
                        help="合并后的PDF文件名称"
                    )
                
                with col2:
                    st.session_state.convert_to_a4 = st.checkbox(
                        "统一转换为A4大小",
                        value=True,
                        help="将所有页面统一转换为A4尺寸"
                    )
                
                # 预览区域
                if len(st.session_state.uploaded_files) > 0:
                    st.markdown("### 👀 预览")
                    preview_col1, preview_col2 = st.columns(2)
                    
                    with preview_col1:
                        st.markdown("**首个文件预览**")
                        display_pdf_preview(st.session_state.uploaded_files[0]['data'], "第一个文件")
                    
                    with preview_col2:
                        if len(st.session_state.uploaded_files) > 1:
                            st.markdown("**末尾文件预览**")
                            display_pdf_preview(st.session_state.uploaded_files[-1]['data'], "最后一个文件")
                
                # 合并按钮
                if st.button("🚀 开始合并", use_container_width=True):
                    with st.spinner("正在合并PDF文件..."):
                        merged_data = merge_pdfs(st.session_state.uploaded_files, output_filename)
                        
                        if merged_data:
                            st.session_state.merged_pdf = merged_data
                            st.markdown('<div class="success-message">✅ PDF合并成功！</div>', unsafe_allow_html=True)
                            
                            # 提供下载
                            st.download_button(
                                label="📥 下载合并后的PDF",
                                data=merged_data,
                                file_name=output_filename,
                                mime="application/pdf",
                                use_container_width=True
                            )
            
            else:
                st.info("请上传PDF文件")
        
        else:
            st.info("👆 请上传需要合并的PDF文件")
    
    with tab2:
        st.markdown('<div class="sub-header">PDF文件拆分工具</div>', unsafe_allow_html=True)
        
        # 文件上传区域
        st.markdown('<div class="file-uploader">', unsafe_allow_html=True)
        split_file = st.file_uploader(
            "选择要拆分的PDF文件",
            type="pdf",
            accept_multiple_files=False,
            key="split_uploader"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if split_file:
            file_data = split_file.getvalue()
            
            # 显示文件信息和预览
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.info(f"**文件信息**\n\n"
                       f"📄 名称: {split_file.name}\n"
                       f"📊 大小: {len(file_data) // 1024} KB\n"
                       f"📑 页数: {len(PyPDF2.PdfReader(io.BytesIO(file_data)).pages)}")
            
            with col2:
                st.markdown("**文件预览**")
                display_pdf_preview(file_data, split_file.name)
            
            # 拆分选项
            split_option = st.radio(
                "拆分方式",
                options=["each_page", "custom"],
                format_func=lambda x: "每页拆分为一个文件" if x == "each_page" else "自定义拆分",
                horizontal=True
            )
            
            if split_option == "custom":
                st.warning("自定义拆分功能正在开发中，目前仅支持每页拆分")
            
            # 拆分按钮
            if st.button("✂️ 开始拆分", use_container_width=True):
                with st.spinner("正在拆分PDF文件..."):
                    split_files = split_pdf(file_data, split_option)
                    
                    if split_files:
                        st.markdown('<div class="success-message">✅ PDF拆分成功！</div>', unsafe_allow_html=True)
                        st.markdown(f"**生成 {len(split_files)} 个文件:**")
                        
                        # 创建下载链接
                        for i, file_info in enumerate(split_files):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"📄 {file_info['name']}")
                            with col2:
                                st.download_button(
                                    label="下载",
                                    data=file_info['data'],
                                    file_name=file_info['name'],
                                    mime="application/pdf",
                                    key=f"split_{i}"
                                )
        
        else:
            st.info("👆 请上传需要拆分的PDF文件")
    
    # 页脚信息
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "📄 PDF工具箱 | 基于Streamlit构建 | 支持合并与拆分功能"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
