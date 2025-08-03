document.addEventListener('DOMContentLoaded', () => {
    // Ambil data hasil analisis dari sessionStorage
    const analysisDataString = sessionStorage.getItem('analysisResult');

    // Jika tidak ada data, kembalikan pengguna ke halaman awal
    if (!analysisDataString) {
        alert("Tidak ada data analisis. Silakan unggah gambar terlebih dahulu.");
        window.location.href = 'index.html';
        return;
    }

    const data = JSON.parse(analysisDataString);
    const originalImageURL = sessionStorage.getItem('originalImageURL');

    // --- Mengambil Elemen-elemen dari HTML ---
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
    
    // Alamat URL server backend
    const BACKEND_URL = 'http://127.0.0.1:5000';

    // Panggil fungsi untuk mengisi dasbor
    populateDashboard(data, originalImageURL);

    function populateDashboard(data, originalImageURL) {
        // 1. Isi Gambar Hasil Analisis
        if (originalImageURL) {
            originalImageResult.src = originalImageURL;
        }
        segmentedImageResult.src = `${BACKEND_URL}${data.segmented_image_url}`;
        heatmapImageResult.src = `${BACKEND_URL}${data.heatmap_image_url}`;

        // 2. Siapkan data untuk diagram
        const composition = data.composition;
        const totalCarbonStock = data.total_stock;
        const landCarbon = totalCarbonStock / (1 + (composition.mangrove / composition.land));
        const mangroveCarbon = totalCarbonStock - landCarbon;

        // 3. Isi Data Teks
        analysisTimestamp.textContent = `Analisis dibuat pada: ${new Date().toLocaleString('id-ID')}`;
        totalArea.textContent = `${data.total_area} ha (est.)`;
        totalStock.textContent = `${totalCarbonStock.toLocaleString('id-ID')} Ton CO₂e`;
        
        const exchangeRate = 16500;
        valueLow.textContent = `Rp ${(totalCarbonStock * 5 * exchangeRate).toLocaleString('id-ID')}`;
        valueHigh.textContent = `Rp ${(totalCarbonStock * 30 * exchangeRate).toLocaleString('id-ID')}`;

        // 4. Buat Diagram
        renderCharts({
            composition,
            mangroveCarbon,
            landCarbon
        });
    }

    function renderCharts(chartData) {
        new Chart(compositionChartCanvas, {
            type: 'pie',
            data: {
                labels: ['Mangrove', 'Perairan', 'Darat Lain'],
                datasets: [{
                    data: [chartData.composition.mangrove, chartData.composition.water, chartData.composition.land],
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b'],
                }]
            },
            options: { responsive: true }
        });

        new Chart(stockChartCanvas, {
            type: 'bar',
            data: {
                labels: ['Mangrove', 'Darat Lain'],
                datasets: [{
                    label: 'Stok Karbon (Ton CO₂e)',
                    data: [chartData.mangroveCarbon, chartData.landCarbon],
                    backgroundColor: ['#10b981', '#f59e0b'],
                }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });
    }
});
