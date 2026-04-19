const videoEl = document.getElementById('webcam');
const overlay = document.getElementById('overlay');
const statusBadge = document.getElementById('status-badge');

let stream = null;
let isPolling = false;
let mediaRecorder = null;
let audioChunks = [];
let capturedFrameBlob = null;
let currentSessionId = null;

// Audio context stuff
let audioContext, analyser, microphone, scriptProcessor;

async function initCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        videoEl.srcObject = stream;
        
        videoEl.onloadedmetadata = () => {
            overlay.classList.add('hidden');
            startPolling();
        };
    } catch (err) {
        console.error("Camera error:", err);
        overlay.textContent = "Camera/Mic permission denied or unavailable.";
    }
}

function switchPanel(panelId) {
    document.querySelectorAll('.panel-section').forEach(p => p.classList.remove('active'));
    document.getElementById(panelId).classList.add('active');
}

function setStatus(text, type='scanning') {
    statusBadge.textContent = text;
    statusBadge.className = `badge ${type}`;
}

function captureFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = videoEl.videoWidth || 640;
    canvas.height = videoEl.videoHeight || 480;
    canvas.getContext('2d').drawImage(videoEl, 0, 0, canvas.width, canvas.height);
    return new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.9));
}

async function pollOnce() {
    if (!isPolling) return;

    try {
        const frameBlob = await captureFrame();
        const fd = new FormData();
        fd.append('frame', frameBlob, 'frame.jpg');

        const res = await fetch('http://localhost:8000/api/interaction/detect_person', { method: 'POST', body: fd });
        
        if (!res.ok) {
            const errorText = await res.text();
            console.error("Backend error:", res.status, errorText);
            setStatus('API Error: check console', 'recording');
            return;
        }

        const data = await res.json();
        
        if (data.person_detected) {
            isPolling = false;
            capturedFrameBlob = frameBlob; // Save the exact frame
            startRecording();
            return;
        }
    } catch (err) {
        console.error("Polling error / Server Rebooting:", err);
        setStatus('Server offline... Retrying', 'recording');
        // Do not set isPolling = false! Let it retry so it survives watchfiles restarts!
    }

    if (isPolling) {
        setTimeout(pollOnce, 1500);
    }
}

// 1 FPS Polling to detect person
function startPolling() {
    switchPanel('panel-idle');
    setStatus('Scanning for faces...', 'scanning');
    
    isPolling = true;
    pollOnce();
}

function startRecording() {
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    
    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunks.push(e.data);
    };
    
    mediaRecorder.onstop = processInteraction;
    
    mediaRecorder.start();
    switchPanel('panel-recording');
    setStatus('Recording audio...', 'recording');
}

document.getElementById('btn-stop-recording').addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
});

document.getElementById('btn-cancel').addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    // Just reset
    setTimeout(startPolling, 500);
});

async function processInteraction() {
    switchPanel('panel-processing');
    setStatus('Processing...', 'scanning');

    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    
    const fd = new FormData();
    fd.append('userid', 1);
    fd.append('frame', capturedFrameBlob, 'frame.jpg');
    fd.append('audio', audioBlob, 'audio.webm');

    try {
        const res = await fetch('http://localhost:8000/api/interaction/process', { method: 'POST', body: fd });
        const data = await res.json();

        if (!res.ok) {
            alert("Error: " + (data.detail || "Processing failed"));
            startPolling();
            return;
        }

        if (data.status === 'needs_registration') {
            currentSessionId = data.temp_session_id;
            switchPanel('panel-unknown');
            setStatus('Needs Action', 'recording');
        } else {
            showResult(data);
        }

    } catch (err) {
        console.error(err);
        alert("Failed to reach server.");
        startPolling();
    }
}

function showResult(data) {
    switchPanel('panel-result');
    setStatus('Saved to database', 'success');
    
    document.getElementById('result-name').textContent = data.person_name;
    document.getElementById('result-relationship').textContent = data.relationship_type || "N/A";
    document.getElementById('result-match').textContent = data.match_status;
    document.getElementById('result-emotion').textContent = data.emotion;
    document.getElementById('result-transcription').textContent = data.transcription;
    document.getElementById('result-summary').textContent = data.summary;
}

document.getElementById('form-resolve').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('input-name').value;
    const rel = document.getElementById('input-relationship').value;

    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
        const res = await fetch('http://localhost:8000/api/interaction/resolve_unknown', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                userid: 1,
                name: name,
                relationship_type: rel
            })
        });

        const data = await res.json();
        if (res.ok) {
            alert("Registered successfully!");
            startPolling();
        } else {
            alert("Error: " + data.detail);
        }
    } catch (err) {
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.textContent = "Register & Save";
        e.target.reset();
    }
});

document.getElementById('btn-discard').addEventListener('click', () => {
    document.getElementById('form-resolve').reset();
    startPolling();
});

document.getElementById('btn-reset').addEventListener('click', () => {
    startPolling();
});

// Start
initCamera();
