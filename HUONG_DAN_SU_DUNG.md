# HUONG DAN SU DUNG - APEX AI LOGISTICS GROWTH PLATFORM

> Du an: AI_Agent_Content_AutoPos  
> Ten san pham hien tai: Apex AI Logistics  
> Dinh vi: AI Sales & Marketing Growth Platform cho doanh nghiep Logistics  
> Ngay cap nhat: 22-07-2026  
> Doi tuong su dung: Owner, Admin, CEO, Manager, Marketing/Editor, Viewer  

---

## 1. Tong Quan San Pham

Apex AI Logistics la nen tang ho tro doanh nghiep Logistics lap ke hoach noi dung, tao bai viet, quan ly lead, cham diem co hoi ban hang, tao campaign funnel va tu dong hoa quy trinh marketing tren cac kenh Facebook, LinkedIn va Zalo.

Nen tang phu hop cho cac doanh nghiep cung cap:

- Van chuyen noi dia va last-mile delivery.
- Kho bai va fulfillment.
- Giao nhan B2B/B2C.
- Forwarding, cross-border logistics.
- Dich vu toi uu chi phi logistics.
- Giai phap dashboard, SLA, tracking va automation cho van hanh giao nhan.

Muc tieu cua he thong:

- Tao lich noi dung dai han cho nganh Logistics.
- Bien kien thuc logistics thanh bai dang co tinh tuong tac va tao lead.
- Ho tro doi Sales co pipeline, lead scoring va script follow-up.
- Dong bo Brand Brain, Company Brain, Knowledge Center de AI viet dung nganh, dung dich vu, dung khach hang.
- Dua noi dung tu y tuong den draft, phe duyet, len lich dang va phan tich hieu qua.

---

## 2. Khoi Chay Nhanh

### 2.1 Yeu Cau

- Python 3.9 tro len.
- Trinh duyet Chrome hoac Edge.
- API key Gemini neu muon sinh noi dung bang AI.
- Token Facebook, LinkedIn, Zalo OA neu muon dang bai truc tiep.

### 2.2 Cai Thu Vien

```bash
pip install -r requirements.txt
```

### 2.3 Khoi Tao Database

```bash
python -c "from database.connection import init_db; init_db()"
```

### 2.4 Chay Ung Dung

```bash
streamlit run app/main.py
```

Dia chi mac dinh:

```text
http://localhost:8501
```

---

## 3. Cau Hinh Moi Truong

Tao hoac cap nhat file `.env` tai thu muc goc du an.

```env
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id
ZALO_OA_ACCESS_TOKEN=your_zalo_oa_access_token
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_AUTHOR_URN=urn:li:person:xxxx

DB_ENGINE=sqlite
```

Neu dung PostgreSQL:

```env
DB_ENGINE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=apex_ai_db
DB_USER=postgres
DB_PASSWORD=your_password
```

---

## 4. Dieu Huong Chinh

Sau khi dang nhap, ung dung hien thi cac nhom chuc nang chinh:

```text
Growth Platform
- Logistics Growth Center
- Content Planning (Wizard)

Content Studio Workspace
- Content Studio Workspace
- Knowledge Center
- Company Brain
- Brand Identity
- Thumbnail Studio
- Fact Check
- Publishing Agent

Intelligence
- Learning Loop

Automation Engine
- Workflow Engine
- Quy trinh phe duyet
- A/B Testing

Data & Analytics
- Analytics Agent
- Thumbnail Analytics
- AI Cost Center
- Billing & Quota

System
- System Monitor

Admin
- Quan ly Workspace
- Audit Log
```

Tab mac dinh hien tai la **Logistics Growth Center**.

---

## 5. Quy Trinh Van Hanh Khuyen Nghi Cho Khach Logistics

Day la luong su dung nen ap dung cho mot doanh nghiep Logistics moi bat dau dung he thong.

### Buoc 1: Nap Company Brain Logistics

Vao **Company Brain** va bam **Nap preset doanh nghiep Logistics**.

Preset nay tu dong dien:

