# rules/tripwire.py
import numpy as np

class TripwireRule:
    def __init__(self, rule_name: str, start_point: tuple, end_point: tuple):
        """
        Sanal bir sınır çizgisi oluşturur.
        start_point: (x1, y1)
        end_point: (x2, y2)
        """
        self.rule_name = rule_name
        self.A = np.array(start_point)
        self.B = np.array(end_point)

    def _ccw(self, A, B, C):
        """Üç noktanın saat yönünün tersine dizilip dizilmediğini kontrol eder (Kesişim matematiği)"""
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def check_intersection(self, prev_pos: tuple, curr_pos: tuple) -> bool:
        """
        Objenin bir önceki konumu ile şu anki konumu arasına hayali bir çizgi çeker.
        Eğer bu hayali çizgi, bizim sanal güvenlik çizgimizle kesişirse True döner.
        """
        C = np.array(prev_pos)
        D = np.array(curr_pos)
        
        # İki çizgi parçasının (AB ve CD) kesişip kesişmediğini denetleyen klasik algoritma
        intersect = (self._ccw(self.A, C, D) != self._ccw(self.B, C, D)) and \
                    (self._ccw(self.A, self.B, C) != self._ccw(self.A, self.B, D))
        
        return intersect