import streamlit as st
import pandas as pd
from database.repositories import PostRepository, KnowledgeRepository
from core.doc_exporter import export_post_to_pdf, export_all_posts_to_pdf, export_knowledge_to_pdf, export_knowledge_to_docx, export_knowledge_to_csv

def render_tab_history(workspace_id: int = None, role: str = "editor"):
    role = (role or "editor").lower()
    can_export = role not in ("viewer",)
    st.header("Kho lưu trữ & Xuất Dữ Liệu")
    df = PostRepository.get_all_posts(workspace_id=workspace_id)

    if not df.empty:
        st.info("💡 **Mẹo:** Nhấp vào một dòng trong bảng bên dưới để chọn bài viết muốn tải PDF chuyên nghiệp.")
        
        selection = st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        selected_rows = selection.get("selection", {}).get("rows", [])
        
        if selected_rows:
            selected_idx = selected_rows[0]
            row = df.iloc[selected_idx]
            
            st.markdown(f"### 📋 Đã chọn: {row['topic'][:100]}")
            
            col_pdf_one, col_pdf_all, col_csv = st.columns([1, 1, 1])
            with col_pdf_one:
                pdf_bytes_hist = export_post_to_pdf(row['topic'], row['platform'], row['content'])
                if pdf_bytes_hist:
                    st.download_button(f"📥 Tải PDF Bài chọn", data=pdf_bytes_hist, file_name=f"Post_{row['id']}.pdf")
            if can_export:
                with col_pdf_all:
                    pdf_all = export_all_posts_to_pdf(df)
                    if pdf_all:
                        st.download_button("📂 Xuất Tất cả (PDF)", data=pdf_all, file_name="Bao_Cao_Lich_Su.pdf")
                with col_csv:
                    csv_all = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📊 Xuất Tất cả (CSV)", csv_all, "full_history.csv")
            else:
                st.caption("🔒 Bạn không có quyền xuất toàn bộ dữ liệu.")
        else:
            if can_export:
                col_down1, col_down2, _ = st.columns([1, 1, 2])
                with col_down1:
                    pdf_all = export_all_posts_to_pdf(df)
                    if pdf_all:
                        st.download_button("📂 Xuất Tất cả dữ liệu (.PDF)", data=pdf_all, file_name="Bao_Cao_Lich_Su.pdf")
                with col_down2:
                    csv_all = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📊 Xuất Tất cả (.CSV)", csv_all, "full_history.csv")
    else:
        st.info("Chưa có lịch sử bài viết.")
        
    st.divider()
    st.subheader("AI Knowledge Export")
    df_knowledge = KnowledgeRepository.get_knowledge_posts(workspace_id=workspace_id)

    if not df_knowledge.empty:
        st.caption("Chọn một nội dung AI Knowledge để export PDF/DOCX, hoặc tải toàn bộ metadata bằng CSV.")
        knowledge_selection = st.dataframe(
            df_knowledge,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="knowledge_export_table"
        )
        knowledge_rows = knowledge_selection.get("selection", {}).get("rows", [])

        if knowledge_rows:
            knowledge_row = df_knowledge.iloc[knowledge_rows[0]]
            st.markdown(f"### AI Knowledge đã chọn: {str(knowledge_row['topic'])[:100]}")
            col_k_pdf, col_k_docx, col_k_csv = st.columns([1, 1, 1])
            with col_k_pdf:
                knowledge_pdf = export_knowledge_to_pdf(knowledge_row)
                if knowledge_pdf:
                    st.download_button(
                        "Tải AI Knowledge PDF",
                        data=knowledge_pdf,
                        file_name=f"AI_Knowledge_{knowledge_row['id']}.pdf",
                        mime="application/pdf"
                    )
            with col_k_docx:
                knowledge_docx = export_knowledge_to_docx(knowledge_row)
                if knowledge_docx:
                    st.download_button(
                        "Tải AI Knowledge DOCX",
                        data=knowledge_docx,
                        file_name=f"AI_Knowledge_{knowledge_row['id']}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            with col_k_csv:
                st.download_button(
                    "Tải metadata CSV",
                    data=export_knowledge_to_csv(df_knowledge),
                    file_name="ai_knowledge_metadata.csv",
                    mime="text/csv"
                )
        else:
            st.download_button(
                "Tải toàn bộ AI Knowledge CSV",
                data=export_knowledge_to_csv(df_knowledge),
                file_name="ai_knowledge_metadata.csv",
                mime="text/csv"
            )
    else:
        st.info("Chưa có nội dung AI Knowledge để export.")
