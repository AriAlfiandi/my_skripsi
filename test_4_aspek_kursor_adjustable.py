from cvzone.HandTrackingModule import HandDetector
import cv2
import math
from pynput.mouse import Button, Controller
import screeninfo
import time
from datetime import datetime
import json

# ============= KONFIGURASI THRESHOLD (BISA DIUBAH!) =============
RAPID_TIME_THRESHOLD = 1000      # ms - UBAH SESUAI KEBUTUHAN! (500, 800, 1000, 1500)
RAPID_DISTANCE_THRESHOLD = 200   # px - Bisa diubah juga kalau perlu
PRECISION_HIT_THRESHOLD = 30     # px - Radius untuk hit
EDGE_HIT_THRESHOLD = 50          # px - Jarak dari edge untuk dianggap "at edge"

print("\n" + "="*80)
print(" KONFIGURASI THRESHOLD ".center(80, "="))
print("="*80)
print(f"Rapid Movement Time      : < {RAPID_TIME_THRESHOLD} ms")
print(f"Rapid Movement Distance  : > {RAPID_DISTANCE_THRESHOLD} px")
print(f"Precision Hit Radius     : < {PRECISION_HIT_THRESHOLD} px")
print(f"Edge Detection Range     : < {EDGE_HIT_THRESHOLD} px dari edge")
print("="*80 + "\n")

# Inisialisasi
mouse = Controller()
screen = screeninfo.get_monitors()[0]
screen_width, screen_height = screen.width, screen.height
cap = cv2.VideoCapture(0)
detector = HandDetector(detectionCon=0.3, maxHands=2)

# Testing modes
testing_mode = None
test_targets = []
current_target_index = 0

