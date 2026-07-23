import streamlit as st
import pandas as pd
import time
from services.monitoring_service import MonitoringService

_MON_CSS = """
<style>
.mon-header {
    background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
    border-radius: 16px;
    padding: 1.8rem;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    border: 1px solid rgba(255,255,255,0.05);
}
.mon-header h2 { color: white !important; margin: 0 0 0.4rem 0; font-weight: 800; font-size: 1.6rem; }
.mon-header p { color: rgba(255,255,255,0.7); margin: 0; font-size: 0.9rem; }

/* Status Indicators */
.mon-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.mon-card {
    flex: 1;
    min-width: 180px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
}
.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 6px;
}
.st-green  { background-color: #10b981; box-shadow: 0 0 8px #10b981; }
.st-yellow { background-color: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
.st-red    { background-color: #ef4444; box-shadow: 0 0 8px #ef4444; }

.m-val  { font-size: 1.8rem; font-weight: 800; color: #0f172a; margin-top: 0.3rem; }
.m-lbl  { font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }

/* Alert Box */
.alert-box {
    border-radius: 12px;
    padding: 1rem 1.3rem;
    margin-bottom: 1rem;
    border: 1px solid #fecaca;
    background-color: #fef2f2;
    color: #991b1b;
}
.alert-title { font-weight: 700; font-size: 0.9rem; display: flex; align-items: center; gap: 8px; }
.alert-desc { font-size: 0.82rem; margin-top: 0.3rem; line-height: 1.5; }
</style>
"""

def render_tab_monitoring(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_MON_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="mon-header">
        <h2>🖥️ System Monitor & Health Check</h2>
        <p>Báo cáo sức khỏe máy chủ ứng dụng · Độ trễ API ngoại vi · Giám sát hiệu năng phần cứng</p>
    </div>
    """, unsafe_allow_html=True)

    # Nút quét lại
    col_scan, _ = st.columns([1, 4])
    with col_scan:
        btn_refresh = st.button("🔄 Quét lại hệ thống", use_container_width=True, type="primary")

    # Thu thập dữ liệu đo đạc
    with st.spinner("Đang thực hiện đo đạc hệ thống..."):
        db_health = MonitoringService.check_db_health()
        sys_metrics = MonitoringService.check_system_metrics()
        api_health = MonitoringService.check_external_apis(gemini_key)
        alerts = MonitoringService.get_active_alerts(sys_metrics, db_health, api_health)

    # ── PHẦN 1: ACTIVE ALERTS (CẢNH BÁO NÓNG) ──
    if alerts:
        st.subheader("⚠️ Cảnh Báo Hệ Thống Kịp Thời")
        for alert in alerts:
            level_icon = "🚨 CRITICAL:" if alert["level"] == "critical" else "⚠️ WARNING:"
            st.markdown(f"""
            <div class="alert-box">
                <div class="alert-title">{level_icon} {alert['source']}</div>
                <div class="alert-desc">{alert['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        st.write("")
    else:
        st.success("✅ Toàn bộ hệ thống hoạt động ổn định — Không phát hiện cảnh báo nguy hại nào.")

    # ── PHẦN 2: HEALTH STATUS CARDS ──
    st.subheader("🩺 Tình trạng hoạt động")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. DB Status
    db_st_cls = "st-green" if db_health["status"] == "healthy" else "st-red"
    with col1:
        st.markdown(f"""
        <div class="mon-card">
            <div class="m-lbl"><span class="status-indicator {db_st_cls}"></span>Trạng thái DB</div>
            <div class="m-val">{db_health['latency_ms']:.1f} <span style="font-size: 1rem; color: #64748b;">ms</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 2. CPU
    cpu_pct = sys_metrics["cpu_usage_pct"]
    cpu_st = "st-green" if cpu_pct < 70 else "st-yellow" if cpu_pct < 90 else "st-red"
    with col2:
        st.markdown(f"""
        <div class="mon-card">
            <div class="m-lbl"><span class="status-indicator {cpu_st}"></span>Sử Dụng CPU</div>
            <div class="m-val">{cpu_pct:.1f} <span style="font-size: 1rem; color: #64748b;">%</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 3. RAM
    ram_pct = sys_metrics["ram"]["percent"]
    ram_st = "st-green" if ram_pct < 70 else "st-yellow" if ram_pct < 90 else "st-red"
    with col3:
        st.markdown(f"""
        <div class="mon-card">
            <div class="m-lbl"><span class="status-indicator {ram_st}"></span>Sử Dụng RAM</div>
            <div class="m-val">{ram_pct:.1f} <span style="font-size: 1rem; color: #64748b;">%</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 4. Disk Space
    disk_pct = sys_metrics["disk"]["percent"]
    disk_st = "st-green" if disk_pct < 70 else "st-yellow" if disk_pct < 90 else "st-red"
    with col4:
        st.markdown(f"""
        <div class="mon-card">
            <div class="m-lbl"><span class="status-indicator {disk_st}"></span>Sử Dụng Ổ Đĩa</div>
            <div class="m-val">{disk_pct:.1f} <span style="font-size: 1rem; color: #64748b;">%</span></div>
        </div>
        """, unsafe_allow_html=True)

    # ── PHẦN 3: CHI TIẾT PHẦN CỨNG & API ──
    st.markdown("---")
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown("##### ⚙️ Thông số phần cứng chi tiết")
        ram_m = sys_metrics["ram"]
        disk_m = sys_metrics["disk"]
        
        hardware_info = {
            "Thông số": ["Hệ điều hành", "Dung lượng RAM", "RAM đã sử dụng", "RAM còn trống", "Dung lượng đĩa tổng", "Đĩa đã sử dụng", "Đĩa còn trống"],
            "Giá trị": [
                sys_metrics["os"],
                f"{ram_m['total_gb']} GB", f"{ram_m['used_gb']} GB ({ram_m['percent']}%)", f"{ram_m['free_gb']} GB",
                f"{disk_m['total_gb']} GB", f"{disk_m['used_gb']} GB ({disk_m['percent']}%)", f"{disk_m['free_gb']} GB"
            ]
        }
        st.dataframe(pd.DataFrame(hardware_info), use_container_width=True, hide_index=True)

    with col_d2:
        st.markdown("##### 🌐 Kết nối các API ngoài (Integrations)")
        api_data = []
        for name, info in api_health.items():
            latency_str = f"{info['latency_ms']} ms" if "latency_ms" in info else "N/A"
            status_text = "🟢 Sẵn sàng" if info["status"] == "healthy" else "🟡 Chưa cấu hình" if info["status"] == "unconfigured" else "🔴 Bị ngắt kết nối"
            api_data.append({
                "Tên dịch vụ API": name,
                "Trạng thái": status_text,
                "Độ trễ": latency_str,
                "Thông điệp": info["message"]
            })
        st.dataframe(pd.DataFrame(api_data), use_container_width=True, hide_index=True)
