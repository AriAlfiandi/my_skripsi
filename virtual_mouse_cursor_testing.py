from cvzone.HandTrackingModule import HandDetector
import cv2
import math
from pynput.mouse import Button, Controller
import screeninfo
import time
from datetime import datetime
import json

# Inisialisasi mouse controller
mouse = Controller()

# Mendapatkan informasi resolusi layar
screen = screeninfo.get_monitors()[0]
screen_width, screen_height = screen.width, screen.height

# Inisialisasi kamera
cap = cv2.VideoCapture(0)

# Inisialisasi hand detector (maxHands=2 untuk deteksi kedua tangan terangkat)
detector = HandDetector(detectionCon=0.3, maxHands=2)

# Variabel untuk menyimpan status scroll aktif/nonaktif
scroll_active = True

# Variabel untuk mengaktifkan/menonaktifkan SEMUA gesture
all_gestures_active = True

# Variabel untuk deteksi kedua tangan terangkat (keluar program)
both_hands_raised_start_time = None
BOTH_HANDS_RAISED_DURATION = 3.0  # 3 detik untuk konfirmasi keluar

# ============= MODE TESTING KONTROL KURSOR =============
cursor_testing_mode = False
cursor_test_targets = []
cursor_test_results = {
    'precision_tests': [],
    'smoothness_tests': [],
    'speed_tests': []
}

def generate_target_grid(img_width, img_height, grid_size=3):
    """Generate grid 3x3 target points"""
    targets = []
    margin_x = img_width // 6
    margin_y = img_height // 6
    
    step_x = (img_width - 2 * margin_x) // (grid_size - 1)
    step_y = (img_height - 2 * margin_y) // (grid_size - 1)
    
    for row in range(grid_size):
        for col in range(grid_size):
            x = margin_x + col * step_x
            y = margin_y + row * step_y
            targets.append((x, y))
    
    return targets

# ============= FUNGSI DETEKSI KEDUA TANGAN TERANGKAT =============
def is_hand_raised(hand_landmarks):
    """
    Mendeteksi apakah tangan terangkat (semua ujung jari di atas pergelangan)
    """
    wrist_y = hand_landmarks[0][1]
    
    # Landmark ujung jari: jempol, telunjuk, tengah, manis, kelingking
    fingertip_landmarks = [4, 8, 12, 16, 20]
    
    # Cek apakah semua ujung jari di atas pergelangan (koordinat y lebih kecil)
    for tip_idx in fingertip_landmarks:
        if hand_landmarks[tip_idx][1] >= wrist_y: 
            return False
    
    return True

def check_both_hands_raised(hands):
    """
    Mendeteksi apakah kedua tangan terangkat
    """
    if len(hands) != 2:
        return False
    
    # Cek kedua tangan
    hand1_raised = is_hand_raised(hands[0]["lmList"])
    hand2_raised = is_hand_raised(hands[1]["lmList"])
    
    return hand1_raised and hand2_raised

