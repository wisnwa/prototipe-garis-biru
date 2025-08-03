document.addEventListener('DOMContentLoaded', () => {

    const imageInput = document.getElementById('image-input');
    const analyzeButton = document.getElementById('analyze-button');
    const imagePreview = document.getElementById('image-preview');

    let uploadedFile = null;
    const BACKEND_URL = 'http://127.0.0.1:5000';

    imageInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadedFile = file;
            imagePreview.src = URL.createObjectURL(file);
        }
    });

    analyzeButton.addEventListener('click', async (event) => {
        event.preventDefault();
        if (!uploadedFile) {
            alert('Silakan pilih gambar terlebih dahulu!');
            return;
        }

        analyzeButton.textContent = 'Mengirim Gambar...';
        analyzeButton.disabled = true;

        const formData = new FormData();
        formData.append('file', uploadedFile);

        try {
            // 1. Kirim gambar ke endpoint BARU untuk memulai analisis
            const startResponse = await fetch(`${BACKEND_URL}/start-analysis`, {
                method: 'POST',
                body: formData,
            });

            if (!startResponse.ok) throw new Error('Failed to start analysis');
            
            const { task_id } = await startResponse.json();
            
            // Tampilkan status baru ke pengguna
            analyzeButton.textContent = 'AI sedang menganalisis... (Mohon tunggu)';
            
            // 2. Mulai mengecek status setiap 3 detik
            checkAnalysisStatus(task_id);

        } catch (error) {
            console.error('Error:', error);
            alert(`Terjadi kesalahan saat memulai analisis: ${error.message}`);
            analyzeButton.textContent = 'Analisis Sekarang';
            analyzeButton.disabled = false;
        }
    });
    
    function checkAnalysisStatus(taskId) {
        const interval = setInterval(async () => {
            try {
                const statusResponse = await fetch(`${BACKEND_URL}/check-status/${taskId}`);
                if (!statusResponse.ok) {
                    clearInterval(interval);
                    throw new Error('Failed to check status');
                }
                
                const task = await statusResponse.json();

                if (task.status === 'completed') {
                    clearInterval(interval); // Hentikan pengecekan
                    analyzeButton.textContent = 'Analisis Selesai!';
                    
                    // Simpan hasil ke sessionStorage dan pindah halaman
                    sessionStorage.setItem('analysisResult', JSON.stringify(task.result));
                    window.location.href = 'result.html';

                } else if (task.status === 'failed') {
                    clearInterval(interval);
                    throw new Error(`Analisis Gagal: ${task.error}`);
                }
                // Jika status masih 'pending', tidak melakukan apa-apa dan lanjut mengecek
                
            } catch (error) {
                clearInterval(interval);
                console.error('Error:', error);
                alert(error.message);
                analyzeButton.textContent = 'Analisis Sekarang';
                analyzeButton.disabled = false;
            }
        }, 3000); // Cek status setiap 3 detik
    }
});
