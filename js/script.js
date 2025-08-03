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
        // Mencegah aksi default apapun dari tombol
        event.preventDefault();

        if (!uploadedFile) {
            alert('Silakan pilih gambar terlebih dahulu!');
            return;
        }

        analyzeButton.textContent = 'Mengirim & Menganalisis...';
        analyzeButton.disabled = true;

        const formData = new FormData();
        formData.append('file', uploadedFile);

        try {
            const response = await fetch(`${BACKEND_URL}/analyze`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Server Error: ${response.statusText}`);
            }
            
            const data = await response.json();

            // Simpan hasil dari server ke sessionStorage
            sessionStorage.setItem('analysisResult', JSON.stringify(data));

            // Arahkan pengguna ke halaman hasil
            window.location.href = 'result.html';

        } catch (error) {
            console.error('Error:', error);
            alert(`Terjadi kesalahan saat menghubungi server analisis: ${error.message}`);
            analyzeButton.textContent = 'Analisis Sekarang';
            analyzeButton.disabled = false;
        }
    });
});
