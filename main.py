import os
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
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


API_KEY_NAME = "access_token"
API_KEY = "999coresapikey" 

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=403,
        detail="Could not validate credentials. Invalid or missing API Key."
    )

class StreamRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Welcome to Custom YouTube Streaming API!",
        "endpoints": {
            "stream": "/api/v1/stream (POST)"
        }
    }

@app.post("/api/v1/stream")
async def get_stream_url(data: StreamRequest, api_key: str = Depends(get_api_key)):
    youtube_url = data.url
    
    if not youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL is required.")

    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            stream_url = info.get('url')
            title = info.get('title')
            duration = info.get('duration')
            thumbnail = info.get('thumbnail')

        
        try:
            supabase.table("api_stats").insert({
                "video_title": title,
                "video_url": youtube_url
            }).execute()
        except Exception as db_error:
            print(f"Database logging error: {db_error}")

        return {
            "success": True,
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "stream_url": stream_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stream: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
