# Deploy Streamlit Community Cloud + Neon Free Postgres

Ung dung nay la Streamlit app, entrypoint la `app/main.py`. Phuong an free khuyen nghi: chay app tren Streamlit Community Cloud va luu database tren Neon Free Postgres.

## 1. Chuan bi GitHub repo

1. Tao GitHub repo moi.
2. Dua code len repo.
3. Khong dua cac file nay len GitHub: `.env`, `.streamlit/secrets.toml`, `content_manager.db`, `*.log`, `uploads/`.

## 2. Tao Neon Free Postgres

1. Vao Neon va tao project moi.
2. Copy connection string dang PostgreSQL.
3. Dung connection string co SSL, vi du:

```text
postgresql://USER:PASSWORD@HOST/DB?sslmode=require
```

## 3. Deploy tren Streamlit Community Cloud

1. Vao Streamlit Community Cloud.
2. Chon **Create app** va ket noi GitHub repo.
3. Main file path: `app/main.py`.
4. Python version: 3.11 neu Streamlit cho chon.
5. Mo **App settings > Secrets** va dan noi dung theo mau trong `.streamlit/secrets.example.toml`.

Secrets toi thieu:

```toml
DB_ENGINE = "postgresql"
PG_DSN = "postgresql://USER:PASSWORD@HOST/DB?sslmode=require"
SECRET_KEY = "replace-with-a-long-random-secret"
JWT_EXPIRE_HOURS = "24"
GEMINI_API_KEY = "your-gemini-key"
```

## 4. Sau khi app chay

- Truy cap URL Streamlit cap.
- Tao tai khoan admin dau tien tu man hinh dang ky.
- Tao tai khoan demo rieng de gui cho khach.
- Neu can demo tinh nang dang bai, hay them token Facebook/Zalo/LinkedIn trong Secrets.

## Gioi han free can biet

- Streamlit Community Cloud phu hop demo app Streamlit, nhung tai nguyen CPU/RAM co gioi han.
- Neon Free co dung luong mien phi gioi han va compute tu sleep khi khong dung, nhung thuc day nhanh hon web service ngu.
- Khong dung cho production hoac du lieu khach hang quan trong neu chua co backup va goi tra phi.

## Chay thu local voi Neon

Tao file `.env` local:

```env
DB_ENGINE=postgresql
PG_DSN=postgresql://USER:PASSWORD@HOST/DB?sslmode=require
SECRET_KEY=local-dev-secret
GEMINI_API_KEY=your-gemini-key
```

Sau do chay:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app/main.py
```
