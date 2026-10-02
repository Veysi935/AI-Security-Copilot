# llm/agent.py
from google import genai
from PIL import Image
import cv2
import numpy as np

# Ayar dosyamızı içeri aktarıyoruz
from config.settings import settings 

class SecurityLLMAgent:
    # Ücretsiz kotası en esnek olan 'lite-latest' modelini seçiyoruz
    def __init__(self, model_name: str = "gemini-flash-lite-latest"):
        """
        Google'ın YENİ nesil (google-genai) SDK'sı ile Gemini API'sini başlatır.
        """
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = model_name
        
        # Sistem promptu: LLM'e "Persona" (Kişilik) atıyoruz.
        self.system_instruction = (
            "Sen kıdemli bir siber güvenlik ve fiziksel güvenlik analistisin. "
            "Görevin, güvenlik kameralarından gelen ihlal fotoğraflarını inceleyip, "
            "kolluk kuvvetlerine veya saha güvenlik ekiplerine verilecek net, profesyonel "
            "ve aksiyona dönüştürülebilir kısa raporlar yazmaktır. "
            "Gereksiz detaylara girme, potansiyel tehdidi, kişinin görünümünü ve durumu özetle."
        )

    def generate_report(self, frame: np.ndarray, violation_data: dict) -> str:
        """
        İhlal anının karesini ve olay verilerini alıp analiz raporu döndürür.
        """
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        prompt = (
            f"Olay Log Kayıtları:\n"
            f"- İhlal Edilen Kural: {violation_data['rule_name']}\n"
            f"- Tespit Edilen Obje: Sınıf={violation_data['class']}, ID={violation_data['object_id']}\n\n"
            "Lütfen ekteki fotoğrafı bu log kayıtları ışığında incele ve acil durum raporunu oluştur."
        )
        
        # --- İŞTE GERÇEK YAPAY ZEKA BAĞLANTISI BURASI ---
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, pil_image],
                config=genai.types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                )
            )
            return response.text
            
        except Exception as e:
            return f"SİSTEM UYARISI: API hatası oluştu. (Hata Detayı: {str(e)})"