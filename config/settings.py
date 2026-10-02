# config/settings.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Proje Ayarları
    PROJECT_NAME: str = "AI Security Copilot"
    DEBUG_MODE: bool = True
    
    # Vision Ayarları
    CAMERA_SOURCE: int=0  # 0 webcam için, rtsp://... IP kameralar için
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    
    # LLM Ayarları
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "api_anahtarini_buraya_yaz_veya_env_kullan")
    
    class Config:
        env_file = ".env"

# Diğer dosyalardan Settings'i çağırmak için global bir nesne
settings = Settings()