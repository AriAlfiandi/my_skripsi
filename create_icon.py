from PIL import Image
import sys

def create_icon_from_image(input_path, output_path="icon.ico"):
    """
    Convert gambar PNG/JPG menjadi icon ICO
    """
    try:
        # Buka gambar
        img = Image.open(input_path)
        
        # Resize ke ukuran icon standard (32x32, 64x64, 128x128)
        icon_sizes = [(32, 32), (64, 64), (128, 128)]
        
        # Convert ke RGBA jika belum
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Save sebagai ICO dengan multiple sizes
        img.save(output_path, format='ICO', sizes=icon_sizes)
        
        print(f"✅ Icon berhasil dibuat: {output_path}")
        print(f"📁 Ukuran file: {round(os.path.getsize(output_path)/1024, 2)} KB")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Pastikan file gambar valid (PNG/JPG)")

def create_simple_icon():
    """
    Buat icon mouse sederhana secara programatik
    """
    try:
        # Buat canvas 64x64 dengan background transparan
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        pixels = img.load()
        
        # Gambar mouse sederhana (kotak dengan ekor)
        # Body mouse (kotak rounded)
        for x in range(15, 50):
            for y in range(20, 45):
                if (x-32)**2 + (y-32)**2 < 400:  # Rounded rectangle
                    pixels[x, y] = (100, 100, 100, 255)  # Gray
        
        # Mouse button lines
        for x in range(15, 50):
            pixels[x, 25] = (60, 60, 60, 255)  # Darker gray
        
        # Mouse cord
        for i in range(5):
            pixels[45+i, 35+i] = (80, 80, 80, 255)
        
        # Save as multiple sizes
        icon_sizes = [(16, 16), (32, 32), (64, 64)]
        img.save("icon.ico", format='ICO', sizes=icon_sizes)
        
        print("✅ Icon mouse sederhana berhasil dibuat: icon.ico")
        
    except Exception as e:
        print(f"❌ Error creating simple icon: {e}")

if __name__ == "__main__":
    import os
    
    print("🖱️ VIRTUAL MOUSE - ICON CREATOR")
    print("=" * 40)
    
    # Check if PIL is available
    try:
        from PIL import Image
    except ImportError:
        print("❌ Pillow tidak terinstall!")
        print("Install dengan: pip install Pillow")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("Pilih opsi:")
    print("1. Convert gambar existing ke ICO")
    print("2. Buat icon mouse sederhana")
    
    choice = input("Masukkan pilihan (1/2): ").strip()
    
    if choice == "1":
        image_path = input("Masukkan path gambar (PNG/JPG): ").strip()
        if os.path.exists(image_path):
            create_icon_from_image(image_path)
        else:
            print("❌ File tidak ditemukan!")
    elif choice == "2":
        create_simple_icon()
    else:
        print("❌ Pilihan tidak valid!")
    
    input("\nPress Enter to exit...")