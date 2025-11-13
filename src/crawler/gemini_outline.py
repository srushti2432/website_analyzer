import os
from google.generativeai import configure, GenerativeModel
from dotenv import load_dotenv

load_dotenv()

def generate_sitemap_outline_from_homepage(html_content):
    """
    Generate a clean sitemap outline using only the visible top navbar and dropdown content.
    No technical paths or URLs. Start with website name.
    """
    prompt = f"""
You are a web UX expert.

Below is the homepage HTML of a website.

Your task:
- Read only the **visible top navigation bar** and **its dropdown menus**
- Extract **clear, human-readable section names**
- Ignore all URLs, file paths, or technical references
- Output the sitemap as a **markdown bullet list**
- Start with the **website name** as the first item
- Keep it simple and clean — no code, no explanations

Example:
- Website Name
  - About Us
  - Services
    - Web Design
    - SEO
  - Blog
  - Contact

HTML Content:
{html_content}
"""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env file")

    configure(api_key=api_key)
    model = GenerativeModel("models/gemini-1.5-pro-latest")
    response = model.generate_content(prompt)
    return response.text.strip()

def categorize_external_link(url):
    """
    Categorize an external link based on its content or intent.
    Example categories: Social Media, Blog, Government Site, Documentation, etc.
    """
    prompt = f"""
You are an expert in classifying web links.

Given this external URL, return a short and specific category that describes its type or purpose.

Examples: Blog, Social Media, Government, Documentation, Support, Product, News, Education, Forum, E-commerce, Sports, Navigation, Form Submission, etc.

Do not return the full URL or extra explanation. Just output the **category** as a single line.

URL: {url}
"""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set in the .env file")

    configure(api_key=api_key)
    model = GenerativeModel("models/gemini-1.5-pro-latest")

    try:
        response = model.generate_content(prompt)
        return response.text.strip().splitlines()[0]
    except Exception as e:
        print(f"Error categorizing URL: {e}")
        return "Unknown"
