/* Mandatory camera capture for grievance submission.
   Uses navigator.mediaDevices.getUserMedia -> canvas -> base64 data URI.
   NO file upload allowed. The form does not submit until a photo is captured. */

document.addEventListener('DOMContentLoaded', function () {
    const video = document.getElementById('cameraPreview');
    const canvas = document.getElementById('photoCanvas');
    const photoPreview = document.getElementById('photoPreview');
    const imageDataField = document.getElementById('imageDataField');
    const startBtn = document.getElementById('startCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const stopBtn = document.getElementById('stopCameraBtn');
    const cameraOff = document.getElementById('cameraOff');
    const noPhoto = document.getElementById('noPhoto');
    const cameraError = document.getElementById('cameraError');
    const form = document.getElementById('grievanceForm');

    let stream = null;
    let photoCaptured = false;

    function showError(msg) {
        cameraError.textContent = msg;
        cameraError.style.display = 'block';
    }

    function clearError() {
        cameraError.style.display = 'none';
        cameraError.textContent = '';
    }

    async function startCamera() {
        clearError();
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showError('Your browser does not support camera access. Please use a modern browser (Chrome/Edge/Firefox).');
            return;
        }
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' },
                audio: false
            });
            video.srcObject = stream;
            cameraOff.style.display = 'none';
            video.style.display = 'block';
            captureBtn.disabled = false;
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } catch (err) {
            showError('Could not access camera: ' + err.message +
                '. Please grant camera permission and try again (note: camera access may require HTTPS or localhost).');
        }
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(t => t.stop());
            stream = null;
        }
        video.srcObject = null;
        video.style.display = 'none';
        cameraOff.style.display = 'block';
        captureBtn.disabled = true;
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }

    function capture() {
        if (!stream) return;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
        photoPreview.src = dataUrl;
        photoPreview.style.display = 'block';
        noPhoto.style.display = 'none';
        imageDataField.value = dataUrl;
        photoCaptured = true;
        captureBtn.disabled = true;
        retakeBtn.disabled = false;
        stopCamera();
    }

    function retake() {
        photoPreview.style.display = 'none';
        noPhoto.style.display = 'block';
        imageDataField.value = '';
        photoCaptured = false;
        retakeBtn.disabled = true;
        startCamera();
    }

    startBtn.addEventListener('click', startCamera);
    captureBtn.addEventListener('click', capture);
    retakeBtn.addEventListener('click', retake);
    stopBtn.addEventListener('click', stopCamera);

    // Prevent form submission without a captured photo
    form.addEventListener('submit', function (e) {
        if (!photoCaptured || !imageDataField.value) {
            e.preventDefault();
            showError('You must capture a photo before submitting. Click "Start Camera" then "Capture".');
        }
    });
});
