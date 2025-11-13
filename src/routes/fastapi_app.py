import os
import sys
import shutil
import subprocess
import traceback
import webbrowser

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from src.crawler.test import run_full_crawl, crawl_selected_external
from src.crawler.diagram_generator import outline_to_mermaid, extract_level1_outlines
from src.crawler.gemini_outline import generate_sitemap_outline_from_homepage, categorize_external_link

if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

router = APIRouter()

OUTPUT_DIR = "tmp"
DIAGRAM_DIR = os.path.join(OUTPUT_DIR, "diagrams")
os.makedirs(DIAGRAM_DIR, exist_ok=True)


class CrawlRequest(BaseModel):
    url: str
    max_depth: int = Field(3, ge=1, le=5)
    use_proxy: bool = True
    generate_links: bool = True
    concurrency: Optional[int] = None
    timeout: Optional[int] = None


class ExternalCrawlRequest(BaseModel):
    external_url: str


def render_mermaid_to_svg(mmd_code: str, svg_path: str):
    import shutil
    mmd_path = svg_path.replace(".svg", ".mmd")
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(mmd_code)

    mmdc_path = shutil.which("mmdc")
    if not mmdc_path:
        raise RuntimeError(
            "Mermaid CLI (mmdc) not found. Please install it using:\n"
            "npm install -g @mermaid-js/mermaid-cli"
        )

    try:
        subprocess.run([mmdc_path, "-i", mmd_path, "-o", svg_path], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Mermaid CLI rendering failed: {e}")
    finally:
        if os.path.exists(mmd_path):
            os.remove(mmd_path)


@router.on_event("startup")
def open_docs():
    webbrowser.open_new_tab("http://127.0.0.1:8000/docs")


@router.post("/")
async def crawl_website(req: CrawlRequest):
    try:
        sitemap_file = os.path.join(OUTPUT_DIR, "sitemap.csv")
        homepage_file = os.path.join(OUTPUT_DIR, "homepage.html")
        external_file = os.path.join(OUTPUT_DIR, "external_links.csv")

        # Clear previous outputs
        for p in (sitemap_file, homepage_file, external_file):
            if os.path.exists(p):
                os.remove(p)
        if os.path.exists(DIAGRAM_DIR):
            shutil.rmtree(DIAGRAM_DIR)
        os.makedirs(DIAGRAM_DIR, exist_ok=True)

        # Run crawler
        page_counts, site_stats, homepage_html = await run_full_crawl(
            url=req.url,
            max_depth=req.max_depth,
            use_proxy=req.use_proxy,
            generate_links=req.generate_links,
            concurrency=req.concurrency or os.cpu_count(),
            timeout=req.timeout or 90000,
        )

        # Save homepage
        with open(homepage_file, "w", encoding="utf-8") as f:
            f.write(homepage_html)

        # Generate Mermaid diagram
        outline_text = generate_sitemap_outline_from_homepage(homepage_html)
        mermaid = outline_to_mermaid(outline_text)
        homepage_svg = os.path.join(DIAGRAM_DIR, "homepage.svg")
        render_mermaid_to_svg(mermaid, homepage_svg)

        # Generate section-wise diagrams
        level_sections = extract_level1_outlines(outline_text)
        for section, lines in level_sections.items():
            code = outline_to_mermaid("\n".join(lines))
            fpath = os.path.join(DIAGRAM_DIR, f"{section.replace(' ', '_').lower()}.svg")
            render_mermaid_to_svg(code, fpath)

        # Categorize external links
        if os.path.exists(external_file):
            lines = open(external_file, encoding="utf-8").read().splitlines()
            header, *rows = lines
            categorized = [header + ",Category"]
            for row in rows:
                ext = row.split(",")[-1]
                cat = categorize_external_link(ext)
                categorized.append(row + "," + cat)
            open(external_file, "w", encoding="utf-8").write("\n".join(categorized))

        return {
            "main_url": req.url,
            "page_counts": dict(page_counts),
            "site_stats": site_stats,
            "homepage_outline": outline_text,
            "homepage_mermaid_diagram": homepage_svg,
            "level_diagrams": [os.path.join(DIAGRAM_DIR, f) for f in os.listdir(DIAGRAM_DIR)],
            "sitemap_download": "/crawl/download/sitemap",
            "external_links_download": "/crawl/download/external",
            "diagram_download": "/crawl/download/diagrams"
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/external")
async def crawl_external(req: ExternalCrawlRequest):
    try:
        res = await crawl_selected_external(req.external_url)
        return {
            "external_url": req.external_url,
            "page_counts": res.get("page_counts", {}),
            "site_stats": res.get("site_stats", {}),
            "summary": res.get("summary", "")
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawl/download/sitemap")
def dl_sitemap():
    return _serve(os.path.join(OUTPUT_DIR, "sitemap.csv"), "sitemap.csv")


@router.get("/crawl/download/external")
def dl_external():
    return _serve(os.path.join(OUTPUT_DIR, "external_links.csv"), "external_links.csv")


@router.get("/crawl/download/diagrams")
def dl_diagrams():
    zip_path = os.path.join(OUTPUT_DIR, "diagrams.zip")

    if not os.path.exists(DIAGRAM_DIR):
        raise HTTPException(status_code=404, detail="Diagrams folder not found")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    shutil.make_archive(zip_path.replace(".zip", ""), 'zip', DIAGRAM_DIR)
    return FileResponse(zip_path, media_type='application/zip', filename="diagrams.zip")


def _serve(path, name):
    if os.path.exists(path):
        return FileResponse(path, filename=name)
    raise HTTPException(status_code=404, detail=f"{name} not found")
