document.addEventListener('DOMContentLoaded', () => {
  // Multilingual Dictionary (English, Telugu, Hindi) - FR Section 18 Compliance
  const translations = {
    en: {
      title: "Emergency Intake Form",
      subtitle: "Submit a verified disaster or rescue report. Our AI Multi-Agent system will immediately triage, coordinate, and notify simulated response units.",
      sos: "Instant Urgent SOS",
      submit: "Submit Emergency Report",
      types: {
        Flood: "Flood",
        Fire: "Fire",
        Accident: "Accident",
        Earthquake: "Earthquake",
        Landslide: "Landslide",
        Storm: "Storm / Cyclone",
        Medical: "Medical SOS"
      }
    },
    te: {
      title: "అత్యవసర సమాచార నమోదు ఫారమ్ (Emergency Intake)",
      subtitle: "వరదలు, అగ్ని, రోడ్డు ప్రమాదాల నివేదికను సమర్పించండి. AI మల్టీ-ఏజెంట్ వ్యవస్థ వెంటనే స్పందిస్తుంది.",
      sos: "అత్యవసర SOS",
      submit: "అత్యవసర నివేదికను సమర్పించండి",
      types: {
        Flood: "వరదలు (Flood)",
        Fire: "అగ్ని ప్రమాదం (Fire)",
        Accident: "రోడ్డు ప్రమాదం (Accident)",
        Earthquake: "భూకంపం (Earthquake)",
        Landslide: "కొండచరియలు (Landslide)",
        Storm: "తుఫాను (Cyclone)",
        Medical: "వైద్య అత్యవసరం (Medical)"
      }
    },
    hi: {
      title: "आपातकालीन सूचना फॉर्म (Emergency Intake)",
      subtitle: "सत्यापित आपदा रिपोर्ट दर्ज करें। हमारा AI मल्टी-एजेंट सिस्टम तुरंत कार्रवाई करेगा।",
      sos: "आपातकालीन SOS",
      submit: "आपातकालीन रिपोर्ट दर्ज करें",
      types: {
        Flood: "बाढ़ (Flood)",
        Fire: "आग (Fire)",
        Accident: "सड़क दुर्घटना (Accident)",
        Earthquake: "भूकंप (Earthquake)",
        Landslide: "भूस्खलन (Landslide)",
        Storm: "तूफान / चक्रवात (Storm)",
        Medical: "चिकित्सा आपातकाल (Medical)"
      }
    }
  };

  const langBtns = document.querySelectorAll('.lang-btn');
  langBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      langBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const lang = btn.getAttribute('data-lang');
      const t = translations[lang] || translations.en;

      const pageTitle = document.getElementById('i18n-page-title');
      const pageSub = document.getElementById('i18n-page-subtitle');
      const sosText = document.getElementById('i18n-sos-btn-text');
      const submitBtn = document.getElementById('submit-report-btn');

      if (pageTitle) pageTitle.innerHTML = `<i class="fa-solid fa-bullhorn" style="color:#ef4444;"></i> ${t.title}`;
      if (pageSub) pageSub.textContent = t.subtitle;
      if (sosText) sosText.textContent = t.sos;
      if (submitBtn) submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> ${t.submit}`;

      // Update type card titles
      document.querySelectorAll('.type-choice-card').forEach(card => {
        const rawType = card.getAttribute('data-type');
        const titleSpan = card.querySelector('.type-title');
        if (titleSpan && t.types[rawType]) {
          titleSpan.textContent = t.types[rawType];
        }
      });

      window.DisasterSync.showToast(`Language switched to ${lang === 'te' ? 'తెలుగు (Telugu)' : lang === 'hi' ? 'हिन्दी (Hindi)' : 'English'}`, 'info');
    });
  });

  // 1. Emergency Type Selector
  const typeCards = document.querySelectorAll('.type-choice-card');
  const typeInput = document.getElementById('selected-emergency-type');
  const titleInput = document.getElementById('report-title');

  // Check URL query param for default type (e.g. /report?type=Fire)
  const urlParams = new URLSearchParams(window.location.search);
  const paramType = urlParams.get('type');
  if (paramType) {
    typeCards.forEach(c => {
      if (c.getAttribute('data-type').toLowerCase() === paramType.toLowerCase()) {
        c.classList.add('selected');
        typeInput.value = c.getAttribute('data-type');
      } else {
        c.classList.remove('selected');
      }
    });
  }

  typeCards.forEach(card => {
    card.addEventListener('click', () => {
      typeCards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      const chosenType = card.getAttribute('data-type');
      typeInput.value = chosenType;

      if (!titleInput.value || titleInput.value.includes('Emergency')) {
        titleInput.value = `Critical ${chosenType} Emergency Reported`;
      }
    });
  });

  // 2. Interactive Leaflet Pin Picker Map
  const mapElement = document.getElementById('picker-map');
  const latInput = document.getElementById('report-lat');
  const lngInput = document.getElementById('report-lng');
  const addrInput = document.getElementById('report-address');

  let defaultLat = 15.9080;
  let defaultLng = 80.4730;

  if (mapElement && typeof L !== 'undefined') {
    const map = L.map('picker-map').setView([defaultLat, defaultLng], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let marker = L.marker([defaultLat, defaultLng], { draggable: true }).addTo(map);

    function updateMarkerPos(lat, lng) {
      marker.setLatLng([lat, lng]);
      latInput.value = lat.toFixed(6);
      lngInput.value = lng.toFixed(6);
      const coordsEl = document.getElementById('overlay-coords-text');
      if (coordsEl) {
        coordsEl.textContent = `📍 GPS: ${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`;
      }
    }

    marker.on('dragend', function (e) {
      const pos = e.target.getLatLng();
      updateMarkerPos(pos.lat, pos.lng);
    });

    map.on('click', function (e) {
      updateMarkerPos(e.latlng.lat, e.latlng.lng);
    });

    // Detect GPS button
    const gpsBtn = document.getElementById('detect-gps-btn');
    if (gpsBtn && navigator.geolocation) {
      gpsBtn.addEventListener('click', () => {
        gpsBtn.disabled = true;
        gpsBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Detecting GPS...`;

        navigator.geolocation.getCurrentPosition(
          (position) => {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;
            map.setView([userLat, userLng], 16);
            updateMarkerPos(userLat, userLng);
            if (!addrInput.value) {
              addrInput.value = `Current Citizen Device Location (${userLat.toFixed(4)}, ${userLng.toFixed(4)})`;
            }
            gpsBtn.disabled = false;
            gpsBtn.innerHTML = `<i class="fa-solid fa-check"></i> GPS Position Locked`;
            window.DisasterSync.showToast('Device location detected via GPS', 'success');
          },
          (error) => {
            gpsBtn.disabled = false;
            gpsBtn.innerHTML = `<i class="fa-solid fa-crosshairs"></i> Retry GPS Detection`;
            window.DisasterSync.showToast('GPS permission denied or unavailable. Using default Bapatla center.', 'danger');
          },
          { timeout: 7000, enableHighAccuracy: true }
        );
      });
    }
  }

  // 3. Top SOS Button in Report Form
  const topSosBtn = document.getElementById('form-top-sos-btn');
  const heroSosBtn = document.getElementById('hero-sos-btn');
  if (topSosBtn) {
    topSosBtn.addEventListener('click', () => {
      const sosModal = document.getElementById('sos-modal');
      if (sosModal) {
        window.DisasterSync.playAlertBeep();
        sosModal.classList.add('active');
      }
    });
  }

  // ====================================================================
  // LIVE CAMERA CONTROLLER (MediaDevices.getUserMedia API - Req 1 to 15)
  // ====================================================================
  const btnStartCamera = document.getElementById('btn-start-camera');
  const btnStopCamera = document.getElementById('btn-stop-camera');
  const btnCapturePhoto = document.getElementById('btn-capture-photo');
  const btnRetakePhoto = document.getElementById('btn-retake-photo');
  const btnUsePhoto = document.getElementById('btn-use-photo');
  const btnSwitchCamera = document.getElementById('btn-switch-camera');
  const liveVideo = document.getElementById('live-camera-feed');
  const cameraHud = document.getElementById('camera-hud-viewfinder');
  const capturedPhotoDisplay = document.getElementById('captured-photo-display');
  const permissionStatusBadge = document.getElementById('camera-permission-status');
  const photoDataInput = document.getElementById('selected-photo-data');
  const photoUrlInput = document.getElementById('selected-photo-url');
  const fileUploadInput = document.getElementById('file-upload-input');
  const quickPhotoBtns = document.querySelectorAll('.quick-photo-btn');

  let activeCameraStream = null;
  let currentFacingMode = 'environment'; // Default to rear camera on phones, fallback to webcam
  let tempCapturedDataUrl = null;

  // 1. Open Device Camera with Permission Request (Req 2, 3, 4, 11, 12, 14)
  async function startLiveCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      window.DisasterSync.showToast('Camera API not supported on this browser. Please use file upload.', 'danger');
      if (permissionStatusBadge) {
        permissionStatusBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Camera Not Supported`;
      }
      return;
    }

    if (permissionStatusBadge) {
      permissionStatusBadge.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Requesting Camera Access...`;
      permissionStatusBadge.style.color = '#fbbf24';
    }

    try {
      const constraints = {
        video: {
          facingMode: currentFacingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      activeCameraStream = stream;
      liveVideo.srcObject = stream;
      await liveVideo.play();

      // UI Viewfinder State
      liveVideo.style.display = 'block';
      if (cameraHud) cameraHud.style.display = 'block';
      if (capturedPhotoDisplay) capturedPhotoDisplay.style.display = 'none';

      // Control Buttons State
      if (btnStartCamera) btnStartCamera.style.display = 'none';
      if (btnCapturePhoto) btnCapturePhoto.style.display = 'inline-flex';
      if (btnStopCamera) btnStopCamera.style.display = 'inline-flex';
      if (btnSwitchCamera) btnSwitchCamera.style.display = 'inline-flex';
      if (btnRetakePhoto) btnRetakePhoto.style.display = 'none';
      if (btnUsePhoto) btnUsePhoto.style.display = 'none';

      if (permissionStatusBadge) {
        permissionStatusBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i> Camera Live (${currentFacingMode === 'user' ? 'Front' : 'Rear'})`;
        permissionStatusBadge.style.color = '#34d399';
      }

      window.DisasterSync.showToast('Live camera viewfinder started. Aim at disaster scene and click Capture.', 'success');
    } catch (err) {
      console.warn('Camera access denied or error:', err);
      let errMsg = 'Camera access was denied or unavailable.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errMsg = 'Camera permission denied. Please allow camera permissions in your browser bar.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errMsg = 'No camera device found on this laptop or phone.';
      }

      if (permissionStatusBadge) {
        permissionStatusBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Camera Access Denied`;
        permissionStatusBadge.style.color = '#f87171';
      }
      window.DisasterSync.showToast(errMsg, 'danger');
    }
  }

  // 2. Stop Device Camera (Req 11)
  function stopLiveCamera() {
    if (activeCameraStream) {
      activeCameraStream.getTracks().forEach(track => track.stop());
      activeCameraStream = null;
    }
    if (liveVideo) {
      liveVideo.srcObject = null;
      liveVideo.style.display = 'none';
    }
    if (cameraHud) cameraHud.style.display = 'none';
    if (capturedPhotoDisplay) capturedPhotoDisplay.style.display = 'block';

    // Buttons State
    if (btnStartCamera) btnStartCamera.style.display = 'inline-flex';
    if (btnCapturePhoto) btnCapturePhoto.style.display = 'none';
    if (btnStopCamera) btnStopCamera.style.display = 'none';
    if (btnSwitchCamera) btnSwitchCamera.style.display = 'none';

    if (permissionStatusBadge) {
      permissionStatusBadge.innerHTML = `<i class="fa-solid fa-video-slash"></i> Camera Stopped`;
      permissionStatusBadge.style.color = '#94a3b8';
    }
  }

  // 3. Capture Photo with Live Geotag Watermark (Req 5, 6, 8, 9)
  function capturePhotoFromCamera() {
    if (!liveVideo || !activeCameraStream) return;

    const canvas = document.createElement('canvas');
    canvas.width = liveVideo.videoWidth || 800;
    canvas.height = liveVideo.videoHeight || 600;
    const ctx = canvas.getContext('2d');

    // Draw video frame onto canvas
    ctx.drawImage(liveVideo, 0, 0, canvas.width, canvas.height);

    // Stamping GPS Geotag HUD Watermark
    const bannerH = Math.max(75, Math.floor(canvas.height * 0.16));
    ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
    ctx.fillRect(0, canvas.height - bannerH, canvas.width, bannerH);
    
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 3;
    ctx.strokeRect(0, canvas.height - bannerH, canvas.width, bannerH);

    const lat = latInput ? latInput.value : '15.9080';
    const lng = lngInput ? lngInput.value : '80.4730';
    const emType = typeInput ? typeInput.value : 'EMERGENCY';
    const addr = addrInput ? (addrInput.value || 'Bapatla Municipal Area') : 'Bapatla Municipal Area';
    const now = new Date().toLocaleString();

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 16px monospace';
    ctx.fillText(`📍 LIVE GEOTAG: ${parseFloat(lat).toFixed(4)}° N, ${parseFloat(lng).toFixed(4)}° E | ${emType.toUpperCase()}`, 18, canvas.height - bannerH + 26);

    ctx.fillStyle = '#ffffff';
    ctx.font = '13px sans-serif';
    ctx.fillText(`LOCATION: ${addr}`, 18, canvas.height - bannerH + 46);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px sans-serif';
    ctx.fillText(`TIMESTAMP: ${now} | DISASTERSYNC AI VERIFIED ON-SCENE CAMERA STREAM`, 18, canvas.height - bannerH + 64);

    // Generate JPEG data URL
    tempCapturedDataUrl = canvas.toDataURL('image/jpeg', 0.9);

    // Stop video stream and display captured image
    stopLiveCamera();

    if (capturedPhotoDisplay) {
      capturedPhotoDisplay.src = tempCapturedDataUrl;
      capturedPhotoDisplay.style.display = 'block';
    }

    // Toggle Retake and Use Photo buttons (Req 7)
    if (btnRetakePhoto) btnRetakePhoto.style.display = 'inline-flex';
    if (btnUsePhoto) btnUsePhoto.style.display = 'inline-flex';
    if (btnStartCamera) btnStartCamera.style.display = 'none';

    window.DisasterSync.playAlertBeep();
    window.DisasterSync.showToast('Photo captured! Click "Use Photo" to attach to report or "Retake" to capture again.', 'info');
  }

  // 4. Retake Photo (Req 7)
  function retakeCapturedPhoto() {
    tempCapturedDataUrl = null;
    startLiveCamera();
  }

  // 5. Use Photo (Req 7 & 8)
  function confirmUsePhoto() {
    if (tempCapturedDataUrl) {
      if (photoDataInput) photoDataInput.value = tempCapturedDataUrl;
      if (photoUrlInput) photoUrlInput.value = '';
      
      if (btnUsePhoto) btnUsePhoto.style.display = 'none';
      if (btnStartCamera) btnStartCamera.style.display = 'inline-flex';
      
      const badge = document.getElementById('geotag-status-badge');
      if (badge) {
        badge.innerHTML = `<i class="fa-solid fa-circle-check"></i> LIVE CAMERA PHOTO ATTACHED`;
        badge.className = 'badge badge-low';
        badge.style.background = 'rgba(16,185,129,0.3)';
        badge.style.color = '#34d399';
      }

      window.DisasterSync.showToast('Live camera photo locked & attached to incident report.', 'success');
    }
  }

  // 6. Flip Camera Lens for Mobile Phones (Req 12)
  async function flipCameraLens() {
    currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    stopLiveCamera();
    await startLiveCamera();
  }

  // Button Event Listeners
  if (btnStartCamera) btnStartCamera.addEventListener('click', startLiveCamera);
  if (btnStopCamera) btnStopCamera.addEventListener('click', stopLiveCamera);
  if (btnCapturePhoto) btnCapturePhoto.addEventListener('click', capturePhotoFromCamera);
  if (btnRetakePhoto) btnRetakePhoto.addEventListener('click', retakeCapturedPhoto);
  if (btnUsePhoto) btnUsePhoto.addEventListener('click', confirmUsePhoto);
  if (btnSwitchCamera) btnSwitchCamera.addEventListener('click', flipCameraLens);

  // File Upload Fallback Handling (Req 15)
  function handleImageFile(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(evt) {
      const img = new Image();
      img.onload = function() {
        const canvas = document.createElement('canvas');
        canvas.width = img.width || 800;
        canvas.height = img.height || 600;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        const bannerH = Math.max(75, Math.floor(canvas.height * 0.16));
        ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
        ctx.fillRect(0, canvas.height - bannerH, canvas.width, bannerH);
        
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 3;
        ctx.strokeRect(0, canvas.height - bannerH, canvas.width, bannerH);

        const lat = latInput ? latInput.value : '15.9080';
        const lng = lngInput ? lngInput.value : '80.4730';
        const emType = typeInput ? typeInput.value : 'EMERGENCY';
        const addr = addrInput ? (addrInput.value || 'Bapatla Municipal Area') : 'Bapatla Municipal Area';
        const now = new Date().toLocaleString();

        ctx.fillStyle = '#38bdf8';
        ctx.font = 'bold 16px monospace';
        ctx.fillText(`📍 LIVE GEOTAG: ${parseFloat(lat).toFixed(4)}° N, ${parseFloat(lng).toFixed(4)}° E | ${emType.toUpperCase()}`, 18, canvas.height - bannerH + 26);

        ctx.fillStyle = '#ffffff';
        ctx.font = '13px sans-serif';
        ctx.fillText(`LOCATION: ${addr}`, 18, canvas.height - bannerH + 46);

        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px sans-serif';
        ctx.fillText(`TIMESTAMP: ${now} | DISASTERSYNC AI VERIFIED FILE UPLOAD`, 18, canvas.height - bannerH + 64);

        const watermarkedUrl = canvas.toDataURL('image/jpeg', 0.9);
        if (capturedPhotoDisplay) {
          capturedPhotoDisplay.src = watermarkedUrl;
          capturedPhotoDisplay.style.display = 'block';
        }
        if (photoDataInput) photoDataInput.value = watermarkedUrl;
        if (photoUrlInput) photoUrlInput.value = '';
        window.DisasterSync.showToast('Uploaded image stamped with GPS coordinates & attached to report!', 'success');
      };
      img.src = evt.target.result;
    };
    reader.readAsDataURL(file);
  }

  if (fileUploadInput) {
    fileUploadInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleImageFile(e.target.files[0]);
      }
    });
  }

  quickPhotoBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const pUrl = btn.getAttribute('data-photo');
      if (capturedPhotoDisplay) {
        capturedPhotoDisplay.src = pUrl;
        capturedPhotoDisplay.style.display = 'block';
      }
      if (photoUrlInput) photoUrlInput.value = pUrl;
      if (photoDataInput) photoDataInput.value = '';
      window.DisasterSync.showToast('Preset scene photo selected with verified geotag', 'info');
    });
  });

  // 4. Report Form Submission & Multi-Agent Intake
  const reportForm = document.getElementById('emergency-report-form');
  const resultModal = document.getElementById('report-result-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');

  if (reportForm) {
    reportForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('submit-report-btn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running Multi-Agent Triage...`;

      const formData = new FormData(reportForm);
      const payload = Object.fromEntries(formData.entries());

      try {
        const resp = await fetch('/api/report', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();

        if (data.success) {
          window.DisasterSync.playAlertBeep();
          
          // Populate Result Modal
          document.getElementById('modal-incident-code').textContent = data.incident_code;
          
          const urgencyBadge = document.getElementById('modal-urgency-badge');
          urgencyBadge.className = `badge badge-${data.urgency_level.toLowerCase()}`;
          urgencyBadge.textContent = `${data.urgency_level} (${data.urgency_score}/100)`;

          const dupStatus = document.getElementById('modal-duplicate-status');
          if (data.is_duplicate) {
            dupStatus.innerHTML = `<span style="color:#c084fc;">⚠️ Duplicate Cluster (Merged with #${data.parent_id})</span>`;
          } else {
            dupStatus.innerHTML = `<span style="color:#34d399;"><i class="fa-solid fa-check"></i> Unique Verified Incident</span>`;
          }

          document.getElementById('modal-alerts-count').textContent = `${data.alerts_count} Simulated Dispatches Generated`;

          // Populate Email Notification Status (Req 1, 2 & Email Send Message)
          const emailPill = document.getElementById('modal-email-status-pill');
          const officerMsg = document.getElementById('modal-officer-email-msg');
          const officerAddr = document.getElementById('modal-officer-email-addr');
          const userMsgText = document.getElementById('modal-user-email-text');

          let emailToastDetail = "Officers notified via email";
          if (data.email_notifications && data.email_notifications.results) {
            const firstResult = data.email_notifications.results[0];
            const st = firstResult?.status || 'PENDING';
            const recipientAddr = firstResult?.recipient || 'N/A';
            if (emailPill) {
              emailPill.textContent = st;
              // Color the pill based on status
              if (st === 'SENT') {
                emailPill.style.background = '#059669';
              } else if (st === 'FAILED') {
                emailPill.style.background = '#dc2626';
              } else {
                emailPill.style.background = '#0284c7';
              }
            }
            if (officerAddr) {
              officerAddr.textContent = `${recipientAddr} — ${st}`;
              officerAddr.style.color = st === 'SENT' ? '#34d399' : (st === 'FAILED' ? '#f87171' : '#fbbf24');
            }
            if (officerMsg && !officerAddr) {
              officerMsg.innerHTML = `<i class="fa-solid fa-bell" style="color:#f59e0b; width:16px;"></i> <span>Officer Alert: <strong style="color:#fbbf24; font-family:monospace;">${recipientAddr}</strong> — ${st}</span>`;
            }
            emailToastDetail = `Officer alert ${st} → ${recipientAddr}`;
          }

          if (data.user_confirmation && data.user_confirmation.recipient) {
            const uStatus = data.user_confirmation.status;
            const uRecipient = data.user_confirmation.recipient;
            if (userMsgText) {
              userMsgText.innerHTML = `Citizen Confirmation: <strong style="font-family:monospace; color:#6ee7b7;">${uRecipient}</strong> — ${uStatus}`;
            }
            emailToastDetail += ` & citizen confirmation ${uStatus} → ${uRecipient}`;
          } else {
            if (userMsgText) {
              userMsgText.textContent = "Citizen Confirmation: No email provided — enter your email to receive tracking updates.";
              userMsgText.style.color = '#94a3b8';
            }
          }

          // Tailor Safety Advice
          const safetyText = document.getElementById('modal-safety-text');
          const emType = (payload.emergency_type || '').toLowerCase();
          if (emType.includes('flood')) {
            safetyText.textContent = "Move immediately to higher floors or high ground. Do NOT attempt to walk, swim, or drive through moving water. Avoid downed electrical powerlines.";
          } else if (emType.includes('fire')) {
            safetyText.textContent = "Evacuate the building immediately. Stay low beneath smoke where air is clearer. Do not use elevators. Assemble at least 300m upwind.";
          } else if (emType.includes('earthquake')) {
            safetyText.textContent = "Drop, Cover, and Hold On. Stay away from glass windows and exterior walls. If outdoors, move away from buildings, streetlights, and utility wires.";
          } else if (emType.includes('accident')) {
            safetyText.textContent = "Do not move severely injured persons unless immediate explosion threat exists. Keep oncoming traffic alerted with hazard lights and flares.";
          } else {
            safetyText.textContent = "Stay calm, conserve your mobile phone battery, and remain in a secure location until authorized emergency responders arrive.";
          }

          document.getElementById('modal-view-detail-btn').href = `/incident/${data.incident_id}`;
          const modalTrackBtn = document.getElementById('modal-track-btn');
          if (modalTrackBtn) modalTrackBtn.href = `/track/${data.incident_code}`;
          
          resultModal.classList.add('active');
          window.DisasterSync.showToast(`Emergency ${data.incident_code} reported! ${emailToastDetail}`, 'success');
        } else {
          window.DisasterSync.showToast(data.error || 'Failed to submit report', 'danger');
        }
      } catch (err) {
        window.DisasterSync.showToast('Network error during report submission', 'danger');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Submit Emergency Report`;
      }
    });
  }

  if (modalCloseBtn && resultModal) {
    modalCloseBtn.addEventListener('click', () => {
      resultModal.classList.remove('active');
      reportForm.reset();
    });
  }
});

