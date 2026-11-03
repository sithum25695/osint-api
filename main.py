from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import asyncio
import hashlib

app = FastAPI()

# InfinityFree එකෙන් එන requests භාර ගැනීමට CORS enable කිරීම
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

USERNAME_SITES = {
    "GitHub": "https://github.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "GitLab": "https://gitlab.com/{}"
}

async def fetch_status(session, name, url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(url, headers=headers, timeout=6) as res:
            if res.status == 200:
                return {"site": name, "found": True, "url": url}
    except Exception:
        pass
    return {"site": name, "found": False, "url": None}

@app.get("/api/search/username")
async def check_username(q: str):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_status(session, site, tmpl.format(q))
            for site, tmpl in USERNAME_SITES.items()
        ]
        results = await asyncio.gather(*tasks)
    return {"query": q, "matches": [r for r in results if r["found"]]}

@app.get("/api/search/email")
async def check_email(q: str):
    # Email එකේ MD5 hash එක මඟින් Gravatar සහ ආශ්‍රිත profiles සෙවීම
    clean_email = q.strip().lower()
    email_hash = hashlib.md5(clean_email.encode()).hexdigest()
    
    email_targets = {
        "Gravatar Profile": f"https://en.gravatar.com/{email_hash}.json",
        "GitHub Events": f"https://api.github.com/search/users?q={clean_email}+in:email"
    }
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_status(session, site, url)
            for site, url in email_targets.items()
        ]
        results = await asyncio.gather(*tasks)
    return {"query": q, "matches": [r for r in results if r["found"]]}