- Linh vuc: Logistics / Fulfillment / Supply Chain.
- Mo ta doanh nghiep logistics.
- Dich vu: van chuyen, last-mile, fulfillment, kho bai, tracking, SLA.
- Khach hang muc tieu: CEO, chu shop, Supply Chain Manager, Procurement Manager, Operations Manager.
- Marketing strategy: LinkedIn cho B2B, Facebook cho case study, Zalo cho cham soc khach.
- Sales guideline: pitch, xu ly tu choi, FAQ ve gia, SLA, khu vuc phuc vu, quy trinh xu ly don loi.

### Buoc 2: Nap Brand Preset Logistics

Vao **Brand Identity** va bam **Ap dung Brand Preset Logistics**.

Preset nay them:

- Tu khoa: logistics, fulfillment, van chuyen, kho bai, SLA, last-mile, chuoi cung ung, toi uu chi phi.
- CTA mac dinh: moi khach de lai thong tin de audit chi phi logistics.
- Tone: Chuyen nghiep va tin cay.

### Buoc 3: Lap Ke Hoach Noi Dung 365 Ngay

Vao **Content Planning (Wizard)**.

Chon:

- Nganh nghe: Logistics.
- Chu ky: Lich tuan, lich thang, ke hoach 365 ngay hoac tuy chinh.
- Nen tang: Facebook, LinkedIn, Zalo.
- Doi tuong: CEO Logistics, Supply Chain Manager, Procurement Manager, Operations Manager, E-commerce Owner, Chu shop online.

He thong se tao lich chu de theo cac pillar logistics:

- Chi phi van chuyen.
- SLA giao hang.
- Giao that bai.
- Fulfillment.
- Kho bai.
- Toi uu tuyen.
- Case Study Logistics.
- ROI Logistics.
- Automation Logistics.
- Dashboard van hanh.
- E-commerce Logistics.
- Cross-border.
- Hau truong van hanh.
- Cam ket dich vu.

Co the tai CSV hoac luu mot phan lich thanh draft posts.

### Buoc 4: Tao Noi Dung Trong Content Studio

Vao **Content Studio Workspace**.

Dung tab **AI Create** de tao bai viet cho:

- Facebook.
- LinkedIn.
- Zalo OA.

Cac goi y nhanh Logistics co san:

- Giam chi phi van chuyen cho doanh nghiep thuong mai dien tu.
- Cam ket SLA giao hang va tac dong den ty le mua lai.
- Case study giam ty le giao that bai trong 60 ngay.
- Fulfillment giup chu shop online xu ly don mua cao diem.
- Dashboard realtime cho CEO Logistics.
- So sanh tu van hanh giao hang va thue 3PL.

Goc tiep can logistics co san:

- Toi uu chi phi van chuyen.
- Cam ket SLA giao hang.
- Giam ty le giao that bai.
- Toi uu ton kho va kho bai.
- Case study tiet kiem chi phi logistics.
- So sanh tu van hanh va thue 3PL.
- Quy trinh fulfillment cho thuong mai dien tu.
- Tu dong hoa cham soc khach sau giao hang.
- Dashboard van hanh realtime.
- Rui ro mua cao diem.

### Buoc 5: Quan Ly Lead Va Growth Pipeline

Vao **Logistics Growth Center**.

Dung cac tab:

- Lead Pipeline.
- Lead Scoring.
- Campaign Funnel.
- Sales Scripts.
- Growth Dashboard.

Day la trung tam chuyen app tu content automation thanh sales and marketing growth platform.

### Buoc 6: Phe Duyet Va Dang Bai

Sau khi co draft:

1. Vao **Quy trinh phe duyet** de gui noi dung cho Manager/CEO duyet.
2. Vao **Publishing Agent** de dang thu cong hoac len lich dang.
3. Theo doi ket qua o **Analytics Agent** va **Learning Loop**.

---

## 6. Logistics Growth Center

File chuc nang: `ui/tab_logistics_growth.py`

Day la tab moi quan trong nhat trong phien ban Sales & Marketing Growth.

### 6.1 Lead Pipeline

Dung de quan ly lead logistics o muc nhe, khong can CRM ngoai.

Cac cot chinh:

