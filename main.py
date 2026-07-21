import os
import time
import asyncio
from fastapi import FastAPI, HTTPException, Security, Header, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI(title="Pro Music & Video Downloader API")

# API Key ကို Environment Variable ကနေ ယူပါမည်
API_KEY = os.getenv("API_KEY", "your_secret_api_key_here")

# ဒေါင်းလုဒ်လုပ်မည့် ဖိုင်တွဲ ဖန်တီးခြင်း
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ဒေါင်းထားတဲ့ ဖိုင်တွေကို URL အနေနဲ့ လှမ်းယူလို့ရအောင် Static File အဖြစ် သတ်မှတ်ခြင်း
app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

# --- ၇ ရက်တစ်ခါ ဖိုင်ဟောင်းများ ရှင်းလင်းသည့် စနစ် (Auto Cleanup) ---
async def cleanup_old_files():
    while True:
        now = time.time()
        # 7 Days in seconds = 7 * 24 * 60 * 60 = 604800
        for filename in os.listdir(DOWNLOAD_DIR):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(filepath):
                if now - os.path.getmtime(filepath) > 604800:
                    try:
                        os.remove(filepath)
                        print(f"🗑️ ၇ ရက်ကျော်သွား၍ ဖျက်လိုက်သော ဖိုင်: {filename}")
                    except Exception as e:
                        print(f"Error deleting file: {e}")
        
        # ၁ ရက် (၂၄ နာရီ) ပြည့်တိုင်း တစ်ခါ ပြန်စစ်ပါမည် (86400 seconds)
        await asyncio.sleep(86400)

@app.on_event("startup")
async def startup_event():
    # Server စပွင့်တာနဲ့ File ရှင်းတဲ့စနစ်ကို နောက်ကွယ်မှာ အလုပ်လုပ်ခိုင်းထားမည်
    asyncio.create_task(cleanup_old_files())

# --- API Key စစ်ဆေးခြင်း ---
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="❌ မှားယွင်းသော API Key ဖြစ်ပါသည်။ Access Denied.")
    return x_api_key

# --- ပင်မ Download API ---
@app.get("/api/download")
def download_media(url: str, type: str = "audio", req_url: str = Security(verify_api_key)):
    """
    type နေရာတွင် 'audio' သို့မဟုတ် 'video' ဟု ထည့်သွင်းနိုင်ပါသည်။
    """
    try:
        # 1. ပထမဆုံး Video ID ကို အရင်ယူပါမည် (ဖိုင်ရှိ/မရှိ စစ်ဆေးရန်)
        # cookies.txt ရှိရင် ထည့်သုံးမည်
        cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None
        
        extract_opts = {'quiet': True, 'cookiefile': cookie_file}
        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            video_title = info.get('title', 'Unknown Title')

        # 2. File အမျိုးအစားပေါ်မူတည်ပြီး နာမည်သတ်မှတ်ခြင်း
        ext = "mp3" if type == "audio" else "mp4"
        filename = f"{video_id}.{ext}"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        # 3. ⚡ ကက်ရှ် (Cache) စနစ် - ဖိုင်ရှိပြီးသားဆိုရင် ထပ်မဒေါင်းတော့ဘဲ ချက်ချင်းပို့ပေးမည်
        if os.path.exists(filepath):
            return JSONResponse({
                "status": "success",
                "message": "⚡ Cached file retrieved immediately!",
                "title": video_title,
                "file_url": f"/files/{filename}"
            })

        # 4. ဖိုင်မရှိသေးရင် yt-dlp ဖြင့် အသစ်ဒေါင်းလုဒ်လုပ်မည်
        if type == "audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
                'cookiefile': cookie_file,
            }
        else: # video
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
                'cookiefile': cookie_file,
                'max_filesize': 200 * 1024 * 1024, # 200MB ထက်ကြီးရင် မဒေါင်းရန်
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return JSONResponse({
            "status": "success",
            "message": "✅ ဒေါင်းလုဒ်လုပ်ပြီးပါပြီ",
            "title": video_title,
            "file_url": f"/files/{filename}"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
