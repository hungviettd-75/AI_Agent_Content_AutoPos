"""ui/tab_knowledge.py
======================
Giao diện quản lý Trung tâm tri thức (Knowledge Center) nâng cao.
Hỗ trợ quản lý Folder, Tag, Collection, Version.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from database.repositories import KnowledgeRepository
from core.document_parser import parse_document
from core.audit_logger import log_action, AuditAction
from core.rbac import render_role_badge

def render_tab_knowledge(workspace_id: int, user_id: int, user_email: str, role: str):
    st.markdown(render_role_badge(role), unsafe_allow_html=True)
    st.header("🧠 Knowledge Center — Trung tâm tri thức")
    st.caption("Tải lên tài liệu hoặc nhập liên kết trang web để tích lũy kho tri thức phục vụ sinh nội dung AI.")

    # Lấy toàn bộ danh sách hiện tại của Workspace để biết Folder / Collection sẵn có
    raw_df = KnowledgeRepository.get_knowledge_posts(workspace_id=workspace_id)
    
    existing_folders = ["Chung"]
    existing_collections = ["Mặc định"]
    
    if not raw_df.empty:
        if "folder" in raw_df.columns:
            folders = raw_df["folder"].dropna().unique().tolist()
            for f in folders:
                if f and f not in existing_folders:
                    existing_folders.append(f)
        if "collection" in raw_df.columns:
            collections = raw_df["collection"].dropna().unique().tolist()
            for c in collections:
                if c and c not in existing_collections:
                    existing_collections.append(c)

    # ─── PHẦN 1: THÊM TRI THỨC MỚI ─────────────────────────────────────────
    if role == "viewer":
        st.warning("⚠️ Vai trò Viewer chỉ có quyền xem tri thức, không thể tải lên hoặc thêm tri thức mới.")
    else:
        st.subheader("➕ Thêm tri thức mới")
        source_type = st.radio("Chọn nguồn tri thức:", ["Tải lên tài liệu", "Liên kết Website (URL)"], horizontal=True)

        # Form điền siêu dữ liệu nâng cao
        st.markdown("##### 🏷️ Cấu hình cấu trúc tri thức")
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        
        # Folder (Thư mục nhóm)
        folder_option = meta_col1.selectbox("Chọn Thư mục (Folder):", options=existing_folders + ["+ Tạo thư mục mới..."])
        if folder_option == "+ Tạo thư mục mới...":
            folder = meta_col1.text_input("Tên thư mục mới:", value="Chính sách")
        else:
            folder = folder_option
            
        # Collection (Bộ sưu tập chuyên đề)
        collection_option = meta_col2.selectbox("Chọn Bộ sưu tập (Collection):", options=existing_collections + ["+ Tạo bộ sưu tập mới..."])
        if collection_option == "+ Tạo bộ sưu tập mới...":
            collection = meta_col2.text_input("Tên bộ sưu tập mới:", value="Sản phẩm 2026")
        else:
            collection = collection_option

        # Version & Tags
        version = meta_col3.text_input("Phiên bản (Version):", value="1.0", help="Ví dụ: 1.0, 2.1. Để quản trị cập nhật.")
        tags_input = st.text_input("Nhãn (Tags) - Phân cách bằng dấu phẩy:", placeholder="ai, marketing, guide, product")
        tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]

        if source_type == "Tải lên tài liệu":
            uploaded_file = st.file_uploader(
                "Chọn file tài liệu:",
                type=["pdf", "docx", "txt", "md"],
                help="Hỗ trợ định dạng PDF, Word (DOCX), Text (TXT) và Markdown (MD)."
            )
            
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                filename = uploaded_file.name
                
                # Input tiêu đề & metadata
                default_title = filename.rsplit('.', 1)[0]
                title = st.text_input("Tiêu đề tri thức:", value=default_title)
                k_type = st.selectbox("Loại tri thức:", ["Tài liệu hướng dẫn", "Case Study", "Sản phẩm & Dịch vụ", "Bài viết kỹ thuật", "Khác"])
                
                if st.button("💾 Xử lý & Lưu vào kho tri thức", key="btn_save_file"):
                    with st.spinner("Đang trích xuất và phân tích nội dung tài liệu..."):
                        res = parse_document(file_bytes=file_bytes, filename=filename)
                        if res["error"]:
                            st.error(f"❌ {res['error']}")
                        elif not res["text"].strip():
                            st.error("❌ Không thể trích xuất văn bản từ tài liệu này (file rỗng hoặc dạng ảnh scan chưa OCR).")
                        else:
                            # Lưu vào database
                            k_id = KnowledgeRepository.save_knowledge_post(
                                date=datetime.now().strftime("%d/%m/%Y %H:%M"),
                                platform="knowledge_center",
                                topic=title,
                                audience="Toàn bộ",
                                tool_name="Tài liệu tải lên",
                                knowledge_type=k_type,
                                difficulty="N/A",
                                content=res["text"],
                                summary=res["preview"],
                                status="Active",
                                workspace_id=workspace_id,
                                created_by=user_id,
                                folder=folder,
                                collection=collection,
                                version=version,
                                tags=tags
                            )
                            
                            # Ghi Audit Log
                            log_action(
                                action=AuditAction.CREATE_KNOWLEDGE,
                                user_id=user_id,
                                user_email=user_email,
                                workspace_id=workspace_id,
                                entity_type="knowledge",
                                entity_id=k_id,
                                description=f"Tải lên tài liệu '{title}' -> Thư mục: {folder}, BST: {collection}, Phiên bản: {version}"
                            )
                            st.success(f"✅ Đã lưu thành công tài liệu tri thức '{title}' ({res['word_count']} từ)!")
                            st.rerun()

        elif source_type == "Liên kết Website (URL)":
            url = st.text_input("Nhập địa chỉ Website URL:", placeholder="https://example.com/blog-post")
            if url:
                title = st.text_input("Tiêu đề tri thức:", placeholder="Nhập tiêu đề gợi nhớ hoặc để trống tự động lấy")
                k_type = st.selectbox("Loại tri thức:", ["Bài viết blog/tin tức", "Trang tài liệu", "Trang chủ sản phẩm", "Khác"])
                
                if st.button("🌐 Cào dữ liệu & Lưu vào kho tri thức", key="btn_save_url"):
                    with st.spinner("Đang tải dữ liệu từ website..."):
                        res = parse_document(url=url)
                        if res["error"]:
                            st.error(f"❌ {res['error']}")
                        elif not res["text"].strip():
                            st.error("❌ Nội dung cào được rỗng. Hãy kiểm tra lại URL hoặc cấu trúc trang.")
                        else:
                            final_title = title.strip() if title.strip() else url
                            # Lưu database
                            k_id = KnowledgeRepository.save_knowledge_post(
                                date=datetime.now().strftime("%d/%m/%Y %H:%M"),
                                platform="knowledge_center",
                                topic=final_title,
                                audience="Toàn bộ",
                                tool_name="Website Scraper",
                                knowledge_type=k_type,
                                difficulty="N/A",
                                content=res["text"],
                                summary=res["preview"],
                                status="Active",
                                workspace_id=workspace_id,
                                created_by=user_id,
                                folder=folder,
                                collection=collection,
                                version=version,
                                tags=tags
                            )
                            
                            # Audit log
                            log_action(
                                action=AuditAction.CREATE_KNOWLEDGE,
                                user_id=user_id,
                                user_email=user_email,
                                workspace_id=workspace_id,
                                entity_type="knowledge",
                                entity_id=k_id,
                                description=f"Cào dữ liệu từ URL: {url} -> Thư mục: {folder}, BST: {collection}"
                            )
                            st.success(f"✅ Đã tải và lưu thành công nội dung từ website ({res['word_count']} từ)!")
                            st.rerun()

    st.markdown("---")

    # ─── PHẦN 2: DANH SÁCH & TÌM KIẾM TRI THỨC ──────────────────────────────
    st.subheader("📚 Kho tri thức hiện tại của Workspace")
    
    # Bộ lọc nâng cao Folder / Collection
    f_col1, f_col2, f_col3 = st.columns(3)
    filter_folder = f_col1.selectbox("📁 Lọc theo Thư mục:", options=["Tất cả"] + existing_folders)
    filter_collection = f_col2.selectbox("📦 Lọc theo Bộ sưu tập:", options=["Tất cả"] + existing_collections)
    search_keyword = f_col3.text_input("🔍 Tìm kiếm theo từ khóa:", "")
    
    # Lấy dữ liệu
    if search_keyword.strip():
        from database.models.knowledge import KnowledgeModel
        raw_list = KnowledgeModel.search(search_keyword.strip(), workspace_id=workspace_id)
        df = pd.DataFrame(raw_list) if raw_list else pd.DataFrame()
    else:
        df = KnowledgeRepository.get_knowledge_posts(workspace_id=workspace_id)
        
    if df.empty:
        st.info("📭 Kho tri thức của Workspace hiện đang trống. Hãy thêm tài liệu hoặc website.")
        return

    # Lọc cục bộ bằng pandas để tối ưu
    if filter_folder != "Tất cả" and "folder" in df.columns:
        df = df[df["folder"] == filter_folder]
    if filter_collection != "Tất cả" and "collection" in df.columns:
        df = df[df["collection"] == filter_collection]

    if df.empty:
        st.info("📭 Không tìm thấy tài liệu phù hợp với bộ lọc thư mục/bộ sưu tập.")
        return

    # Hiển thị danh sách dạng bảng
    display_df = df.copy()
    if "created_at" in display_df.columns:
        display_df["Ngày tạo"] = display_df["created_at"].apply(lambda x: x[:10] if isinstance(x, str) else "")
    elif "date" in display_df.columns:
        display_df["Ngày tạo"] = display_df["date"].apply(lambda x: x[:10] if isinstance(x, str) else "")
        
    display_df["Tiêu đề"] = display_df.get("title", display_df.get("topic", "N/A"))
    display_df["Thư mục"] = display_df.get("folder", "Chung")
    display_df["Bộ sưu tập"] = display_df.get("collection", "Mặc định")
    display_df["Phiên bản"] = display_df.get("version", "1.0")
    
    show_cols = ["id", "Tiêu đề", "Thư mục", "Bộ sưu tập", "Phiên bản", "Ngày tạo"]
    st.dataframe(display_df[[c for c in show_cols if c in display_df.columns]], use_container_width=True, hide_index=True)

    # Chọn xem chi tiết hoặc Xóa
    col_sel, col_del = st.columns([3, 1])
    with col_sel:
        selected_id = st.selectbox(
            "🔎 Chọn tri thức để xem chi tiết:",
            options=df["id"].tolist(),
            format_func=lambda x: f"ID {x} - {df[df['id'] == x]['title'].values[0] if 'title' in df.columns else df[df['id'] == x]['topic'].values[0]}"
        )
    
    if selected_id:
        from database.models.knowledge import KnowledgeModel
        item = KnowledgeModel.get_by_id(selected_id)
        if item:
            st.markdown(f"### 📖 {item.get('title', item.get('topic', ''))}")
            
            # Show Tags / Badges
            tag_list = item.get("tags")
            if tag_list and isinstance(tag_list, list):
                badges_html = " ".join([f"<span style='background:#f1f5f9;color:#475569;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-right:6px'>🏷️ {t}</span>" for t in tag_list])
                st.markdown(badges_html, unsafe_allow_html=True)
                
            st.caption(f"📁 Thư mục: **{item.get('folder', 'Chung')}** | 📦 Bộ sưu tập: **{item.get('collection', 'Mặc định')}** | 🔄 Phiên bản: **{item.get('version', '1.0')}**")
            
            with st.expander("📄 Xem tóm tắt nội dung", expanded=True):
                st.write(item.get("summary", ""))
                
            with st.expander("📝 Chi tiết văn bản gốc đầy đủ", expanded=False):
                st.text_area("Văn bản gốc", value=item.get("content", ""), height=300, disabled=True)

            if role != "viewer":
                with col_del:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Xóa tri thức này", key="btn_del_knowledge", type="primary"):
                        if KnowledgeRepository.delete_knowledge_post(selected_id):
                            log_action(
                                action=AuditAction.DELETE_POST,
                                user_id=user_id,
                                user_email=user_email,
                                workspace_id=workspace_id,
                                entity_type="knowledge",
                                entity_id=selected_id,
                                description=f"Xóa tài liệu tri thức '{item.get('title', item.get('topic', ''))}'"
                            )
                            st.success("🗑️ Đã xóa tri thức khỏi hệ thống!")
                            st.rerun()