| Cot | Y nghia |
|---|---|
| company | Ten cong ty/khach hang tiem nang |
| segment | Nhom khach hang logistics |
| contact_role | Vai tro nguoi lien he |
| need | Nhu cau chinh |
| monthly_shipments | San luong don/thang |
| pain_point | Noi dau chinh |
| source_channel | Nguon lead |
| stage | Trang thai pipeline |
| next_follow_up | Ngay can follow-up tiep theo |
| notes | Ghi chu sales |

Pipeline stages:

- New Lead.
- Qualified.
- Needs Analysis.
- Proposal Sent.
- Negotiation.
- Won.
- Lost.

Co the import/export CSV.

### 6.2 Lead Scoring

He thong cham diem lead tu 0 den 100 dua tren:

- San luong don/thang.
- Vai tro nguoi lien he.
- Pain point.
- Stage trong pipeline.

Y nghia diem:

| Diem | Uu tien |
|---|---|
| 0-49 | Low |
| 50-74 | Medium |
| 75-100 | High |

Lead High-score nen duoc sales follow-up truoc.

### 6.3 Next Best Action

Moi lead duoc de xuat hanh dong tiep theo.

Vi du:

- New Lead: gui checklist audit chi phi logistics.
- Qualified: hen discovery call 20 phut.
- Needs Analysis: chuan bi mini proposal.
- Proposal Sent: follow-up bang case study va bang so sanh TCO.
- Negotiation: de xuat pilot 30 ngay voi KPI ro.
- Won: chuyen sang onboarding va len lich tao case study.
- Lost: dua vao nurture 60 ngay.

### 6.4 Campaign Funnel

Dung de tao ke hoach campaign theo segment logistics.

Input:

- Segment.
- Campaign type.
- Pain point.
- So ngay chay campaign.

Campaign types:

- Lead Magnet.
- LinkedIn B2B Thought Leadership.
- Facebook Case Study.
- Zalo Follow-up / CSKH.
- Retargeting Content.
- Proposal Nurture.

Output gom:

- Ngay.
- Kenh.
- Funnel stage.
- Campaign.
- Segment.
- Pain point.
- Chu de.
- CTA.

Co the export CSV hoac luu 5 chu de dau vao Draft Posts.

### 6.5 Sales Scripts

Tao script follow-up theo tung lead va tung kenh:

- LinkedIn.
- Zalo.
- Facebook.

Script tu dong bam theo:

- Cong ty lead.
- Vai tro nguoi lien he.
- Pain point.
- Nhu cau.
- Stage pipeline.

Co the luu script vao Draft Posts de bien thanh noi dung cham soc khach.

### 6.6 Growth Dashboard

Theo doi nhanh:

- Total leads.
- High-score leads.
- Open pipeline.
- Average score.
- Bieu do so lead theo stage.

Operating rhythm khuyen nghi:

- Moi tuan tao 1 campaign funnel theo segment uu tien.
- Moi ngay xu ly lead High-score truoc.
- Moi proposal phai gan KPI: SLA, ty le giao thanh cong, chi phi/don, hoan hang.
- Moi khach Won can tao case study sau 45-60 ngay.

---

## 7. Content Planning (Wizard) Cho Logistics

File chuc nang: `ui/tab_content_planning_wizard.py`

Tab nay da duoc thay UI thanh **Logistics Content & Marketing Planning Engine**.

### 7.1 Thiet Lap Ke Hoach

Nguoi dung chon:

- Chu ky lap lich: tuan, thang, 365 ngay, tuy chinh.
- Ngay bat dau.
- So bai/ngay.
- Nganh nghe.
- Doi tuong muc tieu.
- Nen tang.
- Cach phan phoi.

Neu chon Logistics, he thong dung bo pillar va content mix rieng cho Logistics.

### 7.2 Ty Le Noi Dung Khuyen Nghi

| Nhom noi dung | Ty le |
|---|---:|
| Noi dau van hanh | 25% |
| Kien thuc logistics thuc chien | 25% |
| Case Study doanh nghiep | 20% |
| Giai phap va cong nghe | 15% |
| Xu huong thi truong | 10% |
| Niem tin thuong hieu | 5% |

### 7.3 Lich Noi Dung

Bang lich gom:

