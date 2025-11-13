import csv
import os
from collections import defaultdict, Counter, deque
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import asyncio

OUTPUT_DIR = "tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BAD_ALT_WORDS = {"image", "photo", "picture", "pic", "logo", "icon", "graphic"}
seen_external_links = set()
seen_external_domains = set()

WAIT_STRATEGIES = ["load", "domcontentloaded", "networkidle"]

def clean_url(url: str) -> str:
    parsed = urlparse(url)
    query = {k: v for k, v in parse_qs(parsed.query).items() if not k.lower().startswith(("utm_", "gclid", "fbclid"))}
    parsed = parsed._replace(query=urlencode(query, doseq=True), fragment="")
    return urlunparse(parsed)

def is_external(url: str, main_domain: str) -> bool:
    try:
        return urlparse(url).netloc and main_domain not in urlparse(url).netloc
    except Exception:
        return False

def extract_links(html: str, base_url: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    return {urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)}

def write_external_link(main_url: str, src_url: str, ext_url: str,
                        filename: str = os.path.join(OUTPUT_DIR, "external_links.csv")) -> None:
    if ext_url in seen_external_links:
        return
    seen_external_links.add(ext_url)
    seen_external_domains.add(urlparse(ext_url).netloc)

    first = not os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Main website URL", "URL where external link was found", "External Link"])
        if first:
            writer.writeheader()
        writer.writerow({
            "Main website URL": main_url,
            "URL where external link was found": src_url,
            "External Link": ext_url,
        })

def write_sitemap_row(writer: csv.DictWriter, url: str, parent_map: dict, max_depth: int) -> None:
    path = []
    while url:
        path.append(url)
        url = parent_map.get(url)
    path.reverse()
    writer.writerow({f"depth {i}": path[i] if i < len(path) else "" for i in range(max_depth + 1)})

def is_descriptive_alt(alt: str | None) -> bool:
    if not alt or not alt.strip():
        return False
    text = alt.strip().lower()
    if text in BAD_ALT_WORDS:
        return False
    if len(text.split()) <= 1 and any(w in text for w in BAD_ALT_WORDS):
        return False
    return True

def is_valid_decorative(img) -> bool:
    return img.get("alt", "").strip() == "" and (
        img.get("role") == "presentation" or img.get("aria-hidden") == "true"
    )

def is_linked_image(img) -> bool:
    return img.find_parent(["a", "button"]) is not None

def is_wcag_compliant(img, seen_alts: Counter) -> bool:
    alt = img.get("alt")
    if alt is None:
        return False
    if is_valid_decorative(img):
        return True
    if is_linked_image(img):
        return is_descriptive_alt(alt)
    if not is_descriptive_alt(alt):
        return False
    if seen_alts[alt.strip().lower()] > 1:
        return False
    return True

# ✅ Sync version wrapped for async use
def fetch_single_page_sync(url, depth, timeout):
    for wait_until in WAIT_STRATEGIES:
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context()
                context.route("**/*", lambda route, request: route.abort() if request.resource_type in {"image", "stylesheet", "font", "media"} else route.continue_())
                page = context.new_page()
                page.goto(url, timeout=timeout, wait_until=wait_until)
                page.wait_for_timeout(1000)
                html = page.content()
                js_links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
                page.close()
                context.close()
                browser.close()
                return url, depth, html, set(js_links)
        except Exception as e:
            print(f"⚠️ Failed with wait_until='{wait_until}' for {url}: {e}")
    return url, depth, "", set()

# ✅ Async wrapper using asyncio.to_thread
async def fetch_single_page(url, depth, timeout):
    return await asyncio.to_thread(fetch_single_page_sync, url, depth, timeout)

