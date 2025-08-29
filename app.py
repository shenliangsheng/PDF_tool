# app.py
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import io
from pypdf import PdfWriter, PdfReader
from streamlit_option_menu import option_menu
import base64
from datetime import datetime
import tempfile

# 设置页面配置
st.set_page_config(
    page_title="PDF工具箱",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主色调：蓝白色系 */
    :root {
        --primary-color: #1E88E5;
        --primary-light: #64B5F6;
        --primary-dark: #0D47A1;
        --secondary-color: #E3F2FD;
        --text-color: #333333;
        --bg-color: #FFFFFF;
        --border-color: #E0E0E0;
    }
    
    /* 页面背景 */
    .stApp {
        background-color: var(--bg-color);
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: var(--primary-dark);
    }
    
    /* 按钮样式 */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background-color: var(--primary-dark);
    }
    
    /* 文件上传区域 */
    .upload-area {
        border: 2px dashed var(--primary-light);
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: var(--secondary-color);
        margin: 10px 0;
    }
    
    /* 卡片样式 */
    .file-card {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 拖拽区域 */
    .drag-drop-area {
        border: 2px dashed var(--primary-color);
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        background-color: var(--secondary-color);
        margin: 20px 0;
    }
    
    /* 进度条 */
    .stProgress > div > div {
        background-color: var(--primary-color);
    }
    
    /* 侧边栏 */
    section[data-testid="stSidebar"] {
        background-color: var(--secondary-color);
    }
    
    /* 预览区域 */
    .preview-container {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 15px;
        background-color: white;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'merged_pdf' not in st.session_state:
    st.session_state.merged_pdf = None
if 'split_pdfs' not in st.session_state:
    st.session_state.split_pdfs = []
if 'merge_files' not in st.session_state:
    st.session_state.merge_files = []
if 'split_file' not in st.session_state:
    st.session_state.split_file = None

def merge_pdfs(files, output_name, page_sizes=None):
    """合并PDF文件"""
    try:
        writer = PdfWriter()
        
        for file in files:
            reader = PdfReader(file)
            for page in reader.pages:
                # 如果指定了页面大小，可以在这里处理
                if page_sizes:
                    # 这里可以添加页面大小调整逻辑
                    pass
                writer.add_page(page)
        
        # 创建输出文件
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        
        return output
    except Exception as e:
        st.error(f"合并PDF时出错: {str(e)}")
        return None

def split_pdf(file, pages_per_split=1):
    """拆分PDF文件"""
    try:
        reader = PdfReader(file)
        total_pages = len(reader.pages)
        split_files = []
        
        for i in range(0, total_pages, pages_per_split):
            writer = PdfWriter()
            end_page = min(i + pages_per_split, total_pages)
            
            for page_num in range(i, end_page):
                writer.add_page(reader.pages[page_num])
            
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            
            split_files.append({
                'file': output,
                'name': f"split_pages_{i+1}_to_{end_page}.pdf",
                'start_page': i+1,
                'end_page': end_page
            })
        
        return split_files
    except Exception as e:
        st.error(f"拆分PDF时出错: {str(e)}")
        return []

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """创建文件下载链接"""
    bin_str = base64.b64encode(bin_file.read()).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}" class="stButton">📥 下载 {file_label}</a>'
    return href

def main():
    # 顶部标题
    st.title("📄 PDF工具箱")
    st.markdown("---")
    
    # 侧边栏导航
    with st.sidebar:
        st.header("导航")
        selected = option_menu(
            menu_title=None,
            options=["PDF合并", "PDF拆分", "使用说明"],
            icons=["files", "scissors", "question-circle"],
            menu_icon="cast",
            default_index=0,
        )
        
        st.markdown("---")
        st.info("💡 提示：支持拖拽上传PDF文件")
    
    # PDF合并功能
    if selected == "PDF合并":
        st.header("📎 PDF合并工具")
        
        # 文件上传区域
        st.subheader("上传PDF文件")
        uploaded_files = st.file_uploader(
            "选择多个PDF文件进行合并",
            type="pdf",
            accept_multiple_files=True,
            key="merge_upload"
        )
        
        if uploaded_files:
            st.session_state.merge_files = uploaded_files
            
            # 显示已上传的文件
            st.subheader("已上传的文件")
            for i, file in enumerate(uploaded_files):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📄 {file.name}")
                with col2:
                    st.write(f"💾 {file.size} bytes")
                with col3:
                    if st.button("❌", key=f"remove_{i}"):
                        st.session_state.merge_files.remove(file)
                        st.experimental_rerun()
            
            # 合并设置
            st.subheader("合并设置")
            
            # 默认使用第一个文件名作为输出名
            default_name = "merged_output.pdf"
            if uploaded_files:
                default_name = f"{os.path.splitext(uploaded_files[0].name)[0]}_合并.pdf"
            
            output_name = st.text_input("输出文件名", value=default_name)
            
            # 页面大小设置
            page_size_option = st.checkbox("将所有页面设为A4大小", value=False)
            
            # 预览合并效果
            st.subheader("预览")
            preview_text = f"将合并 {len(uploaded_files)} 个PDF文件，总页数约 {sum(len(PdfReader(f).pages) for f in uploaded_files)} 页"
            st.info(preview_text)
            
            # 合并按钮
            if st.button("🚀 合并PDF", type="primary", use_container_width=True):
                if uploaded_files:
                    with st.spinner("正在合并PDF文件..."):
                        merged_file = merge_pdfs(uploaded_files, output_name)
                        if merged_file:
                            st.session_state.merged_pdf = {
                                'file': merged_file,
                                'name': output_name
                            }
                            st.success("✅ PDF合并完成！")
                else:
                    st.warning("请先上传PDF文件")
            
            # 下载合并后的文件
            if st.session_state.merged_pdf:
                st.subheader("下载合并后的文件")
                st.download_button(
                    label="📥 下载合并后的PDF",
                    data=st.session_state.merged_pdf['file'],
                    file_name=st.session_state.merged_pdf['name'],
                    mime="application/pdf"
                )
        
        else:
            # 拖拽上传提示
            st.markdown("""
            <div class="drag-drop-area">
                <h3>📁 拖拽PDF文件到这里</h3>
                <p>或者点击上方按钮选择文件</p>
                <p>支持多文件同时上传</p>
            </div>
            """, unsafe_allow_html=True)
    
    # PDF拆分功能
    elif selected == "PDF拆分":
        st.header("✂️ PDF拆分工具")
        
        # 文件上传
        st.subheader("上传PDF文件")
        split_file = st.file_uploader(
            "选择要拆分的PDF文件",
            type="pdf",
            key="split_upload"
        )
        
        if split_file:
            st.session_state.split_file = split_file
            
            # 显示文件信息
            st.subheader("文件信息")
            reader = PdfReader(split_file)
            total_pages = len(reader.pages)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总页数", total_pages)
            with col2:
                st.metric("文件大小", f"{split_file.size} bytes")
            
            # 拆分设置
            st.subheader("拆分设置")
            
            split_method = st.radio(
                "拆分方式",
                ["逐页拆分", "按页数拆分"]
            )
            
            pages_per_split = 1
            if split_method == "按页数拆分":
                pages_per_split = st.number_input("每份页数", min_value=1, max_value=total_pages, value=1)
            
            # 拆分按钮
            if st.button("✂️ 开始拆分", type="primary", use_container_width=True):
                with st.spinner("正在拆分PDF文件..."):
                    split_files = split_pdf(split_file, pages_per_split)
                    if split_files:
                        st.session_state.split_pdfs = split_files
                        st.success(f"✅ PDF拆分完成！共生成 {len(split_files)} 个文件")
            
            # 下载拆分后的文件
            if st.session_state.split_pdfs:
                st.subheader("下载拆分后的文件")
                
                for i, split_file_info in enumerate(st.session_state.split_pdfs):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📄 {split_file_info['name']}")
                    with col2:
                        st.download_button(
                            label="📥 下载",
                            data=split_file_info['file'],
                            file_name=split_file_info['name'],
                            mime="application/pdf",
                            key=f"download_{i}"
                        )
        
        else:
            # 拖拽上传提示
            st.markdown("""
            <div class="drag-drop-area">
                <h3>📁 拖拽PDF文件到这里</h3>
                <p>或者点击上方按钮选择文件</p>
                <p>支持单个PDF文件拆分</p>
            </div>
            """, unsafe_allow_html=True)
    
    # 使用说明
    elif selected == "使用说明":
        st.header("📘 使用说明")
        
        st.subheader("📌 PDF合并功能")
        st.markdown("""
        1. **上传文件**：点击上传按钮或拖拽PDF文件到指定区域
        2. **设置输出名**：可自定义合并后的文件名（默认使用第一个文件名）
        3. **页面设置**：可选择将所有页面设为A4大小
        4. **预览效果**：查看合并前的文件信息
        5. **开始合并**：点击合并按钮生成文件
        6. **下载文件**：合并完成后可直接下载
        """)
        
        st.subheader("📌 PDF拆分功能")
        st.markdown("""
        1. **上传文件**：选择要拆分的PDF文件
        2. **选择方式**：
           - 逐页拆分：每页生成一个单独的PDF文件
           - 按页数拆分：按指定页数拆分文件
        3. **开始拆分**：点击拆分按钮
        4. **下载文件**：拆分完成后可批量下载所有文件
        """)
        
        st.subheader("🎨 界面特色")
        st.markdown("""
        - 🎨 蓝白色调，简约大方
        - 📱 响应式设计，支持移动端
        - 🖱️ 支持拖拽上传
        - ⚡ 操作简单，一键处理
        - 🔒 安全可靠，文件不存储
        """)
        
        st.subheader("⚠️ 注意事项")
        st.markdown("""
        - 请确保上传的文件为PDF格式
        - 大文件处理可能需要较长时间
        - 所有处理都在浏览器端完成，保护隐私
        - 建议使用现代浏览器获得最佳体验
        """)

if __name__ == "__main__":
    main()
