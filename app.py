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
    Fungsi ini membaca gambar dan melakukan analisis 'palsu'
    untuk meniru segmentasi dan pembuatan heatmap.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    # --- 1. Simulasi Segmentasi ---
    # Mengubah gambar ke HSV (Hue, Saturation, Value) agar lebih mudah memfilter warna
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Tentukan rentang warna untuk setiap kelas
    # (Angka-angka ini mungkin perlu disesuaikan tergantung gambar Anda)
    mangrove_lower = np.array([30, 40, 40])
    mangrove_upper = np.array([90, 255, 255])
    water_lower = np.array([90, 50, 50])
    water_upper = np.array([130, 255, 255])
    
    # Buat 'mask' untuk setiap warna
    mangrove_mask = cv2.inRange(hsv, mangrove_lower, mangrove_upper)
    water_mask = cv2.inRange(hsv, water_lower, water_upper)
    
    # Buat gambar output segmentasi
    segmented_img = np.zeros_like(img)
    segmented_img[mangrove_mask > 0] = [0, 255, 0]  # Mangrove -> Hijau
    segmented_img[water_mask > 0] = [255, 0, 0]      # Air -> Biru
    
    # --- 2. Simulasi Heatmap ---
    # Mengubah ke grayscale, di mana area lebih terang dianggap lebih padat
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    heatmap_img = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

    # --- 3. Kalkulasi Data Dummy (berdasarkan hasil mask) ---
    total_pixels = img.shape[0] * img.shape[1]
    mangrove_pixels = cv2.countNonZero(mangrove_mask)
    water_pixels = cv2.countNonZero(water_mask)
    
    mangrove_percentage = (mangrove_pixels / total_pixels) * 100
    water_percentage = (water_pixels / total_pixels) * 100
    land_percentage = 100 - mangrove_percentage - water_percentage

    total_carbon = (mangrove_pixels * 0.015) + ((total_pixels - mangrove_pixels - water_pixels) * 0.003) # Faktor acak

    # --- 4. Simpan gambar hasil analisis ---
    timestamp = int(time.time())
    segmented_filename = f'segmented_{timestamp}.png'
    heatmap_filename = f'heatmap_{timestamp}.png'
    
    cv2.imwrite(os.path.join(RESULT_FOLDER, segmented_filename), segmented_img)
    cv2.imwrite(os.path.join(RESULT_FOLDER, heatmap_filename), heatmap_img)

    # --- 5. Siapkan data untuk dikirim kembali ---
    analysis_data = {
        "segmented_image_url": f"/results/{segmented_filename}",
        "heatmap_image_url": f"/results/{heatmap_filename}",
        "total_stock": round(total_carbon),
        "composition": {
            "mangrove": round(mangrove_percentage, 2),
            "water": round(water_percentage, 2),
            "land": round(land_percentage, 2)
        },
        "total_area": round(total_pixels / 10000, 2) # Asumsi kasar
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
