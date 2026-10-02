# rules/loitering.py
import numpy as np
import cv2
import time

class LoiteringRule:
    def __init__(self, rule_name: str, polygon_points: list, max_seconds: int = 10):
        """
        Belirli bir alanda 'max_seconds' süresinden fazla duran objeleri tespit eder.
        """
        self.rule_name = rule_name
        self.polygon = np.array(polygon_points, np.int32).reshape((-1, 1, 2))
        self.max_seconds = max_seconds
        
        # İçerideki objelerin giriş zamanlarını tutacağımız sözlük {id: timestamp}
        self.object_timers = {} 
        # Aynı kişi için sürekli alarm üretmemek için raporlananları tutacağımız küme
        self.reported_objects = set()

    def check(self, object_id: int, current_pos: tuple) -> bool:
        """
        Objenin anlık pozisyonunu ve kimliğini alıp süreyi ölçer.
        """
        # Obje şu an alanın içinde mi?
        is_inside = cv2.pointPolygonTest(self.polygon, current_pos, False) >= 0

        if is_inside:
            # Obje alana YENİ girdiyse, kronometreyi başlat
            if object_id not in self.object_timers:
                self.object_timers[object_id] = time.time()
            else:
                # Obje zaten içerideyse, ne kadar süredir içeride olduğunu hesapla
                elapsed_time = time.time() - self.object_timers[object_id]
                
                # Süre dolduysa ve daha önce raporlanmadıysa alarm fırlat
                if elapsed_time > self.max_seconds and object_id not in self.reported_objects:
                    self.reported_objects.add(object_id)
                    return True
        else:
            # Obje alandan çıktıysa kronometresini ve rapor kaydını temizle
            if object_id in self.object_timers:
                del self.object_timers[object_id]
            if object_id in self.reported_objects:
                self.reported_objects.remove(object_id)

        return False