document.addEventListener('DOMContentLoaded', () => {

    const imageInput = document.getElementById('image-input');
    const analyzeButton = document.getElementById('analyze-button');
    const imagePreview = document.getElementById('image-preview');
    const dashboardSection = document.getElementById('dashboard-section');
    const analysisTimestamp = document.getElementById('analysis-timestamp');
    const originalImageResult = document.getElementById('original-image-result');
    const segmentedImageResult = document.getElementById('segmented-image-result');
    const heatmapImageResult = document.getElementById('heatmap-image-result');
    const compositionChartCanvas = document.getElementById('composition-chart');
    const stockChartCanvas = document.getElementById('stock-chart');
    const totalArea = document.getElementById('total-area');
    const totalStock = document.getElementById('total-stock');
    const valueLow = document.getElementById('value-low');
    const valueHigh = document.getElementById('value-high');

    let uploadedFile = null;
    let compositionChart = null;
    let stockChart = null;

    // Alamat URL server backend Python Anda
    const BACKEND_URL = 'http://127.0.0.1:5000';

    imageInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadedFile = file; // Simpan file, bukan URL
            imagePreview.src = URL.createObjectURL(file);
        }
    });

    analyzeButton.addEventListener('click', async () => {
        if (!uploadedFile) {
            alert('Silakan pilih gambar terlebih dahulu!');
            return;
        }

        analyzeButton.textContent = 'Mengirim & Menganalisis...';
        analyzeButton.disabled = true;

        // Siapkan data untuk dikirim
        const formData = new FormData();
        formData.append('file', uploadedFile);

        try {
            // Kirim gambar ke backend menggunakan fetch API
            const response = await fetch(`${BACKEND_URL}/analyze`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Server Error: ${response.statusText}`);
            }

            // Terima data hasil analisis dari backend
            const data = await response.json();

            // Tampilkan dasbor dan isi dengan data asli
            dashboardSection.classList.remove('hidden');
            populateDashboard(data);
            dashboardSection.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Error:', error);
            alert(`Terjadi kesalahan saat menghubungi server analisis: ${error.message}`);
        } finally {
            analyzeButton.textContent = 'Analisis Sekarang';
            analyzeButton.disabled = false;
        }
    });

    function populateDashboard(data) {
        // 1. Isi Gambar Hasil Analisis
        // URL.createObjectURL digunakan untuk menampilkan gambar asli yang dipilih pengguna
        originalImageResult.src = URL.createObjectURL(uploadedFile);
        // URL gambar hasil analisis sekarang berasal dari server backend
        segmentedImageResult.src = `${BACKEND_URL}${data.segmented_image_url}`;
        heatmapImageResult.src = `${BACKEND_URL}${data.heatmap_image_url}`;

        // 2. Siapkan data untuk diagram
        const composition = data.composition;
        const totalCarbonStock = data.total_stock;
        const landCarbon = totalCarbonStock / (1 + (composition.mangrove / composition.land)); // Estimasi kasar
        const mangroveCarbon = totalCarbonStock - landCarbon;

        // 3. Isi Data Teks
        analysisTimestamp.textContent = `Analisis dibuat pada: ${new Date().toLocaleString('id-ID')}`;
        totalArea.textContent = `${data.total_area} ha (est.)`;
        totalStock.textContent = `${totalCarbonStock.toLocaleString('id-ID')} Ton CO₂e`;
        
        const exchangeRate = 16500;
        valueLow.textContent = `Rp ${(totalCarbonStock * 5 * exchangeRate).toLocaleString('id-ID')}`;
        valueHigh.textContent = `Rp ${(totalCarbonStock * 30 * exchangeRate).toLocaleString('id-ID')}`;

        // 4. Buat Diagram
        const compositionData = {
            labels: ['Mangrove', 'Perairan', 'Darat Lain'],
            datasets: [{
                data: [composition.mangrove, composition.water, composition.land],
                backgroundColor: ['#10b981', '#3b82f6', '#f59e0b'],
            }]
        };

        const stockData = {
            labels: ['Mangrove', 'Darat Lain'],
            datasets: [{
                label: 'Stok Karbon (Ton CO₂e)',
                data: [mangroveCarbon, landCarbon],
                backgroundColor: ['#10b981', '#f59e0b'],
            }]
        };

        renderCharts(compositionData, stockData);
    }

    function renderCharts(compositionData, stockData) {
        if (compositionChart) compositionChart.destroy();
        if (stockChart) stockChart.destroy();
        
        compositionChart = new Chart(compositionChartCanvas, { type: 'pie', data: compositionData, options: { responsive: true } });
        stockChart = new Chart(stockChartCanvas, { type: 'bar', data: stockData, options: { responsive: true, scales: { y: { beginAtZero: true } } } });
    }
});