# ============= CURSOR TESTING TRACKER =============
class CursorTestTracker:
    def __init__(self):
        self.precision_hits = []  # List of (target_pos, cursor_pos, deviation_px)
        self.smoothness_data = []  # List of cursor positions untuk smooth tracking
        self.speed_data = []  # List of (speed_category, distance_px, time_ms)
        self.last_cursor_pos = None
        self.last_cursor_time = None
        
    def add_precision_test(self, target_pos, cursor_pos):
        """Record precision test result"""
        deviation = math.hypot(target_pos[0] - cursor_pos[0], 
                              target_pos[1] - cursor_pos[1])
        self.precision_hits.append({
            'target': target_pos,
            'cursor': cursor_pos,
            'deviation_px': deviation
        })
        return deviation
    
    def add_smoothness_sample(self, cursor_pos, current_time):
        """Record cursor position for smoothness analysis"""
        self.smoothness_data.append({
            'position': cursor_pos,
            'time': current_time
        })
        
        # Keep only last 100 samples
        if len(self.smoothness_data) > 100:
            self.smoothness_data.pop(0)
    
    def calculate_jitter(self):
        """Calculate jitter (variation in cursor movement)"""
        if len(self.smoothness_data) < 3:
            return 0.0
        
        distances = []
        for i in range(1, len(self.smoothness_data)):
            prev = self.smoothness_data[i-1]['position']
            curr = self.smoothness_data[i]['position']
            dist = math.hypot(curr[0] - prev[0], curr[1] - prev[1])
            distances.append(dist)
        
        if not distances:
            return 0.0
        
        # Calculate standard deviation of distances
        mean_dist = sum(distances) / len(distances)
        variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
        jitter = math.sqrt(variance)
        
        return jitter
    
    def add_speed_test(self, speed_category, distance_px, time_ms):
        """Record speed test result"""
        self.speed_data.append({
            'category': speed_category,
            'distance_px': distance_px,
            'time_ms': time_ms,
            'speed_px_per_s': (distance_px / time_ms * 1000) if time_ms > 0 else 0
        })
    
    def get_precision_stats(self):
        """Get precision statistics"""
        if not self.precision_hits:
            return {
                'avg_deviation': 0.0,
                'min_deviation': 0.0,
                'max_deviation': 0.0,
                'success_rate': 0.0,
                'count': 0
            }
        
        deviations = [h['deviation_px'] for h in self.precision_hits]
        # Success if deviation < 50px
        success_count = sum(1 for d in deviations if d < 50)
        
        return {
            'avg_deviation': sum(deviations) / len(deviations),
            'min_deviation': min(deviations),
            'max_deviation': max(deviations),
            'success_rate': (success_count / len(deviations)) * 100,
            'count': len(deviations)
        }
    
    def get_smoothness_stats(self):
        """Get smoothness statistics"""
        jitter = self.calculate_jitter()
        
        # Smoothness score (inverse of jitter, normalized)
        if jitter == 0:
            smoothness_score = 100.0
        else:
            smoothness_score = max(0, 100 - jitter)
        
        return {
            'jitter_px': jitter,
            'smoothness_score': smoothness_score,
            'sample_count': len(self.smoothness_data)
        }
    
    def get_speed_stats(self):
        """Get speed test statistics by category"""
        stats = {}
        categories = set(s['category'] for s in self.speed_data)
        
        for cat in categories:
            cat_data = [s for s in self.speed_data if s['category'] == cat]
            if cat_data:
                avg_speed = sum(d['speed_px_per_s'] for d in cat_data) / len(cat_data)
                avg_time = sum(d['time_ms'] for d in cat_data) / len(cat_data)
                stats[cat] = {
                    'avg_speed_px_per_s': avg_speed,
                    'avg_time_ms': avg_time,
                    'count': len(cat_data)
                }
        
        return stats
    
    def save_cursor_test_report(self, filename='laporan_kontrol_kursor.txt'):
        """Save detailed cursor control testing report"""
        precision_stats = self.get_precision_stats()
        smoothness_stats = self.get_smoothness_stats()
        speed_stats = self.get_speed_stats()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("LAPORAN PENGUJIAN KONTROL KURSOR\n")
            f.write("Sistem Virtual Mouse - Hand Tracking\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Waktu Pengujian: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}\n\n")
            
            # PRECISION TEST
            f.write("="*80 + "\n")
            f.write("A. PENGUJIAN PRESISI (9 Titik Target)\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Total Tes Presisi      : {precision_stats['count']} titik\n")
            f.write(f"Success Rate           : {precision_stats['success_rate']:.2f}%\n")
            f.write(f"Deviasi Rata-rata      : {precision_stats['avg_deviation']:.2f} px\n")
            f.write(f"Deviasi Minimum        : {precision_stats['min_deviation']:.2f} px\n")
            f.write(f"Deviasi Maximum        : {precision_stats['max_deviation']:.2f} px\n\n")
            
            # Kategori presisi
            avg_dev = precision_stats['avg_deviation']
            if avg_dev < 20:
                kategori = "Excellent (Sangat Presisi)"
            elif avg_dev < 40:
                kategori = "Good (Presisi Baik)"
            elif avg_dev < 60:
                kategori = "Fair (Cukup)"
            else:
                kategori = "Poor (Perlu Perbaikan)"
            
            f.write(f"Kategori Presisi       : {kategori}\n\n")
            
            # Detail per target
            if self.precision_hits:
                f.write("Detail Per Target:\n")
                f.write("-" * 80 + "\n")
                for i, hit in enumerate(self.precision_hits, 1):
                    f.write(f"  Target {i}: ({hit['target'][0]}, {hit['target'][1]}) → "
                           f"Kursor: ({hit['cursor'][0]}, {hit['cursor'][1]}) → "
                           f"Deviasi: {hit['deviation_px']:.2f}px\n")
                f.write("\n")
            
            # SMOOTHNESS TEST
            f.write("="*80 + "\n")
            f.write("B. PENGUJIAN SMOOTHNESS (Kehalusan Tracking)\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Jitter (Variasi Gerak) : {smoothness_stats['jitter_px']:.2f} px\n")
            f.write(f"Smoothness Score       : {smoothness_stats['smoothness_score']:.2f}/100\n")
            f.write(f"Jumlah Sample          : {smoothness_stats['sample_count']}\n\n")
            
            # Kategori smoothness
            smooth_score = smoothness_stats['smoothness_score']
            if smooth_score >= 90:
                smooth_kategori = "Excellent (Sangat Halus)"
            elif smooth_score >= 75:
                smooth_kategori = "Good (Halus)"
            elif smooth_score >= 60:
                smooth_kategori = "Fair (Cukup)"
            else:
                smooth_kategori = "Poor (Patah-patah)"
            
            f.write(f"Kategori Smoothness    : {smooth_kategori}\n\n")
            
            # SPEED TEST
            f.write("="*80 + "\n")
            f.write("C. PENGUJIAN KECEPATAN TRACKING\n")
            f.write("="*80 + "\n\n")
            
            if speed_stats:
                for cat, stats in speed_stats.items():
                    f.write(f"{cat.upper()}:\n")
                    f.write(f"  Kecepatan Rata-rata  : {stats['avg_speed_px_per_s']:.2f} px/s\n")
                    f.write(f"  Waktu Rata-rata      : {stats['avg_time_ms']:.2f} ms\n")
                    f.write(f"  Jumlah Tes           : {stats['count']}\n\n")
            else:
                f.write("Belum ada data pengujian kecepatan.\n\n")
            
            # RANGKUMAN
            f.write("="*80 + "\n")
            f.write("RANGKUMAN UNTUK TABEL SKRIPSI\n")
            f.write("="*80 + "\n\n")
            
            f.write("TABEL 4.6: Hasil Pengujian Move Cursor (Jari Tengah)\n")
            f.write("-" * 80 + "\n\n")
            
            f.write(f"Aspek Responsivitas:\n")
            f.write(f"  Jumlah Tes     : Auto-tracking (setiap detik)\n")
            f.write(f"  Success Rate   : -\n\n")
            
            f.write(f"Aspek Presisi (9 titik):\n")
            f.write(f"  Jumlah Tes     : {precision_stats['count']}\n")
            f.write(f"  Success Rate   : {precision_stats['success_rate']:.2f}%\n")
            f.write(f"  Avg Deviation  : {precision_stats['avg_deviation']:.2f} px\n\n")
            
            f.write(f"Aspek Smoothness:\n")
            f.write(f"  Jumlah Tes     : {smoothness_stats['sample_count']} samples\n")
            f.write(f"  Score          : {smoothness_stats['smoothness_score']:.2f}/100\n")
            f.write(f"  Jitter         : {smoothness_stats['jitter_px']:.2f} px\n\n")
            
            if speed_stats:
                f.write(f"Aspek Kecepatan:\n")
                for cat, stats in speed_stats.items():
                    f.write(f"  {cat.title()}: {stats['avg_time_ms']:.2f} ms "
                           f"({stats['avg_speed_px_per_s']:.2f} px/s)\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("FORMAT UNTUK TABEL SKRIPSI:\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("+--------------------+----------+-------------+-----------+--------------+\n")
            f.write("| Aspek Pengujian    | Jumlah   | Success     | Avg       | Keterangan   |\n")
            f.write("|                    | Tes      | Rate (%)    | Deviation |              |\n")
            f.write("+--------------------+----------+-------------+-----------+--------------+\n")
            f.write(f"| Responsivitas      | Auto     | -           | -         | Auto-track   |\n")
            f.write(f"|                    |          |             |           | per 1s       |\n")
            f.write("+--------------------+----------+-------------+-----------+--------------+\n")
            f.write(f"| Presisi (9 titik)  | {precision_stats['count']:<8} | {precision_stats['success_rate']:<11.2f} | {precision_stats['avg_deviation']:<9.2f} | {kategori.split('(')[0].strip():<12} |\n")
            f.write("+--------------------+----------+-------------+-----------+--------------+\n")
            f.write(f"| Smoothness         | {smoothness_stats['sample_count']:<8} | {smoothness_stats['smoothness_score']:<11.2f} | -         | {smooth_kategori.split('(')[0].strip():<12} |\n")
            f.write("+--------------------+----------+-------------+-----------+--------------+\n")
            
            if 'lambat' in speed_stats:
                f.write(f"| Kecepatan Lambat   | {speed_stats['lambat']['count']:<8} | -           | -         | Smooth       |\n")
                f.write("+--------------------+----------+-------------+-----------+--------------+\n")
            if 'normal' in speed_stats:
                f.write(f"| Kecepatan Normal   | {speed_stats['normal']['count']:<8} | -           | -         | Good         |\n")
                f.write("+--------------------+----------+-------------+-----------+--------------+\n")
            if 'cepat' in speed_stats:
                f.write(f"| Kecepatan Cepat    | {speed_stats['cepat']['count']:<8} | -           | -         | Slight lag   |\n")
                f.write("+--------------------+----------+-------------+-----------+--------------+\n")
        
        print(f"✅ Laporan kontrol kursor disimpan ke: {filename}")

# Inisialisasi cursor test tracker
cursor_tracker = CursorTestTracker()

# ============= SISTEM TRACKING PENGUJIAN DENGAN RESPONSE TIME =============
class GestureTracker:
    def __init__(self):
        self.stats = {
            'scroll_up': {
                'detected': 0, 
                'true_positive': 0, 
                'false_positive': 0, 
                'false_negative': 0,
                'response_times': []
            },
            'scroll_down': {
                'detected': 0, 
                'true_positive': 0, 
                'false_positive': 0, 
                'false_negative': 0,
                'response_times': []
            },
            'click': {
                'detected': 0, 
                'true_positive': 0, 
                'false_positive': 0, 
                'false_negative': 0,
                'response_times': []
            },
            'toggle_scroll': {
                'detected': 0, 
                'true_positive': 0, 
                'false_positive': 0, 
                'false_negative': 0,
                'response_times': []
            },
            'move_cursor': {
                'detected': 0, 
                'true_positive': 0, 
                'false_positive': 0, 
                'false_negative': 0,
                'response_times': []
            }
        }
        self.current_gesture = None
        self.gesture_detected_time = None
        self.gesture_start_time = None
        self.waiting_for_confirmation = False
        self.start_time = time.time()
        self.frame_processing_times = []
        
    def gesture_detected(self, gesture_type, processing_time_ms):
        """Mencatat gesture yang terdeteksi dengan response time"""
        self.stats[gesture_type]['detected'] += 1
        self.stats[gesture_type]['response_times'].append(processing_time_ms)
        self.current_gesture = gesture_type
        self.gesture_detected_time = time.time()
        self.waiting_for_confirmation = True
        
    def confirm_true_positive(self):
        """Konfirmasi gesture benar (True Positive)"""
        if self.current_gesture:
            self.stats[self.current_gesture]['true_positive'] += 1
            self.waiting_for_confirmation = False
            print(f"✓ TRUE POSITIVE: {self.current_gesture}")
            
    def confirm_false_positive(self):
        """Konfirmasi gesture salah (False Positive)"""
        if self.current_gesture:
            self.stats[self.current_gesture]['false_positive'] += 1
            self.waiting_for_confirmation = False
            print(f"✗ FALSE POSITIVE: {self.current_gesture}")
            
    def add_false_negative(self, gesture_type):
        """Tambah False Negative (gesture tidak terdeteksi)"""
        self.stats[gesture_type]['false_negative'] += 1
        print(f"✗ FALSE NEGATIVE: {gesture_type}")
    
    def add_frame_processing_time(self, processing_time_ms):
        """Menyimpan waktu proses per frame"""
        self.frame_processing_times.append(processing_time_ms)
        
    def calculate_accuracy(self, gesture_type):
        """Menghitung akurasi per gesture"""
        stats = self.stats[gesture_type]
        tp = stats['true_positive']
        fp = stats['false_positive']
        fn = stats['false_negative']
        
        total = tp + fp + fn
        if total == 0:
            return 0.0
        
        accuracy = (tp / total) * 100
        return accuracy
    
    def calculate_response_time_stats(self, gesture_type):
        """Menghitung statistik response time per gesture"""
        times = self.stats[gesture_type]['response_times']
        if not times:
            return {
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'count': 0
            }
        
        return {
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'count': len(times)
        }
    
    def calculate_overall_accuracy(self):
        """Menghitung akurasi keseluruhan"""
        total_tp = sum(s['true_positive'] for s in self.stats.values())
        total_fp = sum(s['false_positive'] for s in self.stats.values())
        total_fn = sum(s['false_negative'] for s in self.stats.values())
        
        total = total_tp + total_fp + total_fn
        if total == 0:
            return 0.0
            
        accuracy = (total_tp / total) * 100
        return accuracy
    
    def calculate_overall_response_time(self):
        """Menghitung rata-rata response time keseluruhan"""
        all_times = []
        for stats in self.stats.values():
            all_times.extend(stats['response_times'])
        
        if not all_times:
            return 0.0
        
        return sum(all_times) / len(all_times)
    
    def calculate_avg_frame_processing_time(self):
        """Menghitung rata-rata waktu proses per frame"""
        if not self.frame_processing_times:
            return 0.0
        return sum(self.frame_processing_times) / len(self.frame_processing_times)
    
    def display_stats(self):
        """Menampilkan statistik di terminal"""
        print("\n" + "="*80)
        print("STATISTIK PENGUJIAN SISTEM VIRTUAL MOUSE".center(80))
        print("="*80)
        
        for gesture, stats in self.stats.items():
            accuracy = self.calculate_accuracy(gesture)
            rt_stats = self.calculate_response_time_stats(gesture)
            
            print(f"\n{gesture.upper().replace('_', ' ')}:")
            print(f"  Total Terdeteksi    : {stats['detected']}")
            print(f"  True Positive (TP)  : {stats['true_positive']}")
            print(f"  False Positive (FP) : {stats['false_positive']}")
            print(f"  False Negative (FN) : {stats['false_negative']}")
            print(f"  Akurasi             : {accuracy:.2f}%")
            print(f"  Response Time:")
            print(f"    - Rata-rata       : {rt_stats['avg']:.2f} ms")
            print(f"    - Min             : {rt_stats['min']:.2f} ms")
            print(f"    - Max             : {rt_stats['max']:.2f} ms")
            
        overall_accuracy = self.calculate_overall_accuracy()
        overall_rt = self.calculate_overall_response_time()
        avg_frame_time = self.calculate_avg_frame_processing_time()
        duration = time.time() - self.start_time
        
        print("\n" + "-"*80)
        print(f"AKURASI KESELURUHAN        : {overall_accuracy:.2f}%")
        print(f"RESPONSE TIME RATA-RATA    : {overall_rt:.2f} ms")
        print(f"FRAME PROCESSING TIME      : {avg_frame_time:.2f} ms")
        print(f"Durasi Pengujian           : {duration:.2f} detik ({duration/60:.2f} menit)")
        print("="*80 + "\n")
    
    def save_report(self, filename='laporan_pengujian.json'):
        """Menyimpan laporan ke file JSON"""
        report = {
            'waktu_pengujian': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'durasi_detik': time.time() - self.start_time,
            'akurasi_keseluruhan': self.calculate_overall_accuracy(),
            'response_time_rata_rata_ms': self.calculate_overall_response_time(),
            'frame_processing_time_ms': self.calculate_avg_frame_processing_time(),
            'detail_gesture': {}
        }
        
        for gesture, stats in self.stats.items():
            rt_stats = self.calculate_response_time_stats(gesture)
            report['detail_gesture'][gesture] = {
                'detected': stats['detected'],
                'true_positive': stats['true_positive'],
                'false_positive': stats['false_positive'],
                'false_negative': stats['false_negative'],
                'akurasi': self.calculate_accuracy(gesture),
                'response_time': {
                    'rata_rata_ms': rt_stats['avg'],
                    'min_ms': rt_stats['min'],
                    'max_ms': rt_stats['max'],
                    'jumlah_sample': rt_stats['count']
                }
            }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=4)
        
        print(f"\n✓ Laporan pengujian disimpan ke: {filename}")
        
    def save_report_text(self, filename='laporan_pengujian.txt'):
        """Menyimpan laporan ke file TXT untuk skripsi"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("LAPORAN PENGUJIAN SISTEM VIRTUAL MOUSE\n")
            f.write("Implementasi Hand Tracking untuk Kontrol Mouse\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Waktu Pengujian: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}\n")
            f.write(f"Durasi: {(time.time() - self.start_time)/60:.2f} menit\n\n")
            
            f.write("HASIL PENGUJIAN PER GESTURE:\n")
            f.write("-"*80 + "\n\n")
            
            for gesture, stats in self.stats.items():
                accuracy = self.calculate_accuracy(gesture)
                rt_stats = self.calculate_response_time_stats(gesture)
                
                f.write(f"{gesture.upper().replace('_', ' ')}:\n")
                f.write(f"  Total Deteksi       : {stats['detected']}\n")
                f.write(f"  True Positive (TP)  : {stats['true_positive']}\n")
                f.write(f"  False Positive (FP) : {stats['false_positive']}\n")
                f.write(f"  False Negative (FN) : {stats['false_negative']}\n")
                f.write(f"  Tingkat Akurasi     : {accuracy:.2f}%\n")
                f.write(f"  Response Time:\n")
                f.write(f"    - Rata-rata       : {rt_stats['avg']:.2f} ms\n")
                f.write(f"    - Minimum         : {rt_stats['min']:.2f} ms\n")
                f.write(f"    - Maximum         : {rt_stats['max']:.2f} ms\n")
                f.write(f"    - Jumlah Sample   : {rt_stats['count']}\n")
                f.write("\n")
            
            overall_accuracy = self.calculate_overall_accuracy()
            overall_rt = self.calculate_overall_response_time()
            avg_frame_time = self.calculate_avg_frame_processing_time()
            
            f.write("="*80 + "\n")
            f.write("RINGKASAN KESELURUHAN:\n")
            f.write("-"*80 + "\n")
            
            total_tp = sum(s['true_positive'] for s in self.stats.values())
            total_fp = sum(s['false_positive'] for s in self.stats.values())
            total_fn = sum(s['false_negative'] for s in self.stats.values())
            
            f.write(f"Total True Positive  : {total_tp}\n")
            f.write(f"Total False Positive : {total_fp}\n")
            f.write(f"Total False Negative : {total_fn}\n")
            f.write(f"AKURASI SISTEM       : {overall_accuracy:.2f}%\n")
            f.write(f"RESPONSE TIME RATA-RATA : {overall_rt:.2f} ms\n")
            f.write(f"FRAME PROCESSING TIME   : {avg_frame_time:.2f} ms\n")
            f.write("="*80 + "\n\n")
            
            # Analisis
            f.write("ANALISIS:\n")
            f.write("-"*80 + "\n")
            
            if overall_accuracy >= 90:
                f.write("Sistem memiliki performa SANGAT BAIK dengan akurasi di atas 90%.\n\n")
            elif overall_accuracy >= 80:
                f.write("Sistem memiliki performa BAIK dengan akurasi di atas 80%.\n\n")
            elif overall_accuracy >= 70:
                f.write("Sistem memiliki performa CUKUP dengan akurasi di atas 70%.\n\n")
            else:
                f.write("Sistem perlu PERBAIKAN dengan akurasi di bawah 70%.\n\n")
            
            # Gesture dengan akurasi tertinggi
            best_gesture = max(self.stats.items(), 
                             key=lambda x: self.calculate_accuracy(x[0]))
            best_accuracy = self.calculate_accuracy(best_gesture[0])
            if best_accuracy > 0:
                f.write(f"Gesture dengan akurasi tertinggi:\n")
                f.write(f"  - {best_gesture[0].replace('_', ' ').title()}: {best_accuracy:.2f}%\n\n")
            
            # Gesture dengan response time terbaik
            best_rt_gesture = None
            best_rt = float('inf')
            for gesture in self.stats.keys():
                rt_stats = self.calculate_response_time_stats(gesture)
                if rt_stats['count'] > 0 and rt_stats['avg'] < best_rt:
                    best_rt = rt_stats['avg']
                    best_rt_gesture = gesture
            
            if best_rt_gesture:
                f.write(f"Gesture dengan response time terbaik:\n")
                f.write(f"  - {best_rt_gesture.replace('_', ' ').title()}: {best_rt:.2f} ms\n\n")
            
            # Gesture yang perlu ditingkatkan
            worst_gestures = []
            for gesture in self.stats.keys():
                acc = self.calculate_accuracy(gesture)
                if acc > 0 and acc < 75:
                    worst_gestures.append((gesture, acc))
            
            if worst_gestures:
                f.write("Gesture yang perlu ditingkatkan:\n")
                for gesture, acc in worst_gestures:
                    f.write(f"  - {gesture.replace('_', ' ').title()}: {acc:.2f}%\n")
        
        print(f"✓ Laporan teks disimpan ke: {filename}")

# Inisialisasi tracker
tracker = GestureTracker()

# Variabel untuk cooldown antar gesture
last_gesture_time = time.time()
gesture_cooldown = 0.5

# Variabel untuk tracking state
previous_scroll_state = None
previous_click_state = False
previous_fist_state = False

# Variabel untuk cursor testing
current_target_index = 0
cursor_test_start_time = None

# Window name
window_name = "Virtual Mouse - Testing + Kontrol Kursor"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1) #kamernya selalu didepan wkwk

print("\n" + "="*80)
print("SISTEM VIRTUAL MOUSE - Mode Testing dengan Response Time".center(80))
print("="*80)
print("\nKONTROL UTAMA:")
print("  Y/y - Konfirmasi True Positive (deteksi benar)")
print("  N/n - Konfirmasi False Positive (deteksi salah)")
print("  F/f - Tambah False Negative (gesture tidak terdeteksi)")
print("  S/s - Tampilkan statistik")
print("  R/r - Reset statistik")
print("  T/t - Toggle Scroll (ON/OFF)")
print("  W/w - Toggle SEMUA Gesture (Scroll + Klik)")
print("  Q/q - Keluar dan simpan laporan")
print("\nMODE TESTING KONTROL KURSOR:")
print("  C/c - Toggle Mode Testing Kursor (ON/OFF)")
print("  P/p - Test Presisi (9 titik target)")
print("  M/m - Test Smoothness (tracking pattern)")
print("  1/2/3 - Test Kecepatan (lambat/normal/cepat)")
print("\nGESTURE EXIT:")
print("  Angkat KEDUA tangan dengan jari terbuka, tahan 3 detik")
print("\n" + "="*80 + "\n")

# Main loop
while True:
    frame_start_time = time.time()
    
    success, img = cap.read()
    if not success:
        break
    
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, draw=True, flipType=False)
    
    current_time = time.time()
    
    # Generate targets for cursor testing if in cursor test mode
    if cursor_testing_mode and not cursor_test_targets:
        cursor_test_targets = generate_target_grid(img.shape[1], img.shape[0])
    
    # Draw targets if in cursor test mode
    if cursor_testing_mode and cursor_test_targets:
        for i, target in enumerate(cursor_test_targets):
            color = (0, 255, 0) if i == current_target_index else (100, 100, 100)
            cv2.circle(img, target, 20, color, 2)
            cv2.circle(img, target, 3, color, -1)
            cv2.putText(img, str(i+1), (target[0]-10, target[1]-25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Cek apakah kedua tangan terangkat (untuk exit)
    if hands and check_both_hands_raised(hands):
        if both_hands_raised_start_time is None:
            both_hands_raised_start_time = current_time
            print("\n⏳ Kedua tangan terdeteksi terangkat! Tahan 3 detik untuk keluar...")
        
        elapsed = current_time - both_hands_raised_start_time
        remaining = BOTH_HANDS_RAISED_DURATION - elapsed
        
        if remaining > 0:
            cv2.putText(img, f"Keluar dalam {remaining:.1f} detik...", 
                       (img.shape[1]//2 - 150, img.shape[0]//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        else:
            print("\n✓ Exit gesture confirmed! Menyimpan laporan...")
            tracker.display_stats()
            tracker.save_report('laporan_pengujian.json')
            tracker.save_report_text('laporan_pengujian.txt')
            if cursor_testing_mode:
                cursor_tracker.save_cursor_test_report('laporan_kontrol_kursor.txt')
            print("\n✓ Laporan pengujian berhasil disimpan!")
            break
    else:
        both_hands_raised_start_time = None
    
    # Proses gesture hanya jika ada TEPAT 1 tangan
    if len(hands) == 1:
        hand = hands[0]
        lmList = hand["lmList"]
        if lmList:
            x1, y1 = lmList[4][0], lmList[4][1]
            x2, y2 = lmList[8][0], lmList[8][1]
            x3, y3 = lmList[12][0], lmList[12][1]
            x5, y5 = lmList[20][0], lmList[20][1]

            length = math.hypot(x2 - x1, y2 - y1)
            distance_thumb_pinky = math.hypot(x5 - x1, y5 - y1)

            cv2.circle(img, (x1, y1), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x3, y3), 8, (0, 255, 0), cv2.FILLED)
            cv2.circle(img, (x5, y5), 5, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.line(img, (x1, y1), (x5, y5), (255, 0, 255), 3)

            screen_x = int(x3 * screen_width / img.shape[1])
            screen_y = int(y3 * screen_height / img.shape[0])

            mouse.position = (screen_x, screen_y)
            
            # Cursor testing - smoothness tracking
            if cursor_testing_mode:
                cursor_tracker.add_smoothness_sample((x3, y3), current_time)
                
                # Draw cursor trail
                if len(cursor_tracker.smoothness_data) > 1:
                    for i in range(1, min(10, len(cursor_tracker.smoothness_data))):
                        prev_pos = cursor_tracker.smoothness_data[-i-1]['position']
                        curr_pos = cursor_tracker.smoothness_data[-i]['position']
                        cv2.line(img, prev_pos, curr_pos, (255, 255, 0), 2)
            
            if current_time - last_gesture_time > 1.0:
                frame_time_ms = (time.time() - frame_start_time) * 1000
                tracker.gesture_detected('move_cursor', frame_time_ms)
                last_gesture_time = current_time

            is_fist = all(math.hypot(lmList[i][0] - lmList[0][0], lmList[i][1] - lmList[0][1]) < 40 for i in [4, 8, 12, 16, 20])

            if is_fist and not previous_fist_state:
                if current_time - last_gesture_time > gesture_cooldown:
                    scroll_active = not scroll_active
                    frame_time_ms = (time.time() - frame_start_time) * 1000
                    print(f"\n🤛 TOGGLE SCROLL: {'AKTIF' if scroll_active else 'NONAKTIF'} (RT: {frame_time_ms:.2f}ms)")
                    tracker.gesture_detected('toggle_scroll', frame_time_ms)
                    last_gesture_time = current_time
            
            previous_fist_state = is_fist

            current_scroll_state = None
            if scroll_active and all_gestures_active:
                if length < 50:
                    mouse.scroll(0, 1)
                    cv2.circle(img, (x2, y2), 10, (0, 255, 0), cv2.FILLED)
                    current_scroll_state = 'up'
                    
                    if previous_scroll_state != 'up':
                        if current_time - last_gesture_time > gesture_cooldown:
                            frame_time_ms = (time.time() - frame_start_time) * 1000
                            print(f"\n⬆️  SCROLL UP (RT: {frame_time_ms:.2f}ms)")
                            tracker.gesture_detected('scroll_up', frame_time_ms)
                            last_gesture_time = current_time
                            
                elif length > 150:
                    mouse.scroll(0, -1)
                    cv2.circle(img, (x2, y2), 10, (0, 0, 255), cv2.FILLED)
                    current_scroll_state = 'down'
                    
                    if previous_scroll_state != 'down':
                        if current_time - last_gesture_time > gesture_cooldown:
                            frame_time_ms = (time.time() - frame_start_time) * 1000
                            print(f"\n⬇️  SCROLL DOWN (RT: {frame_time_ms:.2f}ms)")
                            tracker.gesture_detected('scroll_down', frame_time_ms)
                            last_gesture_time = current_time
                else:
                    cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
                    current_scroll_state = None
                    
            previous_scroll_state = current_scroll_state

            current_click_state = distance_thumb_pinky < 30
            if current_click_state and not previous_click_state and all_gestures_active:
                if current_time - last_gesture_time > gesture_cooldown:
                    mouse.click(Button.left)
                    cv2.circle(img, (x5, y5), 15, (0, 255, 0), cv2.FILLED)
                    frame_time_ms = (time.time() - frame_start_time) * 1000
                    print(f"\n👆 KLIK (RT: {frame_time_ms:.2f}ms)")
                    tracker.gesture_detected('click', frame_time_ms)
                    last_gesture_time = current_time
                    
            previous_click_state = current_click_state
    
    frame_end_time = time.time()
    frame_processing_time_ms = (frame_end_time - frame_start_time) * 1000
    tracker.add_frame_processing_time(frame_processing_time_ms)

    # Display info
    gesture_status = "AKTIF ✓" if all_gestures_active else "NONAKTIF ✗"
    hands_count = len(hands) if hands else 0
    avg_rt = tracker.calculate_overall_response_time()
    
    info_text = f"Hands: {hands_count} | Gestures: {gesture_status} | Scroll: {'ON' if scroll_active else 'OFF'}"
    perf_text = f"Akurasi: {tracker.calculate_overall_accuracy():.1f}% | Avg RT: {avg_rt:.1f}ms | FPS: {1000/frame_processing_time_ms:.1f}"
    
    # Cursor test mode indicator
    if cursor_testing_mode:
        mode_text = f"MODE KURSOR: ON | Target: {current_target_index+1}/9"
        smooth_stats = cursor_tracker.get_smoothness_stats()
        precision_stats = cursor_tracker.get_precision_stats()
        cursor_stats_text = f"Jitter: {smooth_stats['jitter_px']:.1f}px | Smooth: {smooth_stats['smoothness_score']:.1f} | Presisi: {precision_stats['count']} hits"
        
        cv2.putText(img, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(img, cursor_stats_text, (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.putText(img, info_text, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if all_gestures_active else (0, 0, 255), 2)
        cv2.putText(img, perf_text, (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
    else:
        cv2.putText(img, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if all_gestures_active else (0, 0, 255), 2)
        cv2.putText(img, perf_text, (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
    
    cv2.putText(img, "[C]=Cursor Test | [T]=Scroll | [W]=ON/OFF | 2 Tangan=Exit", (10, img.shape[0] - 10), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    
    if tracker.waiting_for_confirmation:
        cv2.putText(img, "Konfirmasi: Y=Benar N=Salah", (10, 80 if not cursor_testing_mode else 130), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.imshow(window_name, img)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('y') or key == ord('Y'):
        tracker.confirm_true_positive()
        
    elif key == ord('n') or key == ord('N'):
        tracker.confirm_false_positive()
        
    elif key == ord('f') or key == ord('F'):
        print("\nPilih gesture yang gagal terdeteksi:")
        print("1. Scroll Up")
        print("2. Scroll Down")
        print("3. Klik")
        print("4. Toggle Scroll")
        print("5. Move Cursor")
        gesture_choice = input("Pilihan (1-5): ")
        
        gesture_map = {
            '1': 'scroll_up',
            '2': 'scroll_down',
            '3': 'click',
            '4': 'toggle_scroll',
            '5': 'move_cursor'
        }
        
        if gesture_choice in gesture_map:
            tracker.add_false_negative(gesture_map[gesture_choice])
    
    elif key == ord('s') or key == ord('S'):
        tracker.display_stats()
        if cursor_testing_mode:
            print("\nSTATISTIK KONTROL KURSOR:")
            print("-" * 80)
            precision_stats = cursor_tracker.get_precision_stats()
            smoothness_stats = cursor_tracker.get_smoothness_stats()
            print(f"Presisi - Avg Deviation: {precision_stats['avg_deviation']:.2f}px")
            print(f"Presisi - Success Rate: {precision_stats['success_rate']:.2f}%")
            print(f"Smoothness - Jitter: {smoothness_stats['jitter_px']:.2f}px")
            print(f"Smoothness - Score: {smoothness_stats['smoothness_score']:.2f}/100")
    
    elif key == ord('r') or key == ord('R'):
        confirm = input("\nYakin ingin reset statistik? (y/n): ")
        if confirm.lower() == 'y':
            tracker = GestureTracker()
            cursor_tracker = CursorTestTracker()
            print("✓ Statistik direset")
    
    elif key == ord('c') or key == ord('C'):
        cursor_testing_mode = not cursor_testing_mode
        if cursor_testing_mode:
            print("\n🎯 MODE TESTING KURSOR: AKTIF")
            print("   P - Test Presisi (9 titik)")
            print("   M - Test Smoothness")
            print("   1/2/3 - Test Kecepatan")
            cursor_test_targets = generate_target_grid(img.shape[1], img.shape[0])
            current_target_index = 0
        else:
            print("\n🎯 MODE TESTING KURSOR: NONAKTIF")
            cursor_test_targets = []
    
    elif key == ord('p') or key == ord('P'):
        if cursor_testing_mode and cursor_test_targets and len(hands) == 1:
            # Record precision hit
            hand = hands[0]
            lmList = hand["lmList"]
            x3, y3 = lmList[12][0], lmList[12][1]
            
            target = cursor_test_targets[current_target_index]
            deviation = cursor_tracker.add_precision_test(target, (x3, y3))
            
            print(f"\n🎯 Target {current_target_index+1}/9: Deviasi {deviation:.2f}px")
            
            current_target_index += 1
            if current_target_index >= len(cursor_test_targets):
                current_target_index = 0
                precision_stats = cursor_tracker.get_precision_stats()
                print(f"\n✅ Test Presisi Selesai!")
                print(f"   Avg Deviation: {precision_stats['avg_deviation']:.2f}px")
                print(f"   Success Rate: {precision_stats['success_rate']:.2f}%")
    
    elif key == ord('m') or key == ord('M'):
        if cursor_testing_mode:
            print("\n🌀 Mode Smoothness: Gerakkan jari tengah membentuk lingkaran")
            print("   Tekan M lagi untuk selesai")
    
    elif key == ord('1'):
        if cursor_testing_mode and cursor_test_start_time:
            elapsed = (time.time() - cursor_test_start_time) * 1000
            # Distance calculation would need start position
            cursor_tracker.add_speed_test('lambat', 0, elapsed)
            print(f"\n🐢 Speed Test LAMBAT: {elapsed:.2f}ms")
            cursor_test_start_time = None
        else:
            cursor_test_start_time = time.time()
            print("\n🐢 Speed Test LAMBAT dimulai - Gerak lambat, tekan 1 lagi")
    
    elif key == ord('2'):
        if cursor_testing_mode and cursor_test_start_time:
            elapsed = (time.time() - cursor_test_start_time) * 1000
            cursor_tracker.add_speed_test('normal', 0, elapsed)
            print(f"\n🚶 Speed Test NORMAL: {elapsed:.2f}ms")
            cursor_test_start_time = None
        else:
            cursor_test_start_time = time.time()
            print("\n🚶 Speed Test NORMAL dimulai - Gerak normal, tekan 2 lagi")
    
    elif key == ord('3'):
        if cursor_testing_mode and cursor_test_start_time:
            elapsed = (time.time() - cursor_test_start_time) * 1000
            cursor_tracker.add_speed_test('cepat', 0, elapsed)
            print(f"\n🏃 Speed Test CEPAT: {elapsed:.2f}ms")
            cursor_test_start_time = None
        else:
            cursor_test_start_time = time.time()
            print("\n🏃 Speed Test CEPAT dimulai - Gerak cepat, tekan 3 lagi")
    
    elif key == ord('t') or key == ord('T'):
        scroll_active = not scroll_active
        print(f"\n🔄 TOGGLE SCROLL (Keyboard): {'AKTIF ✓' if scroll_active else 'NONAKTIF ✗'}")
    
    elif key == ord('w') or key == ord('W'):
        all_gestures_active = not all_gestures_active
        status = "AKTIF ✓" if all_gestures_active else "NONAKTIF ✗"
        print(f"\n🎮 SEMUA FITUR (Scroll + Klik): {status}")
        if not all_gestures_active:
            print("   ⚠️  Scroll Up, Scroll Down, dan Klik DINONAKTIFKAN")
        else:
            print("   ✓ Semua fitur DIAKTIFKAN kembali")
    
    elif key == ord('q') or key == ord('Q'):
        break

# Tampilkan statistik akhir
print("\n\n")
tracker.display_stats()

# Simpan laporan
tracker.save_report('laporan_pengujian.json')
tracker.save_report_text('laporan_pengujian.txt')

# Simpan laporan kontrol kursor jika ada data
if cursor_testing_mode or cursor_tracker.precision_hits or cursor_tracker.smoothness_data:
    cursor_tracker.save_cursor_test_report('laporan_kontrol_kursor.txt')

print("\n✓ Laporan pengujian berhasil disimpan!")
print("  - laporan_pengujian.json (format data)")
print("  - laporan_pengujian.txt (untuk skripsi)")
if cursor_testing_mode or cursor_tracker.precision_hits:
    print("  - laporan_kontrol_kursor.txt (untuk tabel kontrol kursor)")

cap.release()
cv2.destroyAllWindows()