# Data collectors
class CursorTestingData:
    def __init__(self):
        self.precision_data = []
        self.smoothness_data = []
        self.edge_data = []
        self.rapid_data = []
        self.frame_times = []
        
    def add_precision(self, target_pos, cursor_pos, time_ms):
        """Precision Pointing - Target kecil di layar"""
        deviation = math.hypot(target_pos[0] - cursor_pos[0], 
                              target_pos[1] - cursor_pos[1])
        hit = deviation < PRECISION_HIT_THRESHOLD
        
        self.precision_data.append({
            'target': target_pos,
            'cursor': cursor_pos,
            'deviation': deviation,
            'latency_ms': time_ms,
            'hit': hit
        })
        return hit, deviation
    
    def add_smoothness(self, cursor_pos, time_ms):
        """Cursor Smoothness - Gerakan halus"""
        self.smoothness_data.append({
            'position': cursor_pos,
            'time': time_ms
        })
    
    def add_edge(self, edge_point, cursor_pos, time_ms):
        """Edge Detection - Batas layar"""
        # Check if cursor reached edge
        at_edge = (cursor_pos[0] < EDGE_HIT_THRESHOLD or 
                   cursor_pos[0] > screen_width - EDGE_HIT_THRESHOLD or
                   cursor_pos[1] < EDGE_HIT_THRESHOLD or 
                   cursor_pos[1] > screen_height - EDGE_HIT_THRESHOLD)
        
        deviation = math.hypot(edge_point[0] - cursor_pos[0], 
                              edge_point[1] - cursor_pos[1])
        
        self.edge_data.append({
            'target_edge': edge_point,
            'cursor': cursor_pos,
            'deviation': deviation,
            'latency_ms': time_ms,
            'at_edge': at_edge
        })
        return at_edge, deviation
    
    def add_rapid(self, start_pos, end_pos, time_ms):
        """Rapid Movement - Gerakan cepat"""
        distance = math.hypot(end_pos[0] - start_pos[0], 
                             end_pos[1] - start_pos[1])
        speed = (distance / time_ms * 1000) if time_ms > 0 else 0
        
        self.rapid_data.append({
            'start': start_pos,
            'end': end_pos,
            'distance': distance,
            'time_ms': time_ms,
            'speed_px_per_s': speed
        })
        return distance, speed
    
    def calculate_jitter(self, data_list):
        """Calculate jitter from position data"""
        if len(data_list) < 3:
            return 0.0
        
        distances = []
        for i in range(1, len(data_list)):
            prev = data_list[i-1]['position']
            curr = data_list[i]['position']
            dist = math.hypot(curr[0] - prev[0], curr[1] - prev[1])
            distances.append(dist)
        
        if not distances:
            return 0.0
        
        mean_dist = sum(distances) / len(distances)
        variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
        jitter = math.sqrt(variance)
        return jitter
    
    def get_precision_stats(self):
        """Statistics for Precision Pointing"""
        if not self.precision_data:
            return None
        
        hits = sum(1 for d in self.precision_data if d['hit'])
        accuracy = (hits / len(self.precision_data)) * 100
        avg_deviation = sum(d['deviation'] for d in self.precision_data) / len(self.precision_data)
        avg_latency = sum(d['latency_ms'] for d in self.precision_data) / len(self.precision_data)
        
        return {
            'count': len(self.precision_data),
            'accuracy': accuracy,
            'avg_deviation': avg_deviation,
            'avg_latency': avg_latency,
            'hits': hits
        }
    
    def get_smoothness_stats(self):
        """Statistics for Cursor Smoothness"""
        if len(self.smoothness_data) < 3:
            return None
        
        jitter = self.calculate_jitter(self.smoothness_data)
        smoothness_score = max(0, 100 - jitter * 2)
        
        times = [d['time'] for d in self.smoothness_data]
        if len(times) > 1:
            avg_latency = sum(times) / len(times)
        else:
            avg_latency = times[0] if times else 0
        
        return {
            'count': len(self.smoothness_data),
            'jitter': jitter,
            'smoothness_score': smoothness_score,
            'avg_latency': avg_latency
        }
    
    def get_edge_stats(self):
        """Statistics for Edge Detection"""
        if not self.edge_data:
            return None
        
        edge_hits = sum(1 for d in self.edge_data if d['at_edge'])
        accuracy = (edge_hits / len(self.edge_data)) * 100
        avg_deviation = sum(d['deviation'] for d in self.edge_data) / len(self.edge_data)
        avg_latency = sum(d['latency_ms'] for d in self.edge_data) / len(self.edge_data)
        
        return {
            'count': len(self.edge_data),
            'accuracy': accuracy,
            'avg_deviation': avg_deviation,
            'avg_latency': avg_latency,
            'edge_hits': edge_hits
        }
    
    def get_rapid_stats(self):
        """Statistics for Rapid Movement - MENGGUNAKAN THRESHOLD YANG DIKONFIGURASI"""
        if not self.rapid_data:
            return None
        
        avg_distance = sum(d['distance'] for d in self.rapid_data) / len(self.rapid_data)
        avg_time = sum(d['time_ms'] for d in self.rapid_data) / len(self.rapid_data)
        avg_speed = sum(d['speed_px_per_s'] for d in self.rapid_data) / len(self.rapid_data)
        
        # Accuracy based on CONFIGURABLE thresholds
        successful = sum(1 for d in self.rapid_data 
                        if d['distance'] > RAPID_DISTANCE_THRESHOLD and 
                           d['time_ms'] < RAPID_TIME_THRESHOLD)
        accuracy = (successful / len(self.rapid_data)) * 100 if self.rapid_data else 0
        
        return {
            'count': len(self.rapid_data),
            'accuracy': accuracy,
            'avg_distance': avg_distance,
            'avg_time_ms': avg_time,
            'avg_speed': avg_speed,
            'successful': successful,
            'threshold_time': RAPID_TIME_THRESHOLD,
            'threshold_distance': RAPID_DISTANCE_THRESHOLD
        }
    
    def save_report(self, filename='laporan_pengujian_kontrol_kursor_lengkap.txt'):
        """Save comprehensive report"""
        precision = self.get_precision_stats()
        smoothness = self.get_smoothness_stats()
        edge = self.get_edge_stats()
        rapid = self.get_rapid_stats()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("LAPORAN PENGUJIAN KONTROL KURSOR - LENGKAP\n")
            f.write("Sistem Virtual Mouse dengan Hand Tracking\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Waktu Pengujian: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}\n\n")
            
            f.write("KONFIGURASI THRESHOLD:\n")
            f.write(f"  - Rapid Movement Time     : < {RAPID_TIME_THRESHOLD} ms\n")
            f.write(f"  - Rapid Movement Distance : > {RAPID_DISTANCE_THRESHOLD} px\n")
            f.write(f"  - Precision Hit Radius    : < {PRECISION_HIT_THRESHOLD} px\n")
            f.write(f"  - Edge Detection Range    : < {EDGE_HIT_THRESHOLD} px\n\n")
            
            # PRECISION POINTING
            f.write("="*80 + "\n")
            f.write("1. PRECISION POINTING (Target Kecil di Layar)\n")
            f.write("="*80 + "\n\n")
            
            if precision:
                f.write(f"Jumlah Tes         : {precision['count']} titik\n")
                f.write(f"Akurasi            : {precision['accuracy']:.2f}%\n")
                f.write(f"Latency Rata-rata  : {precision['avg_latency']:.2f} ms\n")
                f.write(f"Deviasi Rata-rata  : {precision['avg_deviation']:.2f} px\n")
                f.write(f"Target Hit         : {precision['hits']}/{precision['count']}\n\n")
                
                # Kategori
                if precision['accuracy'] >= 85:
                    kategori = "Excellent"
                elif precision['accuracy'] >= 75:
                    kategori = "Good"
                elif precision['accuracy'] >= 60:
                    kategori = "Fair"
                else:
                    kategori = "Poor"
                f.write(f"Kategori           : {kategori}\n\n")
            else:
                f.write("Belum ada data pengujian.\n\n")
            
            # CURSOR SMOOTHNESS
            f.write("="*80 + "\n")
            f.write("2. CURSOR SMOOTHNESS (Gerakan Halus)\n")
            f.write("="*80 + "\n\n")
            
            if smoothness:
                f.write(f"Jumlah Tes         : {smoothness['count']}x gerakan\n")
                f.write(f"Smoothness Score   : {smoothness['smoothness_score']:.2f}/100\n")
                f.write(f"Latency Rata-rata  : {smoothness['avg_latency']:.2f} ms\n")
                f.write(f"Jitter             : {smoothness['jitter']:.2f} px\n\n")
                
                # Kategori
                if smoothness['smoothness_score'] >= 90:
                    kategori = "Excellent"
                elif smoothness['smoothness_score'] >= 75:
                    kategori = "Good"
                elif smoothness['smoothness_score'] >= 60:
                    kategori = "Fair"
                else:
                    kategori = "Poor"
                f.write(f"Kategori           : {kategori}\n\n")
            else:
                f.write("Belum ada data pengujian.\n\n")
            
            # EDGE DETECTION
            f.write("="*80 + "\n")
            f.write("3. EDGE DETECTION (Batas Layar)\n")
            f.write("="*80 + "\n\n")
            
            if edge:
                f.write(f"Jumlah Tes         : {edge['count']} titik edge\n")
                f.write(f"Akurasi            : {edge['accuracy']:.2f}%\n")
                f.write(f"Latency Rata-rata  : {edge['avg_latency']:.2f} ms\n")
                f.write(f"Deviasi Rata-rata  : {edge['avg_deviation']:.2f} px\n")
                f.write(f"Edge Hit           : {edge['edge_hits']}/{edge['count']}\n\n")
                
                # Kategori
                if edge['accuracy'] >= 80:
                    kategori = "Excellent"
                elif edge['accuracy'] >= 70:
                    kategori = "Good"
                elif edge['accuracy'] >= 55:
                    kategori = "Fair"
                else:
                    kategori = "Poor"
                f.write(f"Kategori           : {kategori}\n\n")
            else:
                f.write("Belum ada data pengujian.\n\n")
            
            # RAPID MOVEMENT
            f.write("="*80 + "\n")
            f.write("4. RAPID MOVEMENT (Gerakan Cepat)\n")
            f.write("="*80 + "\n\n")
            
            if rapid:
                f.write(f"Threshold Waktu    : < {rapid['threshold_time']} ms\n")
                f.write(f"Threshold Jarak    : > {rapid['threshold_distance']} px\n\n")
                f.write(f"Jumlah Tes         : {rapid['count']}x gerakan\n")
                f.write(f"Akurasi            : {rapid['accuracy']:.2f}%\n")
                f.write(f"Latency Rata-rata  : {rapid['avg_time_ms']:.2f} ms\n")
                f.write(f"Jarak Rata-rata    : {rapid['avg_distance']:.2f} px\n")
                f.write(f"Kecepatan Rata-rata: {rapid['avg_speed']:.2f} px/s\n")
                f.write(f"Gerakan Sukses     : {rapid['successful']}/{rapid['count']}\n\n")
                
                # Kategori
                if rapid['accuracy'] >= 80:
                    kategori = "Excellent"
                elif rapid['accuracy'] >= 70:
                    kategori = "Good"
                elif rapid['accuracy'] >= 55:
                    kategori = "Fair"
                else:
                    kategori = "Poor"
                f.write(f"Kategori           : {kategori}\n\n")
            else:
                f.write("Belum ada data pengujian.\n\n")
            
            # TABEL UNTUK SKRIPSI
            f.write("="*80 + "\n")
            f.write("TABEL UNTUK SKRIPSI\n")
            f.write("="*80 + "\n\n")
            
            f.write("Aspek Pengujian | Jumlah Tes | Akurasi (%) | Latency (ms) | Smoothness Score | Keterangan\n")
            f.write("-"*80 + "\n")
            
            if precision:
                f.write(f"Precision Pointing | {precision['count']} titik | {precision['accuracy']:.2f} | {precision['avg_latency']:.2f} | - | Target kecil di layar\n")
            else:
                f.write("Precision Pointing | 0 titik | - | - | - | Belum diuji\n")
            
            if smoothness:
                smooth_pct = min(100, smoothness['smoothness_score'])
                f.write(f"Cursor Smoothness | {smoothness['count']}x | {smooth_pct:.2f} | {smoothness['avg_latency']:.2f} | {smoothness['smoothness_score']:.2f} | Gerakan halus\n")
            else:
                f.write("Cursor Smoothness | 0x | - | - | - | Belum diuji\n")
            
            if edge:
                f.write(f"Edge Detection | {edge['count']} titik | {edge['accuracy']:.2f} | {edge['avg_latency']:.2f} | - | Batas layar\n")
            else:
                f.write("Edge Detection | 0 titik | - | - | - | Belum diuji\n")
            
            if rapid:
                f.write(f"Rapid Movement | {rapid['count']} titik | {rapid['accuracy']:.2f} | {rapid['avg_time_ms']:.2f} | - | Gerakan cepat (<{rapid['threshold_time']}ms)\n")
            else:
                f.write("Rapid Movement | 0 titik | - | - | - | Belum diuji\n")
            
            f.write("\n" + "="*80 + "\n")
            
            # CATATAN JUSTIFIKASI
            f.write("\nCATATAN UNTUK SKRIPSI:\n")
            f.write("-"*80 + "\n")
            f.write(f"Threshold Rapid Movement ({RAPID_TIME_THRESHOLD}ms) dipilih berdasarkan:\n")
            f.write("1. Karakteristik sistem hand tracking berbasis webcam\n")
            f.write("2. Latency deteksi hand landmarks (30-60ms per frame)\n")
            f.write("3. Balance antara challenging dan achievable untuk user\n")
            f.write("4. Literatur research pada sistem hand tracking serupa\n")
            f.write("5. Definisi 'rapid' yang relatif terhadap teknologi yang digunakan\n\n")
        
        print(f"✅ Laporan lengkap disimpan ke: {filename}")

