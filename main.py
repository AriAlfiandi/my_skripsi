from cvzone.HandTrackingModule import HandDetector
import cv2
import math
from pynput.mouse import Button, Controller
import screeninfo
import time

mouse = Controller()
    
screen = screeninfo.get_monitors()[0]
screen_width, screen_height = screen.width, screen.height

print(f"Resolusi layar: {screen_width} x {screen_height}")
print(f"Lebar layar: {screen_width} piksel")
print(f"Tinggi layar: {screen_height} piksel")

cap = cv2.VideoCapture(0)

detector = HandDetector(detectionCon=0.3, maxHands=2)

# Variabel status scroll aktif atau tidak
scroll_active = True
last_click_time = 0  # Waktu klik kiri terakhir
last_right_click_time = 0  # Waktu klik kanan terakhir

# Variabel untuk deteksi kedua tangan terangkat
both_hands_raised_start_time = None
BOTH_HANDS_RAISED_DURATION = 3.0  # 3 detik untuk konfirmasi keluar

# Membuat window bernama "kukuruyuk" agar dapat diatur agar selalu di depan
cv2.namedWindow("kukuruyuk", cv2.WINDOW_NORMAL)

def is_hand_raised(hand_landmarks):
    """
    Mendeteksi apakah tangan terangkat (semua ujung jari di atas pergelangan)
    """
    wrist_y = hand_landmarks[0][1]
    
    fingertip_landmarks = [4, 8, 12, 16, 20]
    
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

print("=== HAND TRACKING MOUSE CONTROL ===")
print("Kontrol:")
print("- Jari tengah: Gerakkan kursor")
print("- Mengepal: Toggle scroll mode")
print("- Jempol + Telunjuk: Scroll (dekat=atas, jauh=bawah)")
print("- Jempol + Kelingking: Klik kiri")
print("- Jempol + Jari manis: Klik kanan")
print("- KEDUA TANGAN TERANGKAT (3 detik): Keluar program")
print("=====================================")

while True:
    success, img = cap.read()
    if not success:
        break

    # Membalik gambar secara horizontal (mirror)
    img = cv2.flip(img, 1)

    # Deteksi tangan
    hands, img = detector.findHands(img)

    # Cek apakah kedua tangan terangkat untuk keluar program
    if check_both_hands_raised(hands):
        current_time = time.time()
        
        if both_hands_raised_start_time is None:
            both_hands_raised_start_time = current_time
            print("Kedua tangan terangkat! Tahan selama 3 detik untuk keluar...")
        
        # Hitung durasi kedua tangan terangkat
        duration = current_time - both_hands_raised_start_time
        
        # Tampilkan countdown di layar
        countdown = max(0, BOTH_HANDS_RAISED_DURATION - duration)
        cv2.putText(img, f"Keluar dalam: {countdown:.1f}s", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if duration >= BOTH_HANDS_RAISED_DURATION:
            print("Keluar program...")
            break
    else:
        both_hands_raised_start_time = None  # Reset timer

    # Proses navigasi hanya jika ada tepat 1 tangan (untuk kontrol)
    if len(hands) == 1:
        hand = hands[0]
        lmList = hand["lmList"]
        if lmList:
            # Landmark jari
            x_thumb, y_thumb = lmList[4][0], lmList[4][1]
            x_index, y_index = lmList[8][0], lmList[8][1]
            x_middle, y_middle = lmList[12][0], lmList[12][1]
            x_ring, y_ring = lmList[16][0], lmList[16][1]
            x_pinky, y_pinky = lmList[20][0], lmList[20][1]

            # Jarak antara jempol dan telunjuk (scroll)
            length_thumb_index = math.hypot(x_index - x_thumb, y_index - y_thumb)

            # Jarak antara jempol dan kelingking (klik kiri)
            distance_thumb_pinky = math.hypot(x_pinky - x_thumb, y_pinky - y_thumb)

            # Jarak antara jempol dan jari manis (klik kanan)
            distance_thumb_ring = math.hypot(x_ring - x_thumb, y_ring - y_thumb)

            # Gambar visualisasi
            cv2.circle(img, (x_thumb, y_thumb), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x_index, y_index), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x_middle, y_middle), 5, (0, 255, 255), cv2.FILLED)
            cv2.circle(img, (x_pinky, y_pinky), 5, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x_ring, y_ring), 5, (0, 255, 0), cv2.FILLED)
            cv2.line(img, (x_thumb, y_thumb), (x_index, y_index), (255, 0, 255), 3)
            cv2.line(img, (x_thumb, y_thumb), (x_pinky, y_pinky), (255, 0, 255), 3)
            cv2.line(img, (x_thumb, y_thumb), (x_ring, y_ring), (0, 255, 0), 3)

            # Konversi koordinat jari tengah ke layar
            screen_x = int(x_middle * screen_width / img.shape[1])
            screen_y = int(y_middle * screen_height / img.shape[0])
            mouse.position = (screen_x, screen_y)

            # Deteksi tangan menggenggam untuk toggle scroll
            is_fist = all(
                math.hypot(lmList[i][0] - lmList[0][0], lmList[i][1] - lmList[0][1]) < 40
                for i in [4, 8, 12, 16, 20]
            )
            if is_fist:
                scroll_active = not scroll_active
                print(f"Scroll active: {scroll_active}")

            # Scroll berdasarkan jarak jempol-telunjuk
            if scroll_active:
                if length_thumb_index < 50:
                    mouse.scroll(0, 1)  # Scroll ke atas
                    cv2.circle(img, (x_index, y_index), 10, (0, 255, 0), cv2.FILLED)
                elif length_thumb_index > 150:
                    mouse.scroll(0, -1)  # Scroll ke bawah
                    cv2.circle(img, (x_index, y_index), 10, (0, 0, 255), cv2.FILLED)
                else:
                    cv2.circle(img, (x_index, y_index), 10, (255, 0, 255), cv2.FILLED)

            # Klik kiri dengan jempol dan kelingking
            if distance_thumb_pinky < 30:
                current_time = cv2.getTickCount() / cv2.getTickFrequency()
                if current_time - last_click_time > 0.5:
                    mouse.click(Button.left)
                    last_click_time = current_time
                    cv2.circle(img, (x_pinky, y_pinky), 15, (0, 255, 0), cv2.FILLED)

            if distance_thumb_ring < 30:
                current_time = cv2.getTickCount() / cv2.getTickFrequency()
                if current_time - last_right_click_time > 0.5:
                    mouse.click(Button.right)
                    last_right_click_time = current_time
                    cv2.circle(img, (x_ring, y_ring), 15, (0, 255, 255), cv2.FILLED)

    # Tampilkan status di layar
    status_text = f"Hands: {len(hands)} | Scroll: {'ON' if scroll_active else 'OFF'}"
    cv2.putText(img, status_text, (10, img.shape[0] - 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Set window agar selalu tampil di atas
    cv2.setWindowProperty("kukuruyuk", cv2.WND_PROP_TOPMOST, 1)

    # Tampilkan hasil deteksi
    cv2.imshow("kukuruyuk", img)
    
    # Backup exit dengan 'q' jika diperlukan
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Lepaskan sumber daya
cap.release()
cv2.destroyAllWindows()
print("Program selesai!")