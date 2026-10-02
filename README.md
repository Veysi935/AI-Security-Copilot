
# 🛡️ AI Security Copilot (Akıllı Güvenlik Karar Merkezi)

Bu proje, standart kamera izleme sistemlerini akıllı birer "Karar Destek Sistemine" (VMS) dönüştürmek amacıyla geliştirilmiş, **Olay Güdümlü (Event-Driven)** ve **Yapay Zeka Destekli** bir güvenlik mimarisidir.

## 🚀 Proje Mimarisi ve Özellikler

- **Akıllı Davranış Motoru (Smart Behavior Engine):** Sistem sadece "kırmızı alana girildi" demez. `Alan (Zone) + Davranış (Speed/Motion) + Zaman (Loitering)` formülüyle çalışır. Örneğin, Sarı alanda (Şüpheli Bölge) kişinin bekleme süresini (Loitering) hesaplayarak risk durumuna göre eşik tetiklemesi yapar. Kişilerin pikseller arası öklid mesafesini hesaplayarak donanımı yormadan "Koşma/Hızlanma" tespiti gerçekleştirir.
- **Dinamik Risk Skorlaması:** İhlallere 10 üzerinden risk puanı atanır. Gece saatleri, kalabalık ortamlar, koşarak girme veya şüpheli bekleme süreleri (Loitering) riski artırır.
- **Çift Motorlu Sensör (Dual-Engine):** İnsan takibi yapan ana YOLOv8 motoruna ek olarak, tüm ekranı bağımsız olarak tarayan özel eğitilmiş tehdit modeli (`tehdit.pt`) çalışır. FPS optimizasyonu için kare atlama (frame-skipping) uygulanmıştır. Kişinin alana neyle (Silah vb.) girdiği anında tespit edilir.
- **API Spam Koruması (Cooldown):** Sürekli aynı kareyi LLM'e gönderip API kotasını doldurmamak için ID tabanlı bir hafıza sözlüğü kullanılır. Risk skoru 5'in altındaki olaylar API'ye gönderilmez.
- **Google Gemini 1.5 Flash Entegrasyonu:** Yüksek riskli anlarda, durumun bağlamı (saat, kişi sayısı, ihlal türü) görselle birlikte Gemini API'ye iletilir ve bir güvenlik görevlisi ağzından saniyeler içinde rapor üretilir.
- **CSV Audit Trail:** Üretilen tüm alarmlar ve AI raporları sonsuza kadar saklanmak üzere loglanır.

## 🛠️ Kullanılan Teknolojiler
- **Dil & Arayüz:** Python, Streamlit
- **Bilgisayarlı Görü:** OpenCV, YOLOv8 (Ultralytics)
- **Yapay Zeka & LLM:** Google Gemini API, Custom Trained Threat Model
- **Mimari:** Event-Driven Architecture, State Machine

## ⚙️ Kurulum ve Çalıştırma (Kendi Bilgisayarınızda Denemek İçin)

Projenin bağımlılıklarını kurup, `.env` dosyasında `GEMINI_API_KEY` ve `CAMERA_SOURCE=0` tanımlamalarını yaptıktan sonra terminalden arayüzü başlatabilirsiniz:
```bash
streamlit run ui/app.py
