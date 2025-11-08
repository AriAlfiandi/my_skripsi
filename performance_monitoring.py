"""
Script Monitoring Performa Sistem Virtual Mouse
Mengukur FPS, CPU Usage, Memory Usage, dan Response Time
"""

from cvzone.HandTrackingModule import HandDetector
import cv2
import math
from pynput.mouse import Button, Controller
import screeninfo
import time
import psutil
import json
from datetime import datetime

# Inisialisasi mouse controller
mouse = Controller()

# Mendapatkan informasi resolusi layar
screen = screeninfo.get_monitors()[0]
screen_width, screen_height = screen.width, screen.height

# Inisialisasi kamera
cap = cv2.VideoCapture(0)

# Inisialisasi hand detector
detector = HandDetector(detectionCon=0.3, maxHands=1)

# Variabel untuk menyimpan status scroll aktif/nonaktif
scroll_active = True

# ============= PERFORMANCE MONITORING =============
class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.frame_count = 0
        self.fps_list = []
        self.cpu_list = []
        self.memory_list = []
        self.response_times = []
        self.last_fps_time = time.time()
        self.current_fps = 0
        
    def update_frame(self):
        """Update hitungan frame"""
        self.frame_count += 1
        current_time = time.time()
        
        # Hitung FPS setiap detik
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.fps_list.append(self.current_fps)
            
            # Catat CPU dan Memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            
            self.cpu_list.append(cpu_percent)
            self.memory_list.append(memory_mb)
            
            # Reset counter
            self.frame_count = 0
            self.last_fps_time = current_time
            
            # Tampilkan di terminal
            print(f"\rFPS: {self.current_fps:.1f} | CPU: {cpu_percent:.1f}% | "
                  f"Memory: {memory_mb:.1f}MB ({memory_percent:.1f}%)", end='')
    
    def add_response_time(self, response_time):
        """Tambah waktu response"""
        self.response_times.append(response_time)
    
    def get_statistics(self):
        """Dapatkan statistik performa"""
        duration = time.time() - self.start_time
        
        stats = {
            'duration_seconds': duration,
            'duration_minutes': duration / 60,
            'fps': {
                'average': sum(self.fps_list) / len(self.fps_list) if self.fps_list else 0,
                'min': min(self.fps_list) if self.fps_list else 0,
                'max': max(self.fps_list) if self.fps_list else 0
            },
            'cpu': {
                'average': sum(self.cpu_list) / len(self.cpu_list) if self.cpu_list else 0,
                'min': min(self.cpu_list) if self.cpu_list else 0,
                'max': max(self.cpu_list) if self.cpu_list else 0
            },
            'memory_mb': {
                'average': sum(self.memory_list) / len(self.memory_list) if self.memory_list else 0,
                'min': min(self.memory_list) if self.memory_list else 0,
                'max': max(self.memory_list) if self.memory_list else 0
            },
            'response_time_ms': {
                'average': (sum(self.response_times) / len(self.response_times) * 1000) 
                          if self.response_times else 0,
                'min': min(self.response_times) * 1000 if self.response_times else 0,
                'max': max(self.response_times) * 1000 if self.response_times else 0
            }
        }
        
        return stats
    
    def display_statistics(self):
        """Tampilkan statistik di terminal"""
        stats = self.get_statistics()
        
        print("\n\n" + "="*80)
        print("STATISTIK PERFORMA SISTEM".center(80))
        print("="*80)
        
        print(f"\nDurasi Monitoring: {stats['duration_minutes']:.2f} menit")
        
        print("\n" + "-"*80)
        print("FRAME RATE (FPS)")
        print("-"*80)
        print(f"  Rata-rata : {stats['fps']['average']:.2f} fps")
        print(f"  Minimum   : {stats['fps']['min']:.2f} fps")
        print(f"  Maximum   : {stats['fps']['max']:.2f} fps")
        print(f"  Status    : {'✓ BAIK (>20fps)' if stats['fps']['average'] > 20 else '✗ KURANG'}")
        
        print("\n" + "-"*80)
        print("CPU USAGE")
        print("-"*80)
        print(f"  Rata-rata : {stats['cpu']['average']:.2f}%")
        print(f"  Minimum   : {stats['cpu']['min']:.2f}%")
        print(f"  Maximum   : {stats['cpu']['max']:.2f}%")
        print(f"  Status    : {'✓ BAIK (<50%)' if stats['cpu']['average'] < 50 else '✗ TINGGI'}")
        
        print("\n" + "-"*80)
        print("MEMORY USAGE")
        print("-"*80)
        print(f"  Rata-rata : {stats['memory_mb']['average']:.2f} MB")
        print(f"  Minimum   : {stats['memory_mb']['min']:.2f} MB")
        print(f"  Maximum   : {stats['memory_mb']['max']:.2f} MB")
        print(f"  Status    : {'✓ BAIK (<500MB)' if stats['memory_mb']['average'] < 500 else '✗ TINGGI'}")
        
        print("\n" + "-"*80)
        print("RESPONSE TIME")
        print("-"*80)
        print(f"  Rata-rata : {stats['response_time_ms']['average']:.2f} ms")
        print(f"  Minimum   : {stats['response_time_ms']['min']:.2f} ms")
        print(f"  Maximum   : {stats['response_time_ms']['max']:.2f} ms")
        print(f"  Status    : {'✓ BAIK (<100ms)' if stats['response_time_ms']['average'] < 100 else '✗ LAMBAT'}")
        
        print("\n" + "="*80 + "\n")
    
    def save_report(self, filename='laporan_performa.json'):
        """Simpan laporan ke file JSON"""
        stats = self.get_statistics()
        
        report = {
            'waktu_pengujian': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'durasi_detik': stats['duration_seconds'],
            'durasi_menit': stats['duration_minutes'],
            'fps': stats['fps'],
            'cpu_usage': stats['cpu'],
            'memory_usage_mb': stats['memory_mb'],
            'response_time_ms': stats['response_time_ms']
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=4)
        
        print(f"✓ Laporan performa disimpan: {filename}")
    
    def save_report_text(self, filename='laporan_performa.txt'):
        """Simpan laporan ke file TXT"""
        stats = self.get_statistics()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("LAPORAN PERFORMA SISTEM VIRTUAL MOUSE\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Waktu Pengujian: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}\n")
            f.write(f"Durasi: {stats['duration_minutes']:.2f} menit\n\n")
            
            f.write("HASIL PENGUKURAN:\n")
            f.write("-"*80 + "\n\n")
            
            # FPS
            f.write("1. FRAME RATE (FPS)\n")
            f.write(f"   Rata-rata: {stats['fps']['average']:.2f} fps\n")
            f.write(f"   Minimum  : {stats['fps']['min']:.2f} fps\n")
            f.write(f"   Maximum  : {stats['fps']['max']:.2f} fps\n")
            f.write(f"   Target   : >20 fps\n")
            f.write(f"   Status   : {'✓ Tercapai' if stats['fps']['average'] > 20 else '✗ Tidak Tercapai'}\n\n")
            
            # CPU
            f.write("2. CPU USAGE\n")
            f.write(f"   Rata-rata: {stats['cpu']['average']:.2f}%\n")
            f.write(f"   Minimum  : {stats['cpu']['min']:.2f}%\n")
            f.write(f"   Maximum  : {stats['cpu']['max']:.2f}%\n")
            f.write(f"   Target   : <50%\n")
            f.write(f"   Status   : {'✓ Tercapai' if stats['cpu']['average'] < 50 else '✗ Tidak Tercapai'}\n\n")
            
            # Memory
            f.write("3. MEMORY USAGE\n")
            f.write(f"   Rata-rata: {stats['memory_mb']['average']:.2f} MB\n")
            f.write(f"   Minimum  : {stats['memory_mb']['min']:.2f} MB\n")
            f.write(f"   Maximum  : {stats['memory_mb']['max']:.2f} MB\n")
            f.write(f"   Target   : <500 MB\n")
            f.write(f"   Status   : {'✓ Tercapai' if stats['memory_mb']['average'] < 500 else '✗ Tidak Tercapai'}\n\n")
            
            # Response Time
            f.write("4. RESPONSE TIME\n")
            f.write(f"   Rata-rata: {stats['response_time_ms']['average']:.2f} ms\n")
            f.write(f"   Minimum  : {stats['response_time_ms']['min']:.2f} ms\n")
            f.write(f"   Maximum  : {stats['response_time_ms']['max']:.2f} ms\n")
            f.write(f"   Target   : <100 ms\n")
            f.write(f"   Status   : {'✓ Tercapai' if stats['response_time_ms']['average'] < 100 else '✗ Tidak Tercapai'}\n\n")
            
            # Tabel untuk skripsi
            f.write("\n" + "="*80 + "\n")
            f.write("TABEL UNTUK SKRIPSI:\n")
            f.write("-"*80 + "\n\n")
            
            f.write("Tabel: Hasil Pengujian Performa Sistem\n\n")
            f.write("+-------------------------+----------------+----------+----------+\n")
            f.write("| Metrik                  | Nilai          | Target   | Status   |\n")
            f.write("+-------------------------+----------------+----------+----------+\n")
            f.write(f"| Frame Rate (FPS)        | {stats['fps']['average']:.2f} fps       ")
            f.write(f"| >20 fps  | {'✓ Baik' if stats['fps']['average'] > 20 else '✗ Kurang':8} |\n")
            f.write(f"| CPU Usage               | {stats['cpu']['average']:.2f}%          ")
            f.write(f"| <50%     | {'✓ Baik' if stats['cpu']['average'] < 50 else '✗ Tinggi':8} |\n")
            f.write(f"| Memory Usage            | {stats['memory_mb']['average']:.0f} MB         ")
            f.write(f"| <500 MB  | {'✓ Baik' if stats['memory_mb']['average'] < 500 else '✗ Tinggi':8} |\n")
            f.write(f"| Response Time           | {stats['response_time_ms']['average']:.0f} ms          ")
            f.write(f"| <100 ms  | {'✓ Baik' if stats['response_time_ms']['average'] < 100 else '✗ Lambat':8} |\n")
            f.write("+-------------------------+----------------+----------+----------+\n")
            
            f.write("\n" + "="*80 + "\n")
        
        print(f"✓ Laporan text disimpan: {filename}")

