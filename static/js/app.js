async function checkDocument() {
    const fileInput = document.getElementById('pdfFile');
    const studentName = document.getElementById('studentName').value;
    const studentId = document.getElementById('studentId').value;

    
    if (!fileInput.files[0]) {
        alert('Silakan pilih file PDF terlebih dahulu');
        return;
    }
    
    if (!studentName || !studentId) {
        alert('Silakan lengkapi informasi mahasiswa');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Show loading
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    
    try {
        // Convert to base64
        const base64String = await fileToBase64(file);
        
        // Prepare request data
        const requestData = {
            document_base64: base64String,
            student_info: {
                name: studentName,
                student_id: studentId,
            }
        };
        
        // Send request
        const response = await fetch('/api/check-document', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        // Hide loading
        document.getElementById('loading').classList.add('hidden');
        
        if (result.success) {
            displayResults(result.result);
        } else {
            displayError(result.error);
        }
        
    } catch (error) {
        document.getElementById('loading').classList.add('hidden');
        displayError('Terjadi kesalahan: ' + error.message);
    }
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

function displayResults(result) {
    const resultsDiv = document.getElementById('results');
    const contentDiv = document.getElementById('resultContent');
    const analysis = result.format_analysis;

    const score = analysis.overall_score || 0;
    const scoreClass = score > 80 ? 'status-pass' : 'status-fail';

    // Pastikan array tidak undefined
    const pageIssues = (analysis.page_issues || result.format_analysis.page_issues || []);
    const recommendations = analysis.recommendations || [];
    const masalahPuebi = analysis.masalah_puebi || [];

    contentDiv.innerHTML = `
        <div class="result-summary ${scoreClass}">
            <div class="score">Skor: ${score}/100</div>
        </div>
        <div class="result-details">
            <div class="section">
                <h4>📄 Detail Halaman/Bagian Bermasalah</h4>
                ${pageIssues.length > 0 ?
                    '<ul>' + pageIssues.map(i => `<li>Halaman/Bagian: ${i.page || i.section || '-'} - ${i.issue}</li>`).join('') + '</ul>' :
                    '<p class="success">✅ Tidak ada masalah pada halaman/bagian spesifik</p>'
                }
            </div>
            <div class="section">
                <h4>💡 Saran & Rekomendasi (termasuk PUEBI)</h4>
                <ul>
                    ${[...recommendations, ...masalahPuebi].map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
    resultsDiv.classList.remove('hidden');
}

function displayError(error) {
    const resultsDiv = document.getElementById('results');
    const contentDiv = document.getElementById('resultContent');
    
    contentDiv.innerHTML = `
        <div class="error">
            <h4>❌ Terjadi Kesalahan</h4>
            <p>${error}</p>
        </div>
    `;
    
    resultsDiv.classList.remove('hidden');
}