import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time

# --- Konfigurasi Server ---
app = Flask(__name__, static_folder='results')
CORS(app) # Mengizinkan komunikasi antara frontend dan backend

# Menentukan folder untuk menyimpan gambar
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# --- FUNGSI ANALISIS GAMBAR (SIMULASI AI DENGAN OPENCV) ---

def analyze_image(image_path):
    """
    Fungsi analisis yang disempurnakan.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # --- 1. Segmentasi yang Lebih Baik ---
    # Rentang untuk Mangrove/Vegetasi (Hijau)
    mangrove_lower = np.array([30, 40, 20])
    mangrove_upper = np.array([90, 255, 255])
    mangrove_mask = cv2.inRange(hsv, mangrove_lower, mangrove_upper)

    # Rentang untuk Daratan/Tanah (Kuning/Coklat)
    land_lower = np.array([15, 50, 50])
    land_upper = np.array([30, 255, 255])
    land_mask = cv2.inRange(hsv, land_lower, land_upper)
    
    # Gabungkan mask darat dan mangrove
    non_water_mask = cv2.bitwise_or(mangrove_mask, land_mask)
    
    # Air adalah semua yang BUKAN darat atau mangrove
    water_mask = cv2.bitwise_not(non_water_mask)
    
    # Buat gambar output segmentasi
    segmented_img = np.zeros_like(img)
    segmented_img[water_mask > 0] = [255, 0, 0]      # Air -> Biru
    segmented_img[land_mask > 0] = [0, 255, 255]      # Darat -> Kuning
    segmented_img[mangrove_mask > 0] = [0, 255, 0]  # Mangrove -> Hijau
    
    # --- 2. Simulasi Heatmap (Berdasarkan Vegetasi) ---
    # Heatmap sekarang berdasarkan di mana ada mangrove (lebih logis)
    # Area mangrove akan biru tua, sisanya akan lebih terang
    heatmap_base = np.zeros(img.shape[:2], dtype=np.uint8)
    # Beri nilai tinggi (putih) pada area mangrove
    heatmap_base[mangrove_mask > 0] = 255 
    heatmap_img = cv2.applyColorMap(heatmap_base, cv2.COLORMAP_JET)

    # --- 3. Kalkulasi Data (Lebih Akurat) ---
    total_pixels = img.shape[0] * img.shape[1]
    mangrove_pixels = cv2.countNonZero(mangrove_mask)
    water_pixels = cv2.countNonZero(water_mask)
    land_pixels = cv2.countNonZero(land_mask)
    
    # Normalisasi persentase
    total_classified = mangrove_pixels + water_pixels + land_pixels
    mangrove_percentage = (mangrove_pixels / total_classified) * 100 if total_classified > 0 else 0
    water_percentage = (water_pixels / total_classified) * 100 if total_classified > 0 else 0
    land_percentage = (land_pixels / total_classified) * 100 if total_classified > 0 else 0

    total_carbon = (mangrove_pixels * 0.015) + (land_pixels * 0.003)

    # --- 4. Simpan gambar hasil analisis ---
    timestamp = int(time.time())
    original_filename = f'original_{timestamp}.png'
    segmented_filename = f'segmented_{timestamp}.png'
    heatmap_filename = f'heatmap_{timestamp}.png'
    
    # Simpan juga file original yang diupload untuk referensi
    cv2.imwrite(os.path.join(UPLOAD_FOLDER, original_filename), img)
    cv2.imwrite(os.path.join(RESULT_FOLDER, segmented_filename), segmented_img)
    cv2.imwrite(os.path.join(RESULT_FOLDER, heatmap_filename), heatmap_img)

    # --- 5. Siapkan data untuk dikirim kembali ---
    analysis_data = {
        # Tambahkan URL untuk gambar original
        "original_image_url": f"/uploads/{original_filename}", 
        "segmented_image_url": f"/results/{segmented_filename}",
        "heatmap_image_url": f"/results/{heatmap_filename}",
        "total_stock": round(total_carbon),
        "composition": {
            "mangrove": round(mangrove_percentage, 2),
            "water": round(water_percentage, 2),
            "land": round(land_percentage, 2)
        },
        "total_area": round(total_pixels / 10000, 2)
    }

    return analysis_data

# --- API ENDPOINT ---
# Ini adalah alamat URL yang akan dihubungi oleh JavaScript
@app.route('/analyze', methods=['POST'])
def handle_analysis():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Simpan file yang diunggah
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Jalankan fungsi analisis
        try:
            data = analyze_image(filepath)
            if data is None:
                return jsonify({"error": "Could not read image"}), 500
            
            # Kirim kembali data hasil analisis dalam format JSON
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Endpoint untuk menyajikan gambar dari folder 'results'
@app.route('/results/<filename>')
def serve_result_image(filename):
    return send_from_directory(RESULT_FOLDER, filename)


# --- Menjalankan Server ---
if __name__ == '__main__':
    # Server akan berjalan di http://127.0.0.1:5000
    app.run(debug=True, port=5000)