async def crawl_main_site(main_url: str, generate_links: bool = True,
                          max_depth: int = 3, use_proxy: bool = True,
                          concurrency: int = os.cpu_count(), timeout: int = 60000):

    start_url = clean_url(main_url)
    visited = set()
    queue = deque([(start_url, 0)])
    page_counts = defaultdict(int)
    stats = {"attachments": 0, "images": 0, "accessible_images": 0}
    parent_map = {start_url: None}
    homepage_html = ""

    sitemap_path = os.path.join(OUTPUT_DIR, "sitemap.csv")
    sitemap_file = open(sitemap_path, "w", newline="", encoding="utf-8") if generate_links else None
    sitemap_writer = csv.DictWriter(sitemap_file, fieldnames=[f"depth {i}" for i in range(max_depth + 1)]) if sitemap_file else None
    if sitemap_writer:
        sitemap_writer.writeheader()

    sem = asyncio.Semaphore(concurrency)

    async def crawl_page(url, depth):
        async with sem:
            return await fetch_single_page(url, depth, timeout)

    while queue:
        batch = []
        while queue and len(batch) < concurrency:
            url, depth = queue.popleft()
            if url not in visited and depth <= max_depth:
                batch.append((url, depth))

        tasks = [crawl_page(url, depth) for url, depth in batch]
        results = await asyncio.gather(*tasks)

        for url, depth, html, js_links in results:
            if not html or url in visited:
                continue
            visited.add(url)

            print(f"[{len(visited)}] Crawled (depth {depth}): {url}")
            if depth == 0:
                homepage_html = html
            page_counts[str(depth)] += 1

            soup = BeautifulSoup(html, "html.parser")
            stats["attachments"] += sum(
                1 for a in soup.find_all("a", href=True)
                if a["href"].lower().endswith((".pdf", ".docx", ".pptx", ".xlsx", ".zip"))
            )
            imgs = soup.find_all("img")
            stats["images"] += len(imgs)
            seen_alts = Counter(img.get("alt", "").strip().lower() for img in imgs if img.has_attr("alt"))
            stats["accessible_images"] += sum(is_wcag_compliant(img, seen_alts) for img in imgs)

            domain = urlparse(main_url).netloc
            links = extract_links(html, url) | js_links

            if sitemap_writer and generate_links:
                write_sitemap_row(sitemap_writer, url, parent_map, max_depth)

            for link in links:
                cleaned = clean_url(link)
                if urlparse(cleaned).scheme not in ("http", "https"):
                    continue
                if is_external(cleaned, domain):
                    write_external_link(main_url, url, cleaned)
                elif cleaned not in visited and cleaned not in parent_map:
                    parent_map[cleaned] = url
                    queue.append((cleaned, depth + 1))

    if sitemap_file:
        sitemap_file.close()

    print(f"\n✅ Crawl completed. Pages visited: {len(visited)}")
    print(f"📦 Attachments: {stats['attachments']}, 🖼️ Images: {stats['images']}, ♿ Accessible Images: {stats['accessible_images']}")
    return page_counts, stats, homepage_html

async def crawl_selected_external(ext_url: str, max_depth: int = 2, timeout: int = 60000):
    start_url = clean_url(ext_url)
    visited = set()
    queue = deque([(start_url, 0)])
    page_counts = defaultdict(int)
    stats = {"attachments": 0, "images": 0, "accessible_images": 0}

    while queue:
        url, depth = queue.popleft()
        if depth > max_depth or url in visited:
            continue
        visited.add(url)

        print(f"[Depth {depth}] Crawled: {url}")
        _, _, html, js_links = await fetch_single_page(url, depth, timeout)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        page_counts[str(depth)] += 1

        stats["attachments"] += sum(
            1 for a in soup.find_all("a", href=True)
            if a["href"].lower().endswith((".pdf", ".docx", ".pptx", ".xlsx", ".zip"))
        )

        imgs = soup.find_all("img")
        stats["images"] += len(imgs)
        seen_alts = Counter(img.get("alt", "").strip().lower() for img in imgs if img.has_attr("alt"))
        stats["accessible_images"] += sum(is_wcag_compliant(img, seen_alts) for img in imgs)

        domain = urlparse(start_url).netloc
        links = extract_links(html, url) | js_links
        for link in links:
            cleaned = clean_url(link)
            if urlparse(cleaned).scheme not in ("http", "https"):
                continue
            if domain in urlparse(cleaned).netloc and cleaned not in visited:
                queue.append((cleaned, depth + 1))

    return {
        "page_counts": dict(page_counts),
        "site_stats": stats,
        "summary": f"Crawled {len(visited)} pages from {ext_url}"
    }

async def run_full_crawl(url: str, max_depth: int = 3, use_proxy: bool = True,
                         generate_links: bool = True, concurrency: int = os.cpu_count(),
                         timeout: int = 60000):
    return await crawl_main_site(
        url, generate_links=generate_links,
        max_depth=max_depth, use_proxy=use_proxy,
        concurrency=concurrency, timeout=timeout
    )
