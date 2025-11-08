"""
Script Analisis Hasil Pengujian Virtual Mouse
Membaca file laporan_pengujian.json dan membuat visualisasi
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def load_report(filename='laporan_pengujian.json'):
    """Membaca file laporan JSON"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {filename} tidak ditemukan!")
        print("Jalankan virtual_mouse_with_testing.py terlebih dahulu.")
        return None

def create_accuracy_chart(report):
    """Membuat chart akurasi per gesture"""
    gestures = list(report['detail_gesture'].keys())
    accuracies = [report['detail_gesture'][g]['akurasi'] for g in gestures]
    
    # Format nama gesture
    gesture_labels = [g.replace('_', ' ').title() for g in gestures]
    
    plt.figure(figsize=(12, 6))
    colors = ['#2ecc71' if acc >= 90 else '#f39c12' if acc >= 80 else '#e74c3c' 
              for acc in accuracies]
    
    bars = plt.bar(gesture_labels, accuracies, color=colors, alpha=0.8, edgecolor='black')
    
    # Tambah nilai di atas bar
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{acc:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.xlabel('Jenis Gesture', fontsize=12, fontweight='bold')
    plt.ylabel('Akurasi (%)', fontsize=12, fontweight='bold')
    plt.title('Akurasi Deteksi per Gesture\nSistem Virtual Mouse', 
              fontsize=14, fontweight='bold')
    plt.ylim(0, 105)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Garis threshold
    plt.axhline(y=90, color='green', linestyle='--', alpha=0.5, label='Target Sangat Baik (90%)')
    plt.axhline(y=80, color='orange', linestyle='--', alpha=0.5, label='Target Baik (80%)')
    
    plt.legend()
    plt.tight_layout()
    plt.savefig('chart_akurasi_per_gesture.png', dpi=300, bbox_inches='tight')
    print("✓ Chart akurasi per gesture disimpan: chart_akurasi_per_gesture.png")
    plt.close()

def create_confusion_metrics_chart(report):
    """Membuat chart metrik confusion (TP, FP, FN)"""
    gestures = list(report['detail_gesture'].keys())
    gesture_labels = [g.replace('_', ' ').title() for g in gestures]
    
    tp_values = [report['detail_gesture'][g]['true_positive'] for g in gestures]
    fp_values = [report['detail_gesture'][g]['false_positive'] for g in gestures]
    fn_values = [report['detail_gesture'][g]['false_negative'] for g in gestures]
    
    x = np.arange(len(gesture_labels))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    bars1 = ax.bar(x - width, tp_values, width, label='True Positive', 
                   color='#2ecc71', alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x, fp_values, width, label='False Positive', 
                   color='#e74c3c', alpha=0.8, edgecolor='black')
    bars3 = ax.bar(x + width, fn_values, width, label='False Negative', 
                   color='#f39c12', alpha=0.8, edgecolor='black')
    
    # Tambah nilai di atas bar
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Jenis Gesture', fontsize=12, fontweight='bold')
    ax.set_ylabel('Jumlah', fontsize=12, fontweight='bold')
    ax.set_title('Perbandingan Metrik Pengujian\nTrue Positive, False Positive, False Negative', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(gesture_labels, rotation=15, ha='right')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig('chart_confusion_metrics.png', dpi=300, bbox_inches='tight')
    print("✓ Chart confusion metrics disimpan: chart_confusion_metrics.png")
    plt.close()

def create_overall_pie_chart(report):
    """Membuat pie chart keseluruhan"""
    total_tp = sum(d['true_positive'] for d in report['detail_gesture'].values())
    total_fp = sum(d['false_positive'] for d in report['detail_gesture'].values())
    total_fn = sum(d['false_negative'] for d in report['detail_gesture'].values())
    
    sizes = [total_tp, total_fp, total_fn]
    labels = [f'True Positive\n({total_tp})', 
              f'False Positive\n({total_fp})', 
              f'False Negative\n({total_fn})']
    colors = ['#2ecc71', '#e74c3c', '#f39c12']
    explode = (0.1, 0, 0)
    
    plt.figure(figsize=(10, 8))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90,
            textprops={'fontsize': 12, 'fontweight': 'bold'})
    
    plt.title(f'Distribusi Hasil Pengujian Keseluruhan\n'
              f'Akurasi Total: {report["akurasi_keseluruhan"]:.2f}%',
              fontsize=14, fontweight='bold', pad=20)
    
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('chart_distribusi_keseluruhan.png', dpi=300, bbox_inches='tight')
    print("✓ Chart distribusi keseluruhan disimpan: chart_distribusi_keseluruhan.png")
    plt.close()

def create_comparison_table_text(report):
    """Membuat tabel perbandingan dalam format text"""
    output = "\n" + "="*90 + "\n"
    output += "TABEL PERBANDINGAN HASIL PENGUJIAN".center(90) + "\n"
    output += "="*90 + "\n\n"
    
    output += f"{'Gesture':<20} {'Detected':>10} {'TP':>8} {'FP':>8} {'FN':>8} {'Akurasi':>12}\n"
    output += "-"*90 + "\n"
    
    total_detected = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for gesture, data in report['detail_gesture'].items():
        gesture_name = gesture.replace('_', ' ').title()
        detected = data['detected']
        tp = data['true_positive']
        fp = data['false_positive']
        fn = data['false_negative']
        acc = data['akurasi']
        
        total_detected += detected
        total_tp += tp
        total_fp += fp
        total_fn += fn
        
        output += f"{gesture_name:<20} {detected:>10} {tp:>8} {fp:>8} {fn:>8} {acc:>11.2f}%\n"
    
    output += "-"*90 + "\n"
    output += f"{'TOTAL':<20} {total_detected:>10} {total_tp:>8} {total_fp:>8} {total_fn:>8} "
    output += f"{report['akurasi_keseluruhan']:>11.2f}%\n"
    output += "="*90 + "\n"
    
    # Informasi tambahan
    output += "\nINFORMASI PENGUJIAN:\n"
    output += "-"*90 + "\n"
    output += f"Waktu Pengujian    : {report['waktu_pengujian']}\n"
    output += f"Durasi Pengujian   : {report['durasi_detik']/60:.2f} menit\n"
    output += f"Total Pengujian    : {total_detected} gesture\n"
    output += f"Tingkat Keberhasilan: {report['akurasi_keseluruhan']:.2f}%\n"
    
    # Analisis
    output += "\nANALISIS SINGKAT:\n"
    output += "-"*90 + "\n"
    
    # Gesture terbaik
    best_gesture = max(report['detail_gesture'].items(), 
                      key=lambda x: x[1]['akurasi'])
    output += f"Gesture Terbaik    : {best_gesture[0].replace('_', ' ').title()} "
    output += f"({best_gesture[1]['akurasi']:.2f}%)\n"
    
    # Gesture terlemah
    worst_gesture = min(report['detail_gesture'].items(), 
                       key=lambda x: x[1]['akurasi'])
    output += f"Perlu Ditingkatkan : {worst_gesture[0].replace('_', ' ').title()} "
    output += f"({worst_gesture[1]['akurasi']:.2f}%)\n"
    
    # Precision dan Recall
    precision = (total_tp / (total_tp + total_fp)) * 100 if (total_tp + total_fp) > 0 else 0
    recall = (total_tp / (total_tp + total_fn)) * 100 if (total_tp + total_fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    output += f"\nMetrik Tambahan:\n"
    output += f"Precision          : {precision:.2f}%\n"
    output += f"Recall             : {recall:.2f}%\n"
    output += f"F1-Score           : {f1_score:.2f}%\n"
    output += "="*90 + "\n"
    
    return output

def generate_analysis_report():
    """Fungsi utama untuk generate semua analisis"""
    print("\n" + "="*80)
    print("ANALISIS HASIL PENGUJIAN VIRTUAL MOUSE".center(80))
    print("="*80 + "\n")
    
    # Load data
    print("Memuat data pengujian...")
    report = load_report()
    
    if report is None:
        return
    
    print(f"✓ Data berhasil dimuat dari laporan_pengujian.json\n")
    
    # Generate visualisasi
    print("Membuat visualisasi...")
    create_accuracy_chart(report)
    create_confusion_metrics_chart(report)
    create_overall_pie_chart(report)
    
    # Generate tabel text
    print("\nMembuat tabel analisis...")
    table_text = create_comparison_table_text(report)
    
    with open('tabel_analisis.txt', 'w', encoding='utf-8') as f:
        f.write(table_text)
    print("✓ Tabel analisis disimpan: tabel_analisis.txt")
    
    # Tampilkan di terminal
    print(table_text)
    
    print("\n" + "="*80)
    print("SEMUA FILE BERHASIL DIBUAT!".center(80))
    print("="*80)
    print("\nFile yang dihasilkan:")
    print("  1. chart_akurasi_per_gesture.png    - Chart akurasi setiap gesture")
    print("  2. chart_confusion_metrics.png      - Chart perbandingan TP/FP/FN")
    print("  3. chart_distribusi_keseluruhan.png - Pie chart distribusi total")
    print("  4. tabel_analisis.txt               - Tabel lengkap untuk skripsi")
    print("\nFile-file ini siap untuk dimasukkan ke dalam skripsi Anda!")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        generate_analysis_report()
    except Exception as e:
        print(f"\nError: {e}")
        print("Pastikan file laporan_pengujian.json tersedia.")