# Inisialisasi performance monitor
perf_monitor = PerformanceMonitor()

# Variabel untuk tracking gesture
last_gesture_time = time.time()
gesture_cooldown = 0.5
previous_scroll_state = None
previous_click_state = False
previous_fist_state = False

print("\n" + "="*80)
print("MONITORING PERFORMA SISTEM VIRTUAL MOUSE".center(80))
print("="*80)
print("\nPETUNJUK:")
print("  • Gunakan sistem seperti biasa")
print("  • Monitor akan berjalan otomatis")
print("  • Tekan [Q] untuk berhenti dan lihat hasil")
print("="*80 + "\n")

while True:
    success, img = cap.read()
    if not success:
        break

    # Flip gambar
    img = cv2.flip(img, 1)

    # Deteksi tangan
    gesture_start_time = time.time()
    hands, img = detector.findHands(img)
    
    current_time = time.time()
    
    if hands:
        hand = hands[0]
        lmList = hand["lmList"]
        if lmList:
            # Koordinat jari
            x1, y1 = lmList[4][0], lmList[4][1]  # Jempol
            x2, y2 = lmList[8][0], lmList[8][1]  # Telunjuk
            x5, y5 = lmList[20][0], lmList[20][1]  # Kelingking

            # Hitung jarak
            length = math.hypot(x2 - x1, y2 - y1)
            distance_thumb_pinky = math.hypot(x5 - x1, y5 - y1)

            # Gambar
            cv2.circle(img, (x1, y1), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x5, y5), 5, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.line(img, (x1, y1), (x5, y5), (255, 0, 255), 3)

            # Gerakkan mouse
            screen_x = int(x2 * screen_width / img.shape[1])
            screen_y = int(y2 * screen_height / img.shape[0])
            mouse.position = (screen_x, screen_y)

            # Deteksi kepal
            is_fist = all(math.hypot(lmList[i][0] - lmList[0][0], 
                                    lmList[i][1] - lmList[0][1]) < 40 
                         for i in [4, 8, 12, 16, 20])

            if is_fist and not previous_fist_state:
                if current_time - last_gesture_time > gesture_cooldown:
                    scroll_active = not scroll_active
                    response_time = time.time() - gesture_start_time
                    perf_monitor.add_response_time(response_time)
                    last_gesture_time = current_time
            
            previous_fist_state = is_fist

            # Scroll
            current_scroll_state = None
            if scroll_active:
                if length < 50:
                    mouse.scroll(0, 1)
                    current_scroll_state = 'up'
                    
                    if previous_scroll_state != 'up':
                        if current_time - last_gesture_time > gesture_cooldown:
                            response_time = time.time() - gesture_start_time
                            perf_monitor.add_response_time(response_time)
                            last_gesture_time = current_time
                            
                elif length > 150:
                    mouse.scroll(0, -1)
                    current_scroll_state = 'down'
                    
                    if previous_scroll_state != 'down':
                        if current_time - last_gesture_time > gesture_cooldown:
                            response_time = time.time() - gesture_start_time
                            perf_monitor.add_response_time(response_time)
                            last_gesture_time = current_time
                    
            previous_scroll_state = current_scroll_state

            # Klik
            current_click_state = distance_thumb_pinky < 30
            if current_click_state and not previous_click_state:
                if current_time - last_gesture_time > gesture_cooldown:
                    mouse.click(Button.left)
                    response_time = time.time() - gesture_start_time
                    perf_monitor.add_response_time(response_time)
                    last_gesture_time = current_time
                    
            previous_click_state = current_click_state

    # Update frame count untuk FPS
    perf_monitor.update_frame()

    # Tampilkan info di frame
    cv2.putText(img, f"FPS: {perf_monitor.current_fps:.1f}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Tampilkan frame
    cv2.imshow("Performance Monitoring", img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Tampilkan statistik
perf_monitor.display_statistics()

# Simpan laporan
perf_monitor.save_report('laporan_performa.json')
perf_monitor.save_report_text('laporan_performa.txt')

print("\n✓ Monitoring selesai! File laporan tersimpan.")

# Cleanup
cap.release()
cv2.destroyAllWindows()
