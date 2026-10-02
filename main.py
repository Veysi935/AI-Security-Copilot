# main.py
import cv2
import time
from config.settings import settings

# Yazdığımız modülleri içeri aktarıyoruz
from vision.detector import VisionDetector
from vision.tracker import VisionTracker
from rules.tripwire import TripwireRule
from rules.engine import RuleEngine
from llm.agent import SecurityLLMAgent

def main():
    print("[BİLGİ] AI Security Copilot başlatılıyor...")

    # 1. Modüllerin Başlatılması (Initialization)
    print("[BİLGİ] Modüller yükleniyor (YOLO, DeepSORT, Gemini)...")
    detector = VisionDetector(model_path=settings.YOLO_MODEL_PATH, conf_threshold=settings.CONFIDENCE_THRESHOLD)
    tracker = VisionTracker(max_age=30)
    
    rule_engine = RuleEngine()
    # Örnek bir sanal çizgi ekliyoruz (Kameranın ortasından geçen yatay bir çizgi)
    # Kendi kameranın çözünürlüğüne göre bu koordinatları değiştirebilirsin.
    tripwire = TripwireRule(rule_name="Ana Giriş İhlali", start_point=(100, 300), end_point=(500, 300))
    rule_engine.add_rule(tripwire)

    llm_agent = SecurityLLMAgent()

    # 2. Kamera Akışını Açma
    cap = cv2.VideoCapture(settings.CAMERA_SOURCE)
    if not cap.isOpened():
        print(f"[HATA] Kamera açılamadı: {settings.CAMERA_SOURCE}")
        return

    # Spam engelleme için son raporlama zamanını tutuyoruz
    last_report_time = 0
    cooldown_seconds = 10  # Aynı kural için 10 saniyede bir LLM'e git

    print("[BİLGİ] Sistem aktif. Çıkmak için 'q' tuşuna basın.")
    frame_count = 0

    # 3. Ana Döngü (Main Loop)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[UYARI] Kameradan kare alınamadı. Döngü kırılıyor.")
            break
            
        frame_count += 1

        # A: GÖZ - Tespit (Detection)
        raw_detections = detector.detect(frame)

        # B: GÖZ - Takip (Tracking)
        tracked_objects = tracker.update(raw_detections, frame)

        # C: MANTIK - Kural Denetimi
        violations = rule_engine.evaluate(tracked_objects, frame_count)

        # D: BEYİN - İhlal varsa Raporla
        current_time = time.time()
        for violation in violations:
            if current_time - last_report_time > cooldown_seconds:
                print(f"\n[ALARM] İhlal Yakalandı! Kural: {violation['rule_name']} | Obje ID: {violation['object_id']}")
                print("[BİLGİ] LLM Ajanı rapor oluşturuyor, lütfen bekleyin...")
                
                # Olay anının fotoğrafını çekip ajana gönderiyoruz
                report = llm_agent.generate_report(frame, violation)
                print(f"\n=== GÜVENLİK RAPORU ===\n{report}\n=======================\n")
                
                last_report_time = current_time

        # --- EKRAN ÇİZİMLERİ (Görsel Hata Ayıklama - Debugging) ---
        # 1. Sanal çizgiyi çiz (Sarı renk)
        cv2.line(frame, tripwire.A, tripwire.B, (0, 255, 255), 2)
        
        # 2. Takip edilen objelerin kutularını çiz (Yeşil renk)
        for obj in tracked_objects:
            x1, y1, x2, y2 = obj["bbox"]
            obj_id = obj["id"]
            label = f"{obj['class']} ID:{obj_id}"
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Objenin alt merkez noktasını (ayak basma yeri) işaretle
            center_x = int((x1 + x2) / 2)
            cv2.circle(frame, (center_x, y2), 4, (0, 0, 255), -1)

        # Ekranı göster
        cv2.imshow("AI Security Copilot - Gözlem Ekranı", frame)

        # 'q' ile çıkış
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 4. Kapanış ve Temizlik
    cap.release()
    cv2.destroyAllWindows()
    print("[BİLGİ] Sistem güvenli bir şekilde kapatıldı.")

if __name__ == "__main__":
    main()