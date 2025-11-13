import sys
import asyncio
import uvicorn

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
print("✅ run.py using:", asyncio.get_event_loop_policy())

if __name__ == "__main__":
    # point to the FastAPI instance inside src/main.py
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
