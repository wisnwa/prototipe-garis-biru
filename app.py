import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time

# --- IMPORT FUNGSI AI KITA DARI FILE ai_model.py ---
from ai_model import segment_image_with_ai

# --- Konfigurasi Server ---
app = Flask(__name__, static_folder='results')
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app)

RESULT_FOLDER = 'results'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# --- FUNGSI ANALISIS GAMBAR (SEKARANG MENGGUNAKAN AI) ---
def analyze_image_new(image_path, original_filename_for_user):
    # --- 1. PANGGIL MODEL AI UNTUK SEGMENTASI ---
    # Fungsi ini sekarang mengembalikan gambar berwarna dan peta prediksi mentah (pred_seg)
    segmented_img, pred_seg = segment_image_with_ai(image_path)
    if segmented_img is None:
        return {"error": "AI model failed to process the image"}

    # --- 2. LOGIKA HEATMAP YANG BENAR BERDASARKAN HASIL AI ---
    # Kelas '3' di dataset ADE20K adalah pohon/vegetasi. Kita buat heatmap dari sini.
    # Buat mask di mana nilai piksel adalah 255 jika kelasnya adalah 3 (pohon), dan 0 jika bukan.
    mangrove_mask = (pred_seg == 3).astype(np.uint8) * 255
    
    # Buat dasar heatmap
    heatmap_base = np.zeros_like(mangrove_mask)
    heatmap_base[mangrove_mask > 0] = 255 # Area mangrove diberi nilai tinggi (putih)
    
    # Balikkan nilainya agar area mangrove menjadi biru tua (karbon tinggi) di colormap JET
    heatmap_inverted = cv2.bitwise_not(heatmap_base)
    heatmap_img = cv2.applyColorMap(heatmap_inverted, cv2.COLORMAP_JET)

    # --- 3. Kalkulasi Data Berdasarkan Hasil AI yang Akurat ---
    total_pixels = pred_seg.size
    # Hitung piksel untuk setiap kelas yang relevan dari peta prediksi (pred_seg)
    # Kelas '3' = Pohon (Mangrove), '12' = Air, '17' = Pasir/Darat
    mangrove_pixels = np.count_nonzero(pred_seg == 3)
    water_pixels = np.count_nonzero(pred_seg == 12)
    land_pixels = np.count_nonzero(pred_seg == 17)

    # Hitung persentase
    mangrove_percentage = (mangrove_pixels / total_pixels) * 100 if total_pixels > 0 else 0
    water_percentage = (water_pixels / total_pixels) * 100 if total_pixels > 0 else 0
    land_percentage = (land_pixels / total_pixels) * 100 if total_pixels > 0 else 0
    
    # Kalkulasi karbon (masih menggunakan faktor sederhana untuk demonstrasi)
    total_carbon = (mangrove_pixels * 0.015) + (land_pixels * 0.003)

    # --- 4. Simpan gambar hasil ---
    timestamp = int(time.time())
    segmented_filename = f'segmented_{timestamp}.png'
    heatmap_filename = f'heatmap_{timestamp}.png'
    
    cv2.imwrite(os.path.join(RESULT_FOLDER, segmented_filename), segmented_img)
    cv2.imwrite(os.path.join(RESULT_FOLDER, heatmap_filename), heatmap_img)

    # --- 5. Siapkan data untuk dikirim kembali ---
    analysis_data = {
        "original_image_url": f"/uploads/{original_filename_for_user}",
        "segmented_image_url": f"/results/{segmented_filename}",
        "heatmap_image_url": f"/results/{heatmap_filename}",
        "total_stock": round(total_carbon),
        "composition": {"mangrove": round(mangrove_percentage, 2), "water": round(water_percentage, 2), "land": round(land_percentage, 2)},
        "total_area": round(total_pixels / 10000, 2) # Asumsi kasar 1 piksel = 1m^2
    }
    return analysis_data

# --- API ENDPOINT ---
@app.route('/analyze', methods=['POST'])
def handle_analysis():
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    
    if file:
        timestamp = int(time.time())
        safe_filename = "".join([c for c in file.filename if c.isalpha() or c.isdigit() or c in ['.', '_']]).rstrip()
        original_filename = f"original_{timestamp}_{safe_filename}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(filepath)

        try:
            # Panggil fungsi analisis yang baru
            data = analyze_image_new(filepath, original_filename)
            if "error" in data: return jsonify(data), 500
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Endpoint untuk menyajikan gambar dari folder 'uploads' dan 'results'
@app.route('/uploads/<filename>')
def serve_upload_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/results/<filename>')
def serve_result_image(filename):
    return send_from_directory(RESULT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
