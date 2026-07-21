FROM python:3.11-slim

# System ထဲမှာ ffmpeg နဲ့ လိုအပ်တာတွေ တိုက်ရိုက်သွင်းမည်
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# လိုအပ်သော python packages များ ထည့်သွင်းရန်
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ကုဒ်ဖိုင်များအားလုံးကို ကူးယူမည်
COPY . .

# FastAPI ဆာဗာကို စတင်ရန်
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]