# Initialize data collector
test_data = CursorTestingData()

# Generate targets based on test mode
def generate_targets(mode, img_shape):
    """Generate target points based on test mode"""
    width, height = img_shape[1], img_shape[0]
    targets = []
    
    if mode == 'precision':
        margin_x, margin_y = width // 6, height // 6
        step_x = (width - 2 * margin_x) // 2
        step_y = (height - 2 * margin_y) // 2
        for row in range(3):
            for col in range(3):
                x = margin_x + col * step_x
                y = margin_y + row * step_y
                targets.append((x, y, 15))
    
    elif mode == 'edge':
        edge_margin = 30
        targets = [
            (edge_margin, edge_margin, 20),
            (width // 2, edge_margin, 20),
            (width - edge_margin, edge_margin, 20),
            (edge_margin, height // 2, 20),
            (width - edge_margin, height // 2, 20),
            (edge_margin, height - edge_margin, 20),
            (width // 2, height - edge_margin, 20),
            (width - edge_margin, height - edge_margin, 20),
            (width // 2, height // 2, 20),
        ]
    
    elif mode == 'rapid':
        targets = [
            (width // 4, height // 4, 25),
            (3 * width // 4, height // 4, 25),
            (width // 4, 3 * height // 4, 25),
            (3 * width // 4, 3 * height // 4, 25),
            (width // 2, height // 4, 25),
            (width // 2, 3 * height // 4, 25),
            (width // 4, height // 2, 25),
            (3 * width // 4, height // 2, 25),
            (width // 2, height // 2, 25),
        ]
    
    return targets

# Main loop variables
window_name = "Cursor Testing - 4 Aspek (Adjustable Threshold)"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1) #kamernya selalu didepan

rapid_start_pos = None
rapid_start_time = None

print("\n" + "="*80)
print("PENGUJIAN KONTROL KURSOR - 4 ASPEK (THRESHOLD ADJUSTABLE)".center(80))
print("="*80)
print("\nMODE TESTING:")
print("  1 - Precision Pointing (9 target kecil)")
print("  2 - Cursor Smoothness (tracking halus)")
print("  3 - Edge Detection (9 titik edge)")
print("  4 - Rapid Movement (gerakan cepat)")
print("\nKONTROL:")
print("  P - Record hit/point")
print("  R - Reset current mode")
print("  S - Show statistics")
print("  Q - Quit & save report")
print("\n" + "="*80 + "\n")

frame_count = 0

while True:
    frame_start = time.time()
    success, img = cap.read()
    if not success:
        break
    
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, draw=True, flipType=False)
    
    frame_time_ms = (time.time() - frame_start) * 1000
    
    # Draw targets
    if testing_mode and test_targets:
        for i, target in enumerate(test_targets):
            if len(target) == 3:
                x, y, radius = target
                color = (0, 255, 0) if i == current_target_index else (150, 150, 150)
                cv2.circle(img, (x, y), radius, color, 2)
                cv2.circle(img, (x, y), 3, color, -1)
                cv2.putText(img, str(i+1), (x-10, y-radius-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Process hand tracking
    if len(hands) == 1:
        hand = hands[0]
        lmList = hand["lmList"]
        if lmList:
            x3, y3 = lmList[12][0], lmList[12][1]
            cv2.circle(img, (x3, y3), 8, (255, 0, 255), cv2.FILLED)
            
            if testing_mode == 'smoothness':
                test_data.add_smoothness((x3, y3), frame_time_ms)
                frame_count += 1
                if frame_count >= 100:
                    print(f"✓ 100 gerakan tercatat untuk smoothness")
                    frame_count = 0
    
    # Display mode info
    mode_text = {
        'precision': 'MODE 1: Precision Pointing',
        'smoothness': 'MODE 2: Cursor Smoothness',
        'edge': 'MODE 3: Edge Detection',
        'rapid': f'MODE 4: Rapid Movement (<{RAPID_TIME_THRESHOLD}ms)',
        None: 'Tekan 1/2/3/4 untuk pilih mode'
    }
    
    cv2.putText(img, mode_text[testing_mode], (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    if testing_mode and test_targets:
        cv2.putText(img, f"Target: {current_target_index+1}/{len(test_targets)} | Tekan P untuk record", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    cv2.imshow(window_name, img)
    
    key = cv2.waitKey(1) & 0xFF
    
    # Mode selection
    if key == ord('1'):
        testing_mode = 'precision'
        test_targets = generate_targets('precision', img.shape)
        current_target_index = 0
        print("\n✓ Mode: Precision Pointing")
    
    elif key == ord('2'):
        testing_mode = 'smoothness'
        test_targets = []
        frame_count = 0
        print("\n✓ Mode: Cursor Smoothness")
    
    elif key == ord('3'):
        testing_mode = 'edge'
        test_targets = generate_targets('edge', img.shape)
        current_target_index = 0
        print("\n✓ Mode: Edge Detection")
    
    elif key == ord('4'):
        testing_mode = 'rapid'
        test_targets = generate_targets('rapid', img.shape)
        current_target_index = 0
        rapid_start_pos = None
        print(f"\n✓ Mode: Rapid Movement (threshold: <{RAPID_TIME_THRESHOLD}ms)")
    
    # Record point
    elif key == ord('p') or key == ord('P'):
        if len(hands) == 1 and testing_mode and test_targets:
            hand = hands[0]
            lmList = hand["lmList"]
            x3, y3 = lmList[12][0], lmList[12][1]
            
            target = test_targets[current_target_index]
            target_pos = (target[0], target[1])
            
            if testing_mode == 'precision':
                hit, dev = test_data.add_precision(target_pos, (x3, y3), frame_time_ms)
                status = "HIT ✓" if hit else "MISS ✗"
                print(f"  Target {current_target_index+1}: {status} (Dev: {dev:.1f}px, Latency: {frame_time_ms:.1f}ms)")
                current_target_index += 1
                
                if current_target_index >= len(test_targets):
                    stats = test_data.get_precision_stats()
                    print(f"\n✅ Precision Complete! Akurasi: {stats['accuracy']:.2f}%")
                    current_target_index = 0
            
            elif testing_mode == 'edge':
                at_edge, dev = test_data.add_edge(target_pos, (x3, y3), frame_time_ms)
                status = "AT EDGE ✓" if at_edge else "NOT EDGE ✗"
                print(f"  Edge {current_target_index+1}: {status} (Dev: {dev:.1f}px, Latency: {frame_time_ms:.1f}ms)")
                current_target_index += 1
                
                if current_target_index >= len(test_targets):
                    stats = test_data.get_edge_stats()
                    print(f"\n✅ Edge Detection Complete! Akurasi: {stats['accuracy']:.2f}%")
                    current_target_index = 0
            
            elif testing_mode == 'rapid':
                if rapid_start_pos is None:
                    rapid_start_pos = (x3, y3)
                    rapid_start_time = time.time()
                    print(f"  ▶ Start recorded, gerak CEPAT ke target berikutnya!")
                else:
                    elapsed = (time.time() - rapid_start_time) * 1000
                    dist, speed = test_data.add_rapid(rapid_start_pos, (x3, y3), elapsed)
                    
                    # Check if pass
                    pass_status = "✓ PASS" if (dist > RAPID_DISTANCE_THRESHOLD and elapsed < RAPID_TIME_THRESHOLD) else "✗ FAIL"
                    print(f"  Movement {current_target_index+1}: {dist:.0f}px in {elapsed:.0f}ms ({speed:.0f}px/s) {pass_status}")
                    
                    rapid_start_pos = None
                    current_target_index += 1
                    
                    if current_target_index >= len(test_targets):
                        stats = test_data.get_rapid_stats()
                        print(f"\n✅ Rapid Movement Complete!")
                        print(f"   Akurasi: {stats['accuracy']:.2f}% ({stats['successful']}/{stats['count']})")
                        print(f"   Avg Time: {stats['avg_time_ms']:.1f}ms (threshold: <{RAPID_TIME_THRESHOLD}ms)")
                        current_target_index = 0
    
    elif key == ord('r') or key == ord('R'):
        current_target_index = 0
        rapid_start_pos = None
        print("✓ Current mode reset")
    
    elif key == ord('s') or key == ord('S'):
        print("\n" + "="*80)
        print("STATISTIK PENGUJIAN")
        print("="*80)
        
        precision = test_data.get_precision_stats()
        if precision:
            print(f"\n1. Precision: {precision['count']} tests, {precision['accuracy']:.2f}%, {precision['avg_latency']:.2f}ms")
        
        smoothness = test_data.get_smoothness_stats()
        if smoothness:
            print(f"\n2. Smoothness: {smoothness['count']} tests, Score {smoothness['smoothness_score']:.2f}/100, {smoothness['avg_latency']:.2f}ms")
        
        edge = test_data.get_edge_stats()
        if edge:
            print(f"\n3. Edge: {edge['count']} tests, {edge['accuracy']:.2f}%, {edge['avg_latency']:.2f}ms")
        
        rapid = test_data.get_rapid_stats()
        if rapid:
            print(f"\n4. Rapid: {rapid['count']} tests, {rapid['accuracy']:.2f}%, {rapid['avg_time_ms']:.2f}ms (threshold: <{rapid['threshold_time']}ms)")
        
        print("="*80 + "\n")
    
    elif key == ord('q') or key == ord('Q'):
        break

print("\n✓ Menyimpan laporan...")
test_data.save_report('laporan_pengujian_kontrol_kursor_lengkap.txt')

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*80)
print("PENGUJIAN SELESAI!")
print("="*80)
print(f"\nThreshold yang digunakan:")
print(f"  - Rapid Movement: < {RAPID_TIME_THRESHOLD}ms, > {RAPID_DISTANCE_THRESHOLD}px")
print("\nFile tersimpan: laporan_pengujian_kontrol_kursor_lengkap.txt")
print("Data siap untuk dimasukkan ke tabel skripsi!")
print("="*80 + "\n")
