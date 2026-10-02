# rules/zone.py
import numpy as np
import cv2

class ZoneRule:
    def __init__(self, rule_name: str, polygon_points: list):
        """
        Kullanıcının çizdiği noktaları OpenCV'nin anlayacağı bir çokgen (poligon) matrisine çevirir.
        polygon_points: [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
        """
        self.rule_name = rule_name
        self.polygon = np.array(polygon_points, np.int32).reshape((-1, 1, 2))

    def check_intersection(self, prev_pos: tuple, current_pos: tuple) -> bool:
        """
        Kişinin bir önceki konumuna ve şu anki konumuna bakar.
        Eğer dışarıdan içeriye doğru bir geçiş varsa ihlal (True) fırlatır.
        """
        # cv2.pointPolygonTest: Nokta alanın içindeyse > 0, dışındaysa < 0 döndürür
        prev_inside = cv2.pointPolygonTest(self.polygon, prev_pos, False) >= 0
        curr_inside = cv2.pointPolygonTest(self.polygon, current_pos, False) >= 0
        
        # Sadece alana İLK giriş anında alarm ver (Spam engelleme)
        if not prev_inside and curr_inside:
            return True
            
        return False