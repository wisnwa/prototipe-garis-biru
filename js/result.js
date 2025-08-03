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
    
    // Mengambil elemen baru untuk legenda
    const segmentationLegend = document.getElementById('segmentation-legend');
    const heatmapLegend = document.getElementById('heatmap-legend');
    
    // Alamat URL server backend
    const BACKEND_URL = 'http://127.0.0.1:5000';

    // Panggil fungsi untuk mengisi dasbor
    populateDashboard(data);

    function populateDashboard(data) {
        // 1. Isi Gambar Hasil Analisis
        // SEMUA URL sekarang berasal dari 'data' yang dikirim server
        originalImageResult.src = `${BACKEND_URL}${data.original_image_url}`;
        segmentedImageResult.src = `${BACKEND_URL}${data.segmented_image_url}`;
        heatmapImageResult.src = `${BACKEND_URL}${data.heatmap_image_url}`;
        
        // 2. Buat Legenda secara Dinamis
        segmentationLegend.innerHTML = `
            <div class="legend-item"><div class="legend-color-box" style="background-color: #00FF00;"></div><span>Mangrove</span></div>
            <div class="legend-item"><div class="legend-color-box" style="background-color: #0000FF;"></div><span>Perairan</span></div>
            <div class="legend-item"><div class="legend-color-box" style="background-color: #FFD700;"></div><span>Darat Lain</span></div>
        `;
        heatmapLegend.innerHTML = `
            <div class="legend-item"><span>Rendah</span><div class="heatmap-legend-gradient"></div><span>Tinggi</span></div>
        `;

        // 3. Siapkan data untuk diagram dan teks
        const composition = data.composition;
        const totalCarbonStock = data.total_stock;
        
        // Perkirakan stok per kelas dari persentase
        const mangroveStock = totalCarbonStock * (composition.mangrove / 100);
        const landStock = totalCarbonStock * (composition.land / 100);

        // 4. Isi Data Teks
        analysisTimestamp.textContent = `Analisis dibuat pada: ${new Date().toLocaleString('id-ID')}`;
        totalArea.textContent = `${data.total_area} ha (est.)`;
        totalStock.textContent = `${totalCarbonStock.toLocaleString('id-ID')} Ton CO₂e`;
        
        const exchangeRate = 16500;
        valueLow.textContent = `Rp ${(totalCarbonStock * 5 * exchangeRate).toLocaleString('id-ID')}`;
        valueHigh.textContent = `Rp ${(totalCarbonStock * 30 * exchangeRate).toLocaleString('id-ID')}`;

        // 5. Buat Diagram
        renderCharts({
            composition,
            mangroveStock,
            landStock
        });
    }

    function renderCharts(chartData) {
        // Hancurkan chart lama jika ada, untuk membuat yang baru
        const existingCompositionChart = Chart.getChart(compositionChartCanvas);
        if (existingCompositionChart) {
            existingCompositionChart.destroy();
        }
        const existingStockChart = Chart.getChart(stockChartCanvas);
        if (existingStockChart) {
            existingStockChart.destroy();
        }
        
        // Buat diagram komposisi (Pie Chart)
        new Chart(compositionChartCanvas, {
            type: 'pie',
            data: {
                labels: ['Mangrove', 'Perairan', 'Darat Lain'],
                datasets: [{
                    data: [chartData.composition.mangrove, chartData.composition.water, chartData.composition.land],
                    backgroundColor: ['#00FF00', '#0000FF', '#FFD700'],
                    borderColor: '#ffffff',
                    borderWidth: 1
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false // Ini kunci untuk memperbaiki tinggi diagram
            }
        });

        // Buat diagram stok (Bar Chart)
        new Chart(stockChartCanvas, {
            type: 'bar',
            data: {
                labels: ['Mangrove', 'Darat Lain'],
                datasets: [{
                    label: 'Stok Karbon (Ton CO₂e)',
                    data: [chartData.mangroveStock, chartData.landStock],
                    backgroundColor: ['#00FF00', '#FFD700'],
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, // Ini kunci untuk memperbaiki tinggi diagram
                scales: { 
                    y: { 
                        beginAtZero: true 
                    } 
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
});