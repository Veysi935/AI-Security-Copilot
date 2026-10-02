# ui/app.py
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import cv2
import time
import sys
import os
import numpy as np
import math
import csv
from datetime import datetime
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import settings
from vision.detector import VisionDetector
from vision.tracker import VisionTracker
from llm.agent import SecurityLLMAgent

st.set_page_config(page_title="AI Security Copilot", layout="wide")
st.title("🛡️ AI Security Copilot - Akıllı Davranış ve Karar Merkezi")

# --- KALICI LOG DOSYASI ---
LOG_FILE = "guvenlik_kayitlari.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Tarih_Saat", "Olay", "Obje_ID", "Risk_Skoru", "Yapay_Zeka_Raporu"])

def save_log_to_csv(time_str, rule, obj_id, risk, report):
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([time_str, rule, obj_id, risk, report])

if "event_logs" not in st.session_state:
    st.session_state.event_logs = []

# 🔥 YENİ: AKILLI DAVRANIŞ MOTORU (STATE MACHINE)
class SmartBehaviorEngine:
    def __init__(self):
        # Her ID için: { id: {'first_seen': time, 'last_pos': (x,y), 'last_time': time, 'speed': 0} }
        self.id_states = {}
        self.RUNNING_SPEED_THRESHOLD = 150 # Piksel/saniye (Kamera açına göre ayarlayabilirsin)

    def evaluate(self, tracked_objects, red_zones, yellow_zones, current_time):
        events = []
        current_ids = []

        for obj in tracked_objects:
            obj_id = obj['id']
            current_ids.append(obj_id)
            x1, y1, x2, y2 = obj["bbox"]
            
            # Ayakların yere bastığı merkez nokta
            bottom_center = (int((x1 + x2) / 2), int(y2))

            # 1. ID HAFIZASI VE HIZ HESAPLAMA (Öklid Mesafesi)
            if obj_id not in self.id_states:
                self.id_states[obj_id] = {
                    'first_seen': current_time,
                    'last_pos': bottom_center,
                    'last_time': current_time,
                    'speed': 0,
                    'behavior': 'yürüyor'
                }
            else:
                state = self.id_states[obj_id]
                dt = current_time - state['last_time']
                
                # Saniyede bir hız güncellemesi yap (titremeleri önlemek için)
                if dt > 0.5: 
                    dx = bottom_center[0] - state['last_pos'][0]
                    dy = bottom_center[1] - state['last_pos'][1]
                    distance = math.sqrt(dx**2 + dy**2)
                    speed = distance / dt
                    
                    state['speed'] = speed
                    state['behavior'] = 'KOŞUYOR' if speed > self.RUNNING_SPEED_THRESHOLD else 'yürüyor'
                    state['last_pos'] = bottom_center
                    state['last_time'] = current_time

            state = self.id_states[obj_id]
            time_on_screen = current_time - state['first_seen']

            # 2. ALAN (ZONE) KONTROLÜ
            in_red = any(cv2.pointPolygonTest(np.array(z["points"], np.int32), bottom_center, False) >= 0 for z in red_zones)
            in_yellow = any(cv2.pointPolygonTest(np.array(z["points"], np.int32), bottom_center, False) >= 0 for z in yellow_zones)

            # 3. DİNAMİK EŞİKLER VE OLAY ÜRETİMİ (Zone + Behavior + Time)
            event_name = None
            risk_score = 0

            if in_red:
                event_name = f"Kırmızı Alan İhlali ({state['behavior']})"
                risk_score = 8 if state['behavior'] == 'KOŞUYOR' else 5
            elif in_yellow and time_on_screen > 20: # Sarı alanda 20 sn eşiği
                event_name = f"Sarı Alanda Şüpheli Bekleme ({int(time_on_screen)} sn)"
                risk_score = 4
            elif not in_red and not in_yellow and time_on_screen > 60: # Normal alanda 60 sn eşiği
                event_name = f"Genel Alanda Uzun Süreli Gözetleme ({int(time_on_screen)} sn)"
                risk_score = 3
                
            # Hızlı hareket her zaman şüphelidir (Alan bağımsız ekstra kontrol)
            if state['behavior'] == 'KOŞUYOR' and not in_red:
                if risk_score == 0: 
                    event_name = "Ani Hızlanma / Koşma Tespiti"
                risk_score += 2

            if event_name and risk_score >= 5: # Sadece 5 ve üzeri riski raporla
                events.append({
                    'object_id': obj_id,
                    'rule_name': event_name,
                    'class': 'PERSON',
                    'risk': risk_score
                })

        # Ekrandan çıkan ID'leri hafızadan temizle (RAM şişmesin)
        for old_id in list(self.id_states.keys()):
            if old_id not in current_ids:
                del self.id_states[old_id]

        return events


@st.cache_data
def get_background_image():
    cap = cv2.VideoCapture(settings.CAMERA_SOURCE)
    ret, frame = cap.read()
    cap.release()
    if ret: return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return None

bg_image = get_background_image()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1️⃣ Güvenlik Alanlarını Çiz")
    cizim_modu = st.radio("Fırça Türünü Seçin:", ["🔴 Kırmızı Alan", "🟡 Sarı Alan"], horizontal=True)
    stroke_color, fill_color = ("red", "rgba(255, 0, 0, 0.3)") if "Kırmızı" in cizim_modu else ("yellow", "rgba(255, 255, 0, 0.3)")
        
    canvas_result = st_canvas(
        fill_color=fill_color, stroke_width=3, stroke_color=stroke_color,
        background_image=Image.fromarray(bg_image) if bg_image is not None else None,
        update_streamlit=True, height=bg_image.shape[0] if bg_image is not None else 400,
        width=bg_image.shape[1] if bg_image is not None else 600,
        drawing_mode="rect", key="canvas",
    )

    run_camera = st.checkbox("2️⃣ Sistemi Silahlandır", value=False)
    frame_placeholder = st.empty()