- Ngay.
- Tuan.
- Nen tang.
- Nganh.
- Nhom noi dung.
- Pillar.
- Dinh dang.
- Chu de.
- Hook 3 dong dau.
- CTA.
- Trang thai.

Chuc nang:

- Loc theo thang.
- Loc theo nen tang.
- Loc theo nhom noi dung.
- Tai CSV.
- Luu mot so dong thanh Draft Posts.

### 7.4 Chong Lap Y Tuong

He thong theo doi:

- Tong chu de.
- So chu de trung.
- So pillar da dung.
- So dinh dang da dung.

Cong thuc duy tri noi dung dai han:

```text
12+ pillar logistics x nhieu goc khai thac x 5 dinh dang = hang tram den hang nghin bien the noi dung
```

---

## 8. Content Studio Workspace

File chuc nang: `ui/tab_content_studio_workspace.py`

Day la noi tao va bien tap bai viet.

### 8.1 AI Create

Nguoi dung chon:

- Nen tang: Facebook, LinkedIn, Zalo OA.
- Loai bai viet.
- Khach hang muc tieu.
- Goc tiep can.
- Chu de cu the.
- Research Agent neu can.

Doi voi Logistics, he thong da them:

- Logistics target options.
- Logistics angle options.
- Goi y nhanh chu de Logistics.

### 8.2 Copywriting Framework

Dung khi can tao copy ban hang theo framework:

- AIDA.
- PAS.
- BAB.
- Cac framework co san trong `agents/copywriting_prompts.py`.

Phu hop de tao:

- Bai chao dich vu fulfillment.
- Bai quang cao audit chi phi logistics.
- Noi dung proposal nurture.
- Bai tu van SLA va last-mile.

### 8.3 Brand Brain Profile

Cho xem nhanh AI dang dung:

- Ten doanh nghiep.
- Tone of voice.
- CTA mac dinh.

### 8.4 Creative Concepts

Sau khi sinh bai, he thong phan tich noi dung va tao creative concept cho thumbnail.

Phu hop voi:

- Case study logistics.
- Infographic chi phi/don.
- Dashboard SLA.
- Hinh anh kho bai/fulfillment.

---

## 9. Company Brain

File chuc nang: `ui/tab_company_brain.py`

Company Brain la bo nho doanh nghiep. AI se dua vao day de viet dung nganh va dung dich vu.

### 9.1 Logistics Growth Preset

Bam **Nap preset doanh nghiep Logistics** de dien nhanh:

- Industry.
- Description.
- Products.
- Target customers.
- Marketing strategy.
- Sales guideline.

Sau khi nap preset, nen chinh lai theo doanh nghiep that:

- Ten cong ty.
- Website.
- Khu vuc phuc vu.
- Bang gia.
- SLA.
- Dieu kien giao nhan.
- Quy trinh xu ly don loi.

### 9.2 SOP Va Tai Lieu Van Hanh

Nen them vao Knowledge Center cac tai lieu:

- Bang gia logistics.
- SLA.
- Quy trinh tiep nhan don.
- Quy trinh xu ly giao that bai.
- FAQ sales.
- Case study.
- Hop dong mau.
- Brochure dich vu.

---

## 10. Brand Identity

File chuc nang: `ui/tab_brand.py`

Dung de cau hinh giong noi thuong hieu, CTA, keyword va blacklist.

### 10.1 Logistics Brand Preset

Bam **Ap dung Brand Preset Logistics** de them:

- Logistics keywords.
- CTA audit chi phi logistics.
- Tone chuyen nghiep va tin cay.

### 10.2 Goi Y Cau Hinh Brand Cho Logistics

Tone nen dung:

- Chuyen nghiep.
- Dang tin cay.
- Thuc chien.
- Co so lieu.
- Khong noi qua.

Tu nen han che:

- Re nhat.
- Cam ket tuyet doi.
- Bao dam 100%.
- Than toc neu khong co du lieu.
- So 1 thi truong neu khong co bang chung.

---

## 11. Knowledge Center

File chuc nang: `ui/tab_knowledge.py`

Knowledge Center la kho tai lieu de AI truy xuat khi sinh noi dung.

Nguon tai lieu nen nap cho doanh nghiep Logistics:

