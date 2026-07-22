import os
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.responses import FileResponse
import yt_dlp
from supabase import create_client, Client

app = FastAPI(
    title="999Cores Music & Video Streaming API",
    description="Custom YouTube Audio/Video Streaming API with Supabase Stats & API Key Authentication.",
    version="1.0.0"
)

SUPABASE_URL = "https://iikjhawlpfsenuizxwke.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlpa2poYXdscGZzZW51aXp4d2tlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ3MjY4NDUsImV4cCI6MjEwMDMwMjg0NX0.YfRG36NJeeAgEqWcpVBnAWF9DExTyM_5tfEtJc_AENs"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

API_KEY = "999coresapikey" 
DOWNLOAD_DIR = "downloads"

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Welcome to Custom YouTube Streaming API!",
        "endpoints": {
            "download": "/download (GET)"
        }
    }

@app.get("/download")
async def download_media(url: str, type: str = "audio", api_key: str = None):
    # API Key စစ်ဆေးခြင်း
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL or Video ID is required.")

    if not url.startswith("http"):
        youtube_url = f"https://www.youtube.com/watch?v={url}"
    else:
        youtube_url = url

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ext = "mp3" if type == "audio" else "mp4"
    file_path = os.path.join(DOWNLOAD_DIR, f"{url}.{ext}")

    # ဖိုင်ရှိပြီးသားဆိုရင် တိုက်ရိုက်ပြန်ပေးရန်
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return FileResponse(file_path, media_type="audio/mpeg" if type == "audio" else "video/mp4")

    ydl_opts = {
        'format': 'bestaudio/best' if type == 'audio' else 'bestvideo+bestaudio/best',
        'outtmpl': file_path.rsplit('.', 1)[0],
        'noplaylist': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title')

        # Supabase ထဲသို့ Stats မှတ်တမ်းတင်ခြင်း
        try:
            supabase.table("api_stats").insert({
                "video_title": title,
                "video_url": youtube_url
            }).execute()
        except Exception as db_error:
            print(f"Database logging error: {db_error}")

        # ဖိုင်အစစ်ကို Bot ဆီသို့ ပြန်ပို့ပေးခြင်း
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="audio/mpeg" if type == "audio" else "video/mp4")
        
        raise HTTPException(status_code=500, detail="File download failed.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stream: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
