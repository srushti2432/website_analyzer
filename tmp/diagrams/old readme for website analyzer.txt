🌐 Website Analyzer - Backend

Website Analyzer is a backend service designed to **crawl websites**, analyze their structure, and generate insights and downloadable reports.

This FastAPI-powered crawler:
- Traverses a website up to a specified depth
- Extracts and categorizes **internal pages**, **external links**
- Provides **WCAG-compliant image** analysis
- Outputs **sitemap**, **external links**, and **homepage HTML**
- Returns a **summary report** including:

✅ Page count (depth-wise)  
✅ Total image count  
✅ Attachment file count  
✅ Number of WCAG-compliant images  

---

## 🚀 What’s Inside?

- Python backend
- FastAPI-based API
- Playwright-based async web crawler
- WCAG accessibility checks
- Proxy support
- CSV + HTML exports (sitemap, external links, homepage)
- Swagger/OpenAPI documentation
- Modular architecture (prod-ready)

---

## 🛠️ Setup Instructions

### ✅ Prerequisites

- Python 3.11

---

### 📦 venv creation 

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies


pip install -r requirements.txt
python -m playwright install chromium

▶️ Running the App

python run.py

📬 Who to Contact
 Srushti M
📧 srushtimahesh2003@gmail.com

For backend related issues,  — reach out anytime.

⚙️ .env Format

GOOGLE_API_KEY=your_api_key