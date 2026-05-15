const cvInput = document.getElementById('cvInput');
const dropZone = document.getElementById('dropZone');
const analyzeBtn = document.getElementById('analyzeBtn');
const uploadSection = document.getElementById('upload-section');
const resultSection = document.getElementById('result-section');
const loading = document.getElementById('loading');
const fileInfo = document.getElementById('fileInfo');
const fileNameText = document.getElementById('fileNameText');


// ======================
// DOSYA SEÇME
// ======================

dropZone.addEventListener('click', () => {
    cvInput.click();
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');

    if (e.dataTransfer.files.length > 0) {
        cvInput.files = e.dataTransfer.files;
        handleFileSelect();
    }
});

cvInput.addEventListener('change', handleFileSelect);

function handleFileSelect() {

    const file = cvInput.files[0];

    if (file && file.type === "application/pdf") {

        fileNameText.innerText = file.name;

        dropZone.classList.add('d-none');
        fileInfo.classList.remove('d-none');

    } else {

        alert("Sadece PDF formatı kabul edilmektedir.");
        cvInput.value = "";
    }
}


// ======================
// BACKEND İSTEĞİ
// ======================

analyzeBtn.addEventListener('click', async () => {

    const file = cvInput.files[0];

    if (!file) return;

    uploadSection.classList.add('d-none');
    loading.classList.remove('d-none');

    const formData = new FormData();
    formData.append('cv', file);

    try {

        const response = await fetch('http://127.0.0.1:5000/analyze-cv', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        console.log("GELEN VERİ:", data);

        if (data.status === 'success') {

            displayResults(data);

        } else {

            alert("Hata: " + data.error);
            location.reload();
        }

    } catch (error) {

        console.error(error);

        alert("Sistem Ağ Geçidi Hatası! app.py çalışıyor mu?");
        location.reload();
    }
});


// ======================
// SONUÇ GÖSTER
// ======================

function displayResults(data) {

    loading.classList.add('d-none');
    resultSection.classList.remove('d-none');

    setTimeout(() => {

        const rawScore = data.score
            ? data.score.toString()
            : "0";

        const targetScore =
            parseInt(rawScore.replace(/\D/g, '')) || 0;

        animateScore(targetScore);

        const analysisBox =
            document.getElementById('analysisResult');

        const jobsBox =
            document.getElementById('jobSuggestions');

        analysisBox.innerHTML =
            renderAnalysis(data.analysis);

        jobsBox.innerHTML =
            renderJobs(data.jobs);

    }, 100);
}


// ======================
// SKOR ANİMASYONU
// ======================

function animateScore(target) {

    let current = 0;

    const scoreElement =
        document.getElementById('cvScore');

    const scoreBar =
        document.getElementById('scoreBar');

    const scoreText =
        document.getElementById('scoreText');

    scoreBar.style.width = target + '%';

    const interval = setInterval(() => {

        if (current >= target) {

            clearInterval(interval);

            current = target;

            if (current >= 80) {

                scoreText.innerHTML =
                    '<span class="text-success">Üst Düzey Eşleşme</span>';

            } else if (current >= 50) {

                scoreText.innerHTML =
                    '<span class="text-warning">Ortalama Potansiyel</span>';

            } else {

                scoreText.innerHTML =
                    '<span class="text-danger">Geliştirilmeli</span>';
            }
        }

        scoreElement.innerText = current;

        current++;

    }, 20);
}


// ======================
// ANALİZ RENDER
// ======================

function renderAnalysis(analysis) {

    if (!analysis) {
        return "Analiz bulunamadı.";
    }

    // STRING GELİRSE
    if (typeof analysis === "string") {

        return formatMarkdown(analysis);
    }

    // OBJECT GELİRSE
    let html = "";

    for (const key in analysis) {

        html += `
            <div class="analysis-group mb-4">
                <h5 class="text-gradient fw-bold mb-3">
                    ${key}
                </h5>
        `;

        if (Array.isArray(analysis[key])) {

            analysis[key].forEach(item => {

                html += `
                    <div class="analysis-item">
                        <i class="bi bi-stars"></i>
                        <span>${item}</span>
                    </div>
                `;
            });

        } else {

            html += `
                <p>${analysis[key]}</p>
            `;
        }

        html += `</div>`;
    }

    return html;
}


// ======================
// JOBS RENDER
// ======================

function renderJobs(jobs) {

    if (!jobs) {
        return "Pozisyon bulunamadı.";
    }

    // STRING GELİRSE
    if (typeof jobs === "string") {

        return formatMarkdown(jobs);
    }

    // ARRAY GELİRSE
    if (Array.isArray(jobs)) {

        let html = "";

        jobs.forEach(job => {

            // OBJECT FORMAT
            if (typeof job === "object") {

                const title =
                    job.position ||
                    job.title ||
                    job.job ||
                    "Pozisyon";

                const desc =
                    job.reason ||
                    job.description ||
                    job.detail ||
                    "";

                html += `
                    <div class="job-card">
                        <h5>${title}</h5>
                        <p>${desc}</p>
                    </div>
                `;

            } else {

                html += `
                    <div class="job-card">
                        ${job}
                    </div>
                `;
            }
        });

        return html;
    }

    // OBJECT GELİRSE
    if (typeof jobs === "object") {

        let html = "";

        for (const key in jobs) {

            html += `
                <div class="job-card">
                    <h5>${key}</h5>
                    <p>${jobs[key]}</p>
                </div>
            `;
        }

        return html;
    }

    return "Pozisyon bulunamadı.";
}


// ======================
// MARKDOWN FORMAT
// ======================

function formatMarkdown(text) {

    if (!text) return "";

    return text

        .replace(/^### (.*$)/gim,
            '<h5 class="text-white mt-4 mb-2 fw-bold">$1</h5>')

        .replace(/^## (.*$)/gim,
            '<h4 class="text-gradient mt-4 mb-3 fw-bold">$1</h4>')

        .replace(/^# (.*$)/gim,
            '<h3 class="text-gradient mt-4 mb-3 fw-bold">$1</h3>')

        .replace(/\*\*(.*?)\*\*/g,
            '<strong class="text-white">$1</strong>')

        .replace(/^\s*[\*\-]\s+(.*)/gm,
            '<div class="analysis-item"><i class="bi bi-stars"></i><span>$1</span></div>')

        .replace(/\n/g, '<br>');
}