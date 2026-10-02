# rules/threat.py
class ThreatRule:
    def __init__(self, rule_name: str, threat_classes: list):
        self.rule_name = rule_name
        # Modelin tanıdığı tehlikeli sınıfların isimleri (Örn: 'pistol', 'gun', 'knife')
        self.threat_classes = threat_classes

    def check(self, detected_class: str) -> bool:
        # Ekranda görülen obje bizim tehlike listemizde var mı?
        if detected_class.lower() in self.threat_classes:
            return True
        return False