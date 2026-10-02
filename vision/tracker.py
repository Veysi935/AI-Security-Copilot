# vision/tracker.py
from deep_sort_realtime.deepsort_tracker import DeepSort
import numpy as np

class VisionTracker:
    def __init__(self, max_age: int = 30):
        """
        DeepSORT takipçisini başlatır.
        max_age: Bir obje ekrandan çıkarsa/kaybolursa, ID'sini kaç kare (frame) boyunca hafızada tutacağımızı belirler.
        """
        self.tracker = DeepSort(
            max_age=max_age, 
            n_init=3,          # Objenin onaylanması için art arda 3 karede görünmesi gerekir (Yanlış alarmları önler)
            nms_max_overlap=1.0, 
            embedder="mobilenet" # Görsel özellikleri çıkarmak için hafif bir model
        )

    def update(self, detections: list, frame: np.ndarray) -> list:
        """
        Detektörden gelen isimsiz tespitleri alır, onlara ID atar ve geri döndürür.
        
        Beklenen input: [{'class': 'person', 'confidence': 0.89, 'bbox': [x1, y1, x2, y2]}, ...]
        Döndürülen output: [{'id': '1', 'class': 'person', 'bbox': [x1, y1, x2, y2]}, ...]
        """
        # DeepSORT'un beklediği özel formata dönüştürüyoruz: [ ([x, y, w, h], confidence, class_name) ]
        bbs = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            w = x2 - x1
            h = y2 - y1
            
            # DeepSORT [sol_x, ust_y, genislik, yukseklik] formatını bekler
            bbs.append(([x1, y1, w, h], det["confidence"], det["class"]))

        # Takipçiyi güncelliyoruz (Frame'i veriyoruz ki objenin renk/kıyafet özelliklerini çıkarabilsin)
        tracks = self.tracker.update_tracks(bbs, frame=frame)
        
        tracked_objects = []
        for track in tracks:
            # Sadece Tracker tarafından 'gerçek' olduğu onaylanmış objeleri alıyoruz
            if not track.is_confirmed():
                continue
            
            track_id = track.track_id
            ltrb = track.to_ltrb() # Tekrar [x1, y1, x2, y2] formatına çevir
            class_name = track.get_det_class()
            
            tracked_objects.append({
                "id": track_id,
                "class": class_name,
                "bbox": [int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3])]
            })
            
        return tracked_objects