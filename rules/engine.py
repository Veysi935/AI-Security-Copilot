# rules/engine.py
from typing import List, Dict

class RuleEngine:
    def __init__(self):
        # Aktif kuralları burada tutacağız
        self.active_rules = []
        # Objelerin bir önceki karedeki konumlarını hafızada tutmak için
        self.object_history = {} 

    def add_rule(self, rule):
        """Motora yeni bir güvenlik kuralı (örn: Tripwire) ekler."""
        self.active_rules.append(rule)

    # rules/engine.py içindeki ilgili bölüm
    def evaluate(self, current_detections: list, frame_id: int) -> list:
        violations = []

        for obj in current_detections:
            obj_id = obj.get("id")
            x1, y1, x2, y2 = obj["bbox"]
            current_pos = (int((x1 + x2) / 2), y2) 

            # 1. Uzamsal (Geçiş) Kurallarını Denetle (Tripwire, Zone vb.)
            if obj_id in self.object_history:
                prev_pos = self.object_history[obj_id]
                for rule in self.active_rules:
                    if hasattr(rule, 'check_intersection'):
                        if rule.check_intersection(prev_pos, current_pos):
                            violations.append({
                                "rule_name": rule.rule_name,
                                "object_id": obj_id,
                                "class": obj["class"],
                                "timestamp_frame": frame_id
                            })

            # 2. Zamansal (Bekleme) Kurallarını Denetle (Loitering)
            for rule in self.active_rules:
                if hasattr(rule, 'check'):
                    if rule.check(obj_id, current_pos):
                        violations.append({
                            "rule_name": rule.rule_name,
                            "object_id": obj_id,
                            "class": obj["class"],
                            "timestamp_frame": frame_id
                        })

            self.object_history[obj_id] = current_pos

        return violations