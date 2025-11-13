# Website Analyzer
An Intelligent Web Crawler for Comprehensive Site Analysis

This project is a FastAPI-powered web crawler that uses Playwright, BeautifulSoup, and async processing to extract and analyze websites in depth. It provides rich analytics, accessibility evaluations, and AI-driven visualizations — all accessible via Swagger UI endpoints and downloadable reports.

## Features

### Website Crawling & Analysis

* Depth-wise site crawling with asynchronous fetching for speed.

* Extracts and summarizes:

  * Total page count

  * Image count

* Document count (PDF, DOC, etc.)

* WCAG accessibility image stats

* Intelligent link normalization and deduplication to ensure clean data.

## AI & Visualization

Generates Mermaid.js flowcharts and LLM-based homepage diagrams to visualize website structure.

Produces sitemap tables with page hierarchy and metadata.

Categorizes external links into types:

*  E-Commerce

*  Social Media

*  News / Blogs

*  Others

*  Accessibility Insights

*  Evaluates WCAG text and image accessibility across crawled pages.

*  Identifies potential violations and classifies them by WCAG Level A / AA / AAA.

## Data Exports

All analytics are downloadable as:

* CSV tables (Sitemap, External Links, Accessibility Issues)

* Flowcharts & Visuals (Mermaid.js / SVG)

* JSON summaries

* API Endpoints

* Deployed via FastAPI with automatic Swagger UI documentation, including:

  * `/crawl – Crawl a website and get aggregated statistics`

  * `/sitemap – Retrieve sitemap data`

  * `/externals – View and categorize outbound links`

  * `/diagram – Generate homepage flowchart`

## Tech Overview

* Web Crawler	Playwright (headless browser automation)
  
* HTML Parsing	BeautifulSoup4

* Async Engine	asyncio + Playwright concurrent tasks

* Accessibility Engine	Custom WCAG evaluator

* Visualization	Mermaid.js + LLM-generated flow diagrams

* Backend API	FastAPI

* Documentation	Swagger UI

* Proxies & VPN Rotating proxy system via proxies.txt

## Installation

```
git clone https://github.com/yourusername/website-analyzer.git
```
```
cd website-analyzer
```
```
pip install -r requirements.txt
```

#### Then set up your environment variables in .env (example):

```
OPENAI_API_KEY=your_api_key

PROXY_LIST=proxies.txt
```

## Running the App

### Option 1 — Run via FastAPI

``` uvicorn src.main:app --reload```


#### Open the docs at:
```http://127.0.0.1:8000/docs```

### Option 2 — Run via CLI

```python run.py```