| Loai tai lieu | Vi du |
|---|---|
| Bang gia | Phi van chuyen, phi luu kho, phi COD |
| SLA | Thoi gian giao, ty le giao dung hen, khu vuc phuc vu |
| Case study | Giam chi phi, tang ty le giao thanh cong, toi uu kho |
| FAQ | Cau hoi ve gia, hop dong, tracking, xu ly don loi |
| SOP | Quy trinh tiep nhan don, doi soat, xu ly hoan hang |
| Sales deck | Tai lieu ban hang, proposal, brochure |
| Bao cao | KPI van hanh, dashboard, du lieu mua cao diem |

AI se dung RAG de tim tai lieu lien quan va dua vao prompt.

---

## 12. Publishing Agent

File chuc nang: `ui/tab_publishing.py`

Dung de dang bai len:

- Facebook.
- LinkedIn.
- Zalo OA.

Chuc nang chinh:

- Xem trang thai cau hinh API.
- Dang thu cong tu kho nhap.
- Len lich dang tu dong.
- Chay lich dang.

Luu y:

- Can cau hinh token dung.
- Nen dua bai qua quy trinh phe duyet truoc khi dang.
- Nen kiem tra lai noi dung lien quan gia, SLA, cam ket dich vu truoc khi publish.

---

## 13. Quy Trinh Phe Duyet

File chuc nang: `ui/tab_approval.py`

Dung de tranh dang sai thong tin logistics.

Quy trinh khuyen nghi:

1. Editor tao draft.
2. Manager kiem tra thong diep, offer, CTA.
3. CEO hoac Owner duyet cac bai co cam ket ve gia, SLA, case study, ROI.
4. Publishing Agent moi dang bai.

Nhung noi dung can duyet ky:

- Bang gia.
- SLA.
- Cam ket giao hang.
- So lieu case study.
- So sanh doi thu.
- Noi dung co tinh phap ly/hop dong.

---

## 14. Analytics, A/B Testing Va Learning Loop

### 14.1 Analytics Agent

Dung de xem hieu qua bai dang:

- Reach.
- Impressions.
- Engagement.
- Top posts.
- Hieu qua theo kenh.

Voi Logistics, nen theo doi them:

- Bai nao tao nhieu inbox.
- Chu de nao tao lead B2B.
- LinkedIn co tao lead CEO/Manager khong.
- Facebook case study co tao comment/tu van khong.
- Zalo co giup cham soc lead va follow-up khong.

### 14.2 A/B Testing

Dung de test:

- Hook ve chi phi vs hook ve SLA.
- Case study vs checklist.
- CTA tai checklist vs CTA dat lich audit.
- Anh kho bai vs infographic KPI.

### 14.3 Learning Loop

He thong hoc tu ket qua cu de cai thien prompt sinh bai tiep theo.

Nen dung Learning Loop sau moi 2-4 tuan chay campaign.

---

## 15. Automation Engine

File chuc nang: `ui/tab_workflow.py`

Dung de mo phong va cau hinh quy trinh tu dong hoa.

Quy trinh Logistics nen tao:

```text
Lead moi
-> Tao sales script
-> Tao bai nurture Zalo
-> Gui phe duyet
-> Len lich follow-up
-> Tao campaign case study
-> Theo doi analytics
```

Luu y: Khong nen auto-publish noi dung co gia, SLA hoac cam ket neu chua duoc duyet.

---

## 16. Phan Quyen

| Vai tro | Quyen khuyen nghi |
|---|---|
| Owner / Super Admin | Quan tri toan bo he thong, workspace, billing, API, audit |
| Admin | Cau hinh Company Brain, Brand, Knowledge, Publishing |
| CEO | Xem dashboard, duyet noi dung quan trong, xem pipeline va analytics |
| Manager | Quan ly lead, duyet bai, xem campaign, dieu phoi editor |
| Marketing / Editor | Tao lich noi dung, tao draft, tao script, gui phe duyet |
| Viewer | Chi xem bao cao, lich noi dung va tai lieu |

---

## 17. Du Lieu Nen Chuan Bi Truoc Khi Ban Cho Khach Logistics

De onboarding khach nhanh, nen yeu cau khach gui:

