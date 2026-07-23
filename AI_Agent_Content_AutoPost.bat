@echo off
title AI-Agent Marketing - Streamlit App
color 0b

:: 1. Chuyển hướng đến thư mục làm việc
cd /d "E:\Save APP\AI_Agent_Content_AutoPos"

:: 2. Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Python chua duoc cai dat hoac chua add vao PATH!
    pause
    exit
)

:: 3. Kiểm tra file .env
if not exist ".env" (
    echo [CANH BAO] File .env khong tim thay. Ung dung co the thieu cau hinh API.
)

:: 4. Thông báo chế độ database (đọc từ .env)
echo.
echo ============================================================
echo   AI-Agent Marketing - Khoi dong ung dung
echo   Config: Xem file .env de thay doi cau hinh
echo ============================================================
echo.

:: 5. Chạy ứng dụng Streamlit (config trong .env)
echo Dang khoi dong Streamlit...
python -m streamlit run "app/main.py"

:: 6. Giữ cửa sổ nếu có lỗi xảy ra
pause