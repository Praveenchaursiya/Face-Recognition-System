(() => {
  const camera = document.getElementById('camera');
  const canvas = document.getElementById('snapshot');
  let cameraStream;

  function setCameraStatus(message, isError = false) {
    const status = document.getElementById('capture-status') || document.getElementById('recognition-result');
    if (!status) return;
    status.textContent = message;
    if (isError) status.className = 'result danger';
  }

  async function startCamera() {
    if (!camera) return;
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraStatus('This browser does not support camera access.', true);
      return;
    }
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      camera.srcObject = cameraStream;
      await camera.play();
      setCameraStatus('Camera ready.');
    } catch (error) {
      const reason = error.name === 'NotAllowedError'
        ? 'Camera permission was denied. Allow camera access in your browser and Windows settings.'
        : 'Camera could not be opened. Close other apps using it, then refresh this page.';
      setCameraStatus(reason, true);
    }
  }

  window.addEventListener('beforeunload', () => cameraStream?.getTracks().forEach((track) => track.stop()));

  function captureImage() {
    if (!camera || !camera.videoWidth) throw new Error('Camera is not ready. Allow access and wait for the preview.');
    canvas.width = camera.videoWidth; canvas.height = camera.videoHeight;
    canvas.getContext('2d').drawImage(camera, 0, 0);
    return canvas.toDataURL('image/jpeg', 0.92);
  }
  const capture = document.getElementById('capture');
  if (capture) capture.addEventListener('click', () => {
    try { document.getElementById('face-image').value = captureImage(); document.getElementById('capture-status').textContent = 'Face image captured. You can now register.'; }
    catch (error) { document.getElementById('capture-status').textContent = error.message; }
  });
  const recognize = document.getElementById('recognize');
  if (recognize) recognize.addEventListener('click', async () => {
    const result = document.getElementById('recognition-result');
    try {
      recognize.disabled = true; result.textContent = 'Analyzing face…';
      const response = await fetch('/api/recognize', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({image: captureImage()})});
      const data = await response.json(); result.textContent = data.message || data.error || 'Recognition failed.';
      result.className = `result ${data.status === 'recognized' ? 'success' : 'warning'}`;
    } catch (error) { result.textContent = error.message; result.className = 'result danger'; }
    finally { recognize.disabled = false; }
  });
  startCamera();
})();
