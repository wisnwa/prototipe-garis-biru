from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import cv2

# --- Inisialisasi Model ---
# Model akan diunduh secara otomatis saat pertama kali dijalankan dan disimpan di cache
# Kita menggunakan model SegFormer dari NVIDIA yang sudah dilatih pada dataset ADE20K
model_name = "nvidia/segformer-b0-finetuned-ade-512-512"
processor = AutoImageProcessor.from_pretrained(model_name)
model = AutoModelForSemanticSegmentation.from_pretrained(model_name)

def get_ade20k_colors():
    """
    Fungsi helper untuk membuat palet warna yang sesuai dengan kelas model ADE20K.
    Ini membantu kita memvisualisasikan hasil segmentasi.
    """
    # ADE20K memiliki 150 kelas. Kita buat palet warna acak untuknya.
    palette = np.random.randint(0, 255, size=(150, 3), dtype=np.uint8)
    # Beberapa kelas penting kita definisikan warnanya secara manual
    palette[0] = [0, 0, 0]      # Latar belakang -> Hitam
    palette[3] = [0, 255, 0]    # Pohon/Vegetasi -> Hijau
    palette[12] = [255, 0, 0]   # Air -> Biru
    palette[17] = [0, 255, 255] # Pasir -> Kuning
    return palette

def segment_image_with_ai(image_path):
    """
    Fungsi utama untuk melakukan segmentasi menggunakan model AI dari Hugging Face.
    """
    try:
        # 1. Buka gambar
        image = Image.open(image_path).convert("RGB")

        # 2. Siapkan gambar untuk model (preprocessing)
        inputs = processor(images=image, return_tensors="pt")

        # 3. Lakukan prediksi (inference)
        with torch.no_grad():
            outputs = model(**inputs)
        
        logits = outputs.logits.cpu()

        # 4. Proses output model menjadi gambar segmentasi yang bisa dilihat
        # Logits diubah menjadi peta prediksi kelas (ukuran H x W)
        upsampled_logits = F.interpolate(
            logits,
            size=image.size[::-1], # (lebar, tinggi)
            mode="bilinear",
            align_corners=False,
        )
        pred_seg = upsampled_logits.argmax(dim=1)[0].numpy()

        # 5. Beri warna pada setiap kelas prediksi
        color_seg = np.zeros((pred_seg.shape[0], pred_seg.shape[1], 3), dtype=np.uint8)
        palette = get_ade20k_colors()

        for label, color in enumerate(palette):
            color_seg[pred_seg == label, :] = color

        # 6. Konversi kembali ke format yang bisa disimpan oleh OpenCV
        # PIL menggunakan RGB, OpenCV menggunakan BGR
        color_seg_bgr = cv2.cvtColor(color_seg, cv2.COLOR_RGB2BGR)

        return color_seg_bgr, pred_seg
        
    except Exception as e:
        print(f"Error during AI segmentation: {e}")
        return None, None