async function checkDocument() {
    const fileInput = document.getElementById('pdfFile');
    const studentName = document.getElementById('studentName').value;
    const studentId = document.getElementById('studentId').value;
    const degree = document.getElementById('degree').value;
    
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
                degree: degree
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
    const compliance = analysis.compliance_status;
    
    let statusClass = '';
    let statusIcon = '';
    
    switch(compliance) {
        case 'PASS':
            statusClass = 'status-pass';
            statusIcon = '✅';
            break;
        case 'FAIL':
            statusClass = 'status-fail';
            statusIcon = '❌';
            break;
        default:
            statusClass = 'status-revision';
            statusIcon = '⚠️';
    }
    
    contentDiv.innerHTML = `
        <div class="result-summary ${statusClass}">
            <h4>${statusIcon} Status: ${compliance}</h4>
            <div class="score">Skor: ${analysis.overall_score}/100</div>
        </div>
        
        <div class="result-details">
            <div class="section">
                <h4>📋 Bagian yang Hilang</h4>
                ${analysis.missing_sections.length > 0 ? 
                    '<ul>' + analysis.missing_sections.map(s => `<li>${s}</li>`).join('') + '</ul>' :
                    '<p class="success">✅ Semua bagian wajib ditemukan</p>'
                }
            </div>
            
            <div class="section">
                <h4>⚠️ Masalah Format</h4>
                ${analysis.format_issues.length > 0 ?
                    '<ul>' + analysis.format_issues.map(i => `<li>${i}</li>`).join('') + '</ul>' :
                    '<p class="success">✅ Tidak ada masalah format ditemukan</p>'
                }
            </div>
            
            <div class="section">
                <h4>💡 Rekomendasi Perbaikan</h4>
                <ul>
                    ${analysis.recommendations.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
            
            <div class="section">
                <h4>📊 Informasi Dokumen</h4>
                <p>Total Halaman: ${result.pdf_metadata.total_pages}</p>
                <p>Check ID: ${result.check_id}</p>
            </div>
            
            <div class="section">
                <h4>📄 Detail Halaman/Bagian Bermasalah</h4>
                ${result.format_analysis.page_issues && result.format_analysis.page_issues.length > 0 ?
                    '<ul>' + result.format_analysis.page_issues.map(i => `<li>Halaman/Bagian: ${i.page || i.section} - ${i.issue}</li>`).join('') + '</ul>' :
                    '<p class="success">✅ Tidak ada masalah pada halaman/bagian spesifik</p>'
                }
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