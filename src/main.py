"""
FastAPI entry‑point – mounts crawl router.
Only change: import path is now `.routes.fastapi_app`.
"""

import os
import sys
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ Windows-specific asyncio fix must be set **before any async code runs**
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# absolute‑within‑package import ✔
from src.routes.fastapi_app import router as crawl_router

# optional file logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/crawler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = FastAPI(title="Website Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crawl_router, prefix="/crawl")

logging.info("🚀 API started")
