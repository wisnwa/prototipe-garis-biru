import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time
import uuid
import threading # Library untuk menjalankan tugas di latar belakang

# --- IMPORT FUNGSI AI KITA ---
from ai_model import segment_image_with_ai

# --- Konfigurasi Server ---
app = Flask(__name__, static_folder='results')
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app)

RESULT_FOLDER = 'results'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# --- 'DATABASE' SEMENTARA UNTUK MELACAK TUGAS ---
# Dalam aplikasi nyata, ini akan menjadi database seperti Redis atau lainnya.
tasks = {}

# --- FUNGSI ANALISIS GAMBAR (SEKARANG BERJALAN DI THREAD) ---
def run_analysis_in_background(task_id, filepath, original_filename):
    print(f"Starting analysis for task_id: {task_id}")
    try:
        # Panggil model AI (ini adalah bagian yang lama)
        segmented_img, pred_seg = segment_image_with_ai(filepath)
        if segmented_img is None:
            tasks[task_id] = {"status": "failed", "error": "AI model failed"}
            return

        # Proses heatmap
        mangrove_mask = (pred_seg == 3).astype(np.uint8) * 255
        heatmap_base = np.zeros_like(mangrove_mask)
        heatmap_base[mangrove_mask > 0] = 255
        heatmap_inverted = cv2.bitwise_not(heatmap_base)
        heatmap_img = cv2.applyColorMap(heatmap_inverted, cv2.COLORMAP_JET)

        # Kalkulasi data
        total_pixels = pred_seg.size
        mangrove_pixels = np.count_nonzero(pred_seg == 3)
        water_pixels = np.count_nonzero(pred_seg == 12)
        land_pixels = np.count_nonzero(pred_seg == 17)
        mangrove_percentage = (mangrove_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        water_percentage = (water_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        land_percentage = (land_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        total_carbon = (mangrove_pixels * 0.015) + (land_pixels * 0.003)

        # Simpan gambar hasil
        timestamp = int(time.time())
        segmented_filename = f'segmented_{timestamp}.png'
        heatmap_filename = f'heatmap_{timestamp}.png'
        cv2.imwrite(os.path.join(RESULT_FOLDER, segmented_filename), segmented_img)
        cv2.imwrite(os.path.join(RESULT_FOLDER, heatmap_filename), heatmap_img)
        
        # Simpan hasil akhir ke 'database' tugas
        tasks[task_id]['result'] = {
            "original_image_url": f"/uploads/{original_filename}",
            "segmented_image_url": f"/results/{segmented_filename}",
            "heatmap_image_url": f"/results/{heatmap_filename}",
            "total_stock": round(total_carbon),
            "composition": {"mangrove": round(mangrove_percentage, 2), "water": round(water_percentage, 2), "land": round(land_percentage, 2)},
            "total_area": round(total_pixels / 10000, 2)
        }
        tasks[task_id]['status'] = 'completed'
        print(f"Completed analysis for task_id: {task_id}")

    except Exception as e:
        print(f"Error in background task for {task_id}: {e}")
        tasks[task_id] = {"status": "failed", "error": str(e)}


# --- API ENDPOINT BARU ---

# 1. Endpoint untuk memulai analisis
@app.route('/start-analysis', methods=['POST'])
def start_analysis():
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    
    # Buat ID unik untuk tugas ini
    task_id = str(uuid.uuid4())
    
    # Simpan file
    safe_filename = "".join([c for c in file.filename if c.isalpha() or c.isdigit() or c in ['.', '_']]).rstrip()
    original_filename = f"original_{task_id}_{safe_filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    file.save(filepath)
    
    # Catat tugas baru sebagai 'pending'
    tasks[task_id] = {"status": "pending"}

    # Jalankan fungsi analisis di background thread
    thread = threading.Thread(target=run_analysis_in_background, args=(task_id, filepath, original_filename))
    thread.start()
    
    # Langsung kirim kembali task_id ke frontend
    return jsonify({"task_id": task_id})

# 2. Endpoint untuk mengecek status analisis
@app.route('/check-status/<task_id>', methods=['GET'])
def check_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "not_found"}), 404
    return jsonify(task)

# Endpoint untuk menyajikan gambar
@app.route('/uploads/<filename>')
def serve_upload_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/results/<filename>')
def serve_result_image(filename):
    return send_from_directory(RESULT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