with col2:
    st.subheader("🚨 Akıllı Olay Kayıtları")
    log_placeholder = st.empty()

if run_camera:
    red_zones = []
    yellow_zones = []
    
    if canvas_result.json_data is not None:
        for obj in canvas_result.json_data["objects"]:
            if obj["type"] == "rect":
                left, top, width, height = int(obj["left"]), int(obj["top"]), int(obj["width"]), int(obj["height"])
                pts = [(left, top), (left + width, top), (left + width, top + height), (left, top + height)]
                if obj["stroke"] == "red": red_zones.append({"color": (0, 0, 255), "points": pts})
                elif obj["stroke"] == "yellow": yellow_zones.append({"color": (0, 255, 255), "points": pts})

    detector = VisionDetector(model_path=settings.YOLO_MODEL_PATH, conf_threshold=settings.CONFIDENCE_THRESHOLD)
    tracker = VisionTracker(max_age=30)
    threat_detector = VisionDetector(model_path="tehdit.pt", conf_threshold=0.60) 
    
    behavior_engine = SmartBehaviorEngine()
    llm_agent = SecurityLLMAgent()
    cap = cv2.VideoCapture(settings.CAMERA_SOURCE)
    
    frame_count = 0
    id_cooldowns = {} 
    last_threat_detections = []

    while cap.isOpened() and run_camera:
        ret, frame = cap.read()
        if not ret: break
        
        frame_count += 1
        current_time_sec = time.time()
        
        raw_detections = detector.detect(frame)
        tracked_objects = tracker.update(raw_detections, frame)

        if frame_count % 10 == 0:
            last_threat_detections = threat_detector.detect(frame)

        # 1. DAVRANIŞ VE ALAN ANALİZİ (YENİ MOTOR)
        behavior_events = behavior_engine.evaluate(tracked_objects, red_zones, yellow_zones, current_time_sec)

        # 2. GLOBAL TEHDİT KONTROLÜ (SİLAH/BIÇAK)
        for tehdit in last_threat_detections:
            t_class = tehdit["class"].upper()
            tehdit_anahtari = f"TEHDIT_{t_class}"
            
            if tehdit_anahtari not in id_cooldowns or (current_time_sec - id_cooldowns[tehdit_anahtari] > 30):
                behavior_events.append({
                    'object_id': "GLOBAL",
                    'rule_name': f"🚨 KRİTİK TEHDİT: {t_class}",
                    'class': t_class,
                    'risk': 10
                })
                id_cooldowns[tehdit_anahtari] = current_time_sec

        # 3. LLM RAPORLAMA VE LOGLAMA
        kisi_sayisi = len(tracked_objects)
        
        for event in behavior_events:
            obj_id = event['object_id']
            
            if obj_id != "GLOBAL" and (obj_id in id_cooldowns and (current_time_sec - id_cooldowns[obj_id] < 30)):
                continue 
                
            risk_score = event['risk']
            current_hour = datetime.now().hour
            if current_hour >= 22 or current_hour <= 5: risk_score += 2 
            if kisi_sayisi >= 3: risk_score += 2 
                
            durum_notu = f"(Saat: {current_hour}:00, Alandaki Kişi: {kisi_sayisi})"
            violation_data = {
                "rule_name": f"{event['rule_name']} (Risk: {risk_score}/10)",
                "class": f"{event['class']} {durum_notu}",
                "object_id": obj_id
            }
            
            report = llm_agent.generate_report(frame, violation_data)
            log_zamani = time.strftime("%H:%M:%S")
            
            st.session_state.event_logs.append({
                "time": log_zamani, "rule": event['rule_name'], "id": obj_id, "risk": risk_score, "report": report
            })
            save_log_to_csv(log_zamani, event['rule_name'], obj_id, risk_score, report)
            
            if obj_id != "GLOBAL":
                id_cooldowns[obj_id] = current_time_sec

        # --- ÇİZİMLER ---
        for z_list in [red_zones, yellow_zones]:
            for zone in z_list:
                pts = np.array(zone["points"], np.int32).reshape((-1, 1, 2))
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], zone["color"])
                cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
                cv2.polylines(frame, [pts], isClosed=True, color=zone["color"], thickness=2)

        for obj in tracked_objects:
            x1, y1, x2, y2 = obj["bbox"]
            obj_id = obj['id']
            # Hız ve Davranış bilgisini ekrana yazdır!
            behavior_text = behavior_engine.id_states.get(obj_id, {}).get('behavior', '')
            color = (0, 0, 255) if behavior_text == 'KOŞUYOR' else (0, 255, 0)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID:{obj_id} | {behavior_text}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        for tehdit in last_threat_detections:
            x1, y1, x2, y2 = tehdit["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(frame, f"TEHLIKE: {tehdit['class']}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_column_width=True)

        with log_placeholder.container():
            for log in reversed(st.session_state.event_logs): 
                icon = "🚨🔫" if log['risk'] >= 10 else "🔥" if log['risk'] >= 7 else "🔴" if log['risk'] >= 5 else "🟡"
                with st.chat_message("assistant", avatar="🚨"):
                    st.markdown(f"**⏰ {log['time']} | {icon} {log['rule']} (Risk: {log['risk']} - ID: {log['id']})**")
                    st.write(log['report'])

    cap.release()