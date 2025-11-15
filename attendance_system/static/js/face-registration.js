/**
 * Face Registration Module
 * Handles webcam capture and face registration
 */

let videoStream = null;
let capturedImages = [];
let faceDetectionLoaded = false;

// Initialize face-api.js
async function initializeFaceDetection() {
    try {
        const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/';
        await faceapi.nets.tinyFaceDetector.load(MODEL_URL);
        await faceapi.nets.faceLandmark68Net.load(MODEL_URL);
        await faceapi.nets.faceRecognitionNet.load(MODEL_URL);
        faceDetectionLoaded = true;
        console.log('Face detection models loaded successfully');
    } catch (error) {
        console.error('Error loading face detection models:', error);
        showMessage('Error loading face detection models', 'error');
    }
}

// Start webcam
async function startWebcam() {
    try {
        if (!faceDetectionLoaded) {
            await initializeFaceDetection();
        }

        const video = document.getElementById('webcam');
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            },
            audio: false
        });
        
        video.srcObject = videoStream;
        document.getElementById('webcamPlaceholder').style.display = 'none';
        document.getElementById('startWebcamBtn').style.display = 'none';
        document.getElementById('stopWebcamBtn').style.display = 'inline-block';
        document.getElementById('captureBtn').style.display = 'inline-block';
        
        // Start face detection loop
        detectFacesLoop(video);
        showMessage('Webcam started successfully', 'success');
    } catch (error) {
        console.error('Error accessing webcam:', error);
        showMessage('Unable to access webcam. Please check permissions.', 'error');
    }
}

// Stop webcam
function stopWebcam() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    
    document.getElementById('webcam').srcObject = null;
    document.getElementById('webcamPlaceholder').style.display = 'flex';
    document.getElementById('startWebcamBtn').style.display = 'inline-block';
    document.getElementById('stopWebcamBtn').style.display = 'none';
    document.getElementById('captureBtn').style.display = 'none';
    
    showMessage('Webcam stopped', 'info');
}

// Detect faces in real-time
async function detectFacesLoop(video) {
    if (!videoStream) return;

    try {
        const detections = await faceapi.detectAllFaces(
            video,
            new faceapi.TinyFaceDetectorOptions()
        ).withFaceLandmarks();

        if (detections.length > 0) {
            document.getElementById('faceDetectionInfo').style.display = 'block';
            document.getElementById('faceCount').textContent = `${detections.length} face(s) detected`;
        } else {
            document.getElementById('faceDetectionInfo').style.display = 'none';
        }
    } catch (error) {
        console.error('Error detecting faces:', error);
    }

    requestAnimationFrame(() => detectFacesLoop(video));
}

// Capture image from webcam
function captureImage() {
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Mirror the image (since video is mirrored)
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    
    // Convert to blob
    canvas.toBlob(blob => {
        const reader = new FileReader();
        reader.onload = (e) => {
            capturedImages.push(e.target.result);
            addCapturedImageToUI(e.target.result);
            showMessage(`Image captured! (${capturedImages.length} total)`, 'success');
            document.getElementById('submitBtn').disabled = capturedImages.length === 0;
        };
        reader.readAsDataURL(blob);
    }, 'image/jpeg', 0.95);
}

// Add captured image to UI
function addCapturedImageToUI(imageData) {
    const container = document.getElementById('capturedImagesContainer');
    
    if (container.querySelector('p')) {
        container.innerHTML = '';
    }
    
    const div = document.createElement('div');
    div.className = 'captured-image';
    div.innerHTML = `
        <img src="${imageData}" alt="Captured">
        <button class="remove-btn" onclick="removeCapturedImage(this)" title="Remove">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(div);
}

// Remove captured image
function removeCapturedImage(btn) {
    const index = Array.from(document.querySelectorAll('.captured-image')).indexOf(btn.parentElement);
    capturedImages.splice(index, 1);
    btn.parentElement.remove();
    
    if (capturedImages.length === 0) {
        document.getElementById('capturedImagesContainer').innerHTML = '<p class="text-muted text-center py-5">No images captured yet</p>';
        document.getElementById('submitBtn').disabled = true;
    } else {
        document.getElementById('submitBtn').disabled = false;
    }
}

// Clear all captures
function clearCaptures() {
    if (confirm('Are you sure you want to clear all captured images?')) {
        capturedImages = [];
        document.getElementById('capturedImagesContainer').innerHTML = '<p class="text-muted text-center py-5">No images captured yet</p>';
        document.getElementById('submitBtn').disabled = true;
        showMessage('All images cleared', 'info');
    }
}

// Handle file upload
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const files = e.target.files;
            for (let file of files) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    capturedImages.push(event.target.result);
                    addCapturedImageToUI(event.target.result);
                };
                reader.readAsDataURL(file);
            }
            document.getElementById('submitBtn').disabled = capturedImages.length === 0;
        });
    }
});

// Submit registration
async function submitRegistration() {
    if (capturedImages.length === 0) {
        showMessage('Please capture or upload at least one image', 'warning');
        return;
    }

    document.getElementById('submitBtn').disabled = true;
    showMessage('Uploading images...', 'info');

    try {
        for (let i = 0; i < capturedImages.length; i++) {
            const imageData = capturedImages[i];
            const blob = await (await fetch(imageData)).blob();
            
            const formData = new FormData();
            formData.append('image', blob, `face_${i}.jpg`);
            
            const response = await fetch('/api/ai/register_face/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                const error = await response.json();
                showMessage(`Error uploading image ${i + 1}: ${error.error || 'Unknown error'}`, 'error');
                document.getElementById('submitBtn').disabled = false;
                return;
            }

            // Update progress
            const progress = ((i + 1) / capturedImages.length) * 100;
            document.getElementById('uploadProgress').style.width = progress + '%';
        }

        showMessage('Face registration completed successfully! Redirecting...', 'success');
        setTimeout(() => {
            window.location.href = '/student-dashboard/';
        }, 2000);
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('Error during registration: ' + error.message, 'error');
        document.getElementById('submitBtn').disabled = false;
    }
}

// Show message
function showMessage(message, type = 'info') {
    const container = document.getElementById('statusMessages');
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize on page load
window.addEventListener('load', initializeFaceDetection);
