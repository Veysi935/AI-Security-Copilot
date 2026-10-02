# vision/detector.py
from ultralytics import YOLO
import cv2
import numpy as np

class VisionDetector:
    def __init__(self, model_path: str, conf_threshold: float):
        """
        YOLO modelini başlatır. Modeli bir kez yükleyip hafızada tutarız.
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame: np.ndarray) -> list:
        """
        Kareyi alır ve tespit edilen nesnelerin listesini döndürür.
        Çıktı formatı: [{'class': 'person', 'confidence': 0.89, 'bbox': [x1, y1, x2, y2]}, ...]
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Koordinatları, güven skorunu ve sınıf kimliğini alıyoruz
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]
                
                detections.append({
                    "class": class_name,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2]
                })
                
        return detections