- Ten cong ty, website, khu vuc phuc vu.
- Danh sach dich vu logistics.
- Bang gia hoac khung gia tham khao.
- SLA hien tai.
- Cac nhom khach hang muc tieu.
- Case study da co.
- FAQ sales.
- Quy trinh xu ly don loi.
- Hinh anh kho, xe, doi van hanh, dashboard.
- File CSV lead neu co.

---

## 18. Playbook 7 Ngay Dau Cho Khach Logistics

### Ngay 1: Setup

- Tao workspace cho khach.
- Nap Logistics Company Preset.
- Nap Logistics Brand Preset.
- Cau hinh API Gemini.
- Nhap tai lieu co ban vao Knowledge Center.

### Ngay 2: Lap ke hoach

- Tao lich noi dung 30 ngay.
- Loc cac chu de uu tien.
- Luu 7 draft dau tien.

### Ngay 3: Tao noi dung

- Sinh 3 bai LinkedIn B2B.
- Sinh 2 bai Facebook case study.
- Sinh 2 noi dung Zalo follow-up.

### Ngay 4: Lead pipeline

- Import lead CSV.
- Chuan hoa stage.
- Chay lead scoring.
- Chon top 10 lead uu tien.

### Ngay 5: Campaign funnel

- Tao campaign Lead Magnet.
- Tao checklist audit chi phi logistics.
- Luu 5 chu de campaign vao draft.

### Ngay 6: Phe duyet va len lich

- Gui bai cho Manager/CEO duyet.
- Len lich dang tuan dau.
- Tao sales script cho top lead.

### Ngay 7: Review

- Xem analytics ban dau.
- Kiem tra inbox/lead moi.
- Dieu chinh hook, CTA, segment.

---

## 19. Changelog Moi Nhat

### V4.0 - Logistics Sales & Marketing Growth Edition (22-07-2026)

- Them **Logistics Growth Center**.
- Them lead pipeline session-based voi import/export CSV.
- Them lead scoring theo san luong don, vai tro, pain point, stage.
- Them next best action cho tung stage sales.
- Them campaign funnel builder cho Logistics.
- Them sales script generator cho LinkedIn, Zalo, Facebook.
- Them Growth Dashboard.
- Doi dinh vi app thanh **AI Sales & Marketing Growth Platform for Logistics**.
- Dat **Logistics Growth Center** lam tab mac dinh.

### V3.9 - Logistics Content & Marketing Automation Edition (22-07-2026)

- Them `config/logistics_vertical.py`.
- Them Logistics content pillars.
- Nang Content Planning thanh Logistics Content & Marketing Planning Engine.
- Them Logistics target va angle trong Content Studio.
- Them Logistics Company Preset.
- Them Logistics Brand Preset.
- Doi header app thanh Apex AI Logistics.

### V3.1 - Studio Edition

- Professional Workspace Editor.
- Version History.
- Load Post.
- Auto-save draft.
- Creative Concept Engine.
- Approval handoff.

### V3 - Intelligence Edition

- Knowledge Center nang cap.
- RAG System.
- Brand Voice Engine.
- Workflow Engine.
- Audit Log.
- Learning Loop.

---

## 20. Cau Truc File Lien Quan

```text
app/main.py
ui/nav_config.py
ui/tab_logistics_growth.py
ui/tab_content_planning_wizard.py
ui/tab_content_studio_workspace.py
ui/tab_company_brain.py
ui/tab_brand.py
ui/tab_publishing.py
ui/tab_approval.py
ui/tab_analytics.py
config/logistics_vertical.py
database/models/posts.py
HUONG_DAN_SU_DUNG.md
```

---

## 21. Ghi Chu Van Hanh

- Nen dung LinkedIn cho B2B Logistics va CEO/Manager.
- Nen dung Facebook cho case study, educational content va lead magnet.
- Nen dung Zalo cho follow-up, CSKH va nhac lich tu van.
- Khong nen tu dong dang noi dung co cam ket gia/SLA neu chua duoc duyet.
- Nen cap nhat Knowledge Center moi khi co bang gia, SLA, case study hoac FAQ moi.
- Nen review Growth Dashboard hang tuan de chon lead uu tien va segment campaign tiep theo.
