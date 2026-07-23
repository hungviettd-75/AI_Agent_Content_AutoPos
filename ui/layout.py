import streamlit as st
from ui.sidebar import render_sidebar
from ui.header import render_header
from ui.footer import render_footer
from ui.breadcrumb import render_breadcrumb
from ui.design_system import DesignSystem

class LayoutManager:
    """
    LayoutManager - Điều phối cấu trúc hiển thị toàn bộ trang bao gồm:
    - Tiêm CSS chuẩn của Design System
    - Thiết lập Responsive Sidebar (kèm trạng thái Expand/Collapse)
    - Vẽ Header (kèm breadcrumbs, notifications, search)
    - Bao bọc Main Content
    - Render Footer chân trang
    """
    
    @staticmethod
    def render_app_layout(
        current_user: dict,
        workspaces: list,
        active_workspace_id: int,
        nav_groups: dict,
        active_nav: str
    ) -> tuple:
        """
        Khởi tạo layout mẫu cho ứng dụng và tiêm CSS.
        """
        # 1. Tiêm styles từ Design System
        DesignSystem.inject_styles()
        
        # 2. Quản lý trạng thái Collapse của Sidebar
        if 'sidebar_collapsed' not in st.session_state:
            st.session_state['sidebar_collapsed'] = False
            
        # 3. Vẽ Sidebar
        new_nav, rerun, toggle = render_sidebar(
            current_user=current_user,
            workspaces=workspaces,
            active_workspace_id=active_workspace_id,
            nav_groups=nav_groups,
            active_nav=active_nav,
            collapsed=st.session_state['sidebar_collapsed']
        )
        
        if toggle:
            st.session_state['sidebar_collapsed'] = not st.session_state['sidebar_collapsed']
            st.rerun()
            
        # 4. Tìm kiếm Workspace đang active để đưa vào Header
        active_ws_name = "Default Workspace"
        for w in workspaces:
            if w["id"] == active_workspace_id:
                active_ws_name = w["name"]
                break
                
        # 5. Vẽ Header & Breadcrumbs
        render_header(
            active_workspace_name=active_ws_name,
            active_page_name=active_nav,
            notifications_count=3  # Mock notification count
        )
        
        # Trả về trang điều hướng mới được chọn
        return new_nav, rerun
