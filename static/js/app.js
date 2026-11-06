// DisasterSync AI - Core Application Script
window.DisasterSync = {
  // Synthesize an alert sound using Web Audio API (no external mp3 file needed)
  playAlertBeep: function() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, ctx.currentTime); // A5
      osc.frequency.setValueAtTime(1174, ctx.currentTime + 0.15); // D6
      
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    } catch (e) {
      console.warn("Audio playback not permitted or unavailable", e);
    }
  },

  // Text-to-Speech radio dispatcher announcement
  speakRadioDispatch: function(text) {
    try {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.05;
        utterance.pitch = 0.95;
        window.speechSynthesis.speak(utterance);
      }
    } catch (e) {
      console.warn("Speech synthesis unavailable", e);
    }
  },

  // Display a toast message in bottom right
  showToast: function(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `card`;
    toast.style.cssText = `
      padding: 12px 18px;
      margin-bottom: 8px;
      border-radius: 8px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.6);
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.88rem;
      font-weight: 600;
      min-width: 260px;
      animation: slide-in 0.3s ease;
      color: #fff;
    `;

    if (type === 'success') {
      toast.style.background = '#065f46';
      toast.style.border = '1px solid #10b981';
      toast.innerHTML = `<i class="fa-solid fa-circle-check" style="color:#34d399;"></i> <span>${message}</span>`;
    } else if (type === 'danger') {
      toast.style.background = '#7f1d1d';
      toast.style.border = '1px solid #ef4444';
      toast.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color:#f87171;"></i> <span>${message}</span>`;
    } else {
      toast.style.background = '#1e3a8a';
      toast.style.border = '1px solid #3b82f6';
      toast.innerHTML = `<i class="fa-solid fa-info" style="color:#60a5fa;"></i> <span>${message}</span>`;
    }

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Nav Toggle
  const toggleBtn = document.getElementById('mobile-toggle');
  const navMenu = document.getElementById('nav-menu');
  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', () => {
      navMenu.classList.toggle('show');
    });
  }

  // Demo Scenario Buttons
  const scenarioBtns = [
    document.getElementById('load-scenario-btn'),
    document.getElementById('load-scenario-dash-btn')
  ];

  scenarioBtns.forEach(btn => {
    if (!btn) return;
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Initializing Multi-Agent Scenario...`;

      try {
        const resp = await fetch('/api/demo/load-scenario', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await resp.json();

        if (data.success) {
          window.DisasterSync.playAlertBeep();
          window.DisasterSync.showToast(data.message, 'success');
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 800);
        } else {
          window.DisasterSync.showToast('Failed to load demo scenario', 'danger');
          btn.disabled = false;
          btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Load Hackathon Demo Scenario`;
        }
      } catch (err) {
        window.DisasterSync.showToast('Error communicating with backend', 'danger');
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Load Hackathon Demo Scenario`;
      }
    });
  });

  // Global SOS Modal Handlers
  const heroSosBtn = document.getElementById('hero-sos-btn');
  const sosModal = document.getElementById('sos-modal');
  const sosCancelBtn = document.getElementById('sos-cancel-btn');
  const sosQuickForm = document.getElementById('sos-quick-form');
  const sosLocInput = document.getElementById('sos-location');
  const sosLatInput = document.getElementById('sos-lat');
  const sosLngInput = document.getElementById('sos-lng');

  if (heroSosBtn && sosModal) {
    heroSosBtn.addEventListener('click', () => {
      window.DisasterSync.playAlertBeep();
      sosModal.classList.add('active');

      // Attempt GPS fetch
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            sosLatInput.value = pos.coords.latitude.toFixed(6);
            sosLngInput.value = pos.coords.longitude.toFixed(6);
            sosLocInput.value = `Live GPS: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)} (Current Citizen Position)`;
          },
          (err) => {
            // Default Bapatla demo position
            sosLatInput.value = "15.9054";
            sosLngInput.value = "80.4682";
            sosLocInput.value = "Bapatla Municipal Area (GPS Permission Required for Exact Street)";
          },
          { timeout: 5000 }
        );
      }
    });

    if (sosCancelBtn) {
      sosCancelBtn.addEventListener('click', () => {
        sosModal.classList.remove('active');
      });
    }

    if (sosQuickForm) {
      sosQuickForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const confirmBtn = document.getElementById('sos-confirm-btn');
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Broadcasting SOS...`;

        const payload = {
          emergency_type: document.getElementById('sos-type').value,
          location_address: sosLocInput.value,
          latitude: parseFloat(sosLatInput.value),
          longitude: parseFloat(sosLngInput.value),
          people_affected: parseInt(document.getElementById('sos-people').value) || 2,
          trapped_count: 1,
          description: "CRITICAL 1-CLICK SOS CITIZEN DISTRESS BEACON ACTIVATED. Immediate rescue, police perimeter, and medical assistance required."
        };

        try {
          const resp = await fetch('/api/sos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const data = await resp.json();

          if (data.success) {
            window.DisasterSync.playAlertBeep();
            window.DisasterSync.showToast(`SOS Dispatched! Code: ${data.incident_code}`, 'danger');
            sosModal.classList.remove('active');
            setTimeout(() => {
              window.location.href = `/incident/${data.incident_id}`;
            }, 1000);
          } else {
            window.DisasterSync.showToast(data.error || 'Failed to dispatch SOS', 'danger');
            confirmBtn.disabled = false;
          }
        } catch (err) {
          window.DisasterSync.showToast('Network error triggering SOS', 'danger');
          confirmBtn.disabled = false;
        }
      });
    }
  }

  // Incident Tracking Form on Homepage
  const trackForm = document.getElementById('track-incident-form');
  const trackModal = document.getElementById('track-result-modal');
  const trackModalContent = document.getElementById('track-modal-content');
  const trackModalClose = document.getElementById('track-modal-close');

  if (trackForm && trackModal) {
    trackForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const codeInput = document.getElementById('track-code-input');
      const code = codeInput ? codeInput.value.trim().toUpperCase() : '';
      if (!code) return;

      trackModal.classList.add('active');
      trackModalContent.innerHTML = `
        <div style="text-align: center; padding: 25px; color: var(--text-muted);">
          <i class="fa-solid fa-spinner fa-spin" style="font-size: 1.5rem; color: #3b82f6;"></i>
          <div style="margin-top: 8px;">Querying CAD dispatch registry for ${code}...</div>
        </div>
      `;

      try {
        const resp = await fetch(`/api/track/${encodeURIComponent(code)}`);
        const data = await resp.json();

        if (data.success && data.incident) {
          const inc = data.incident;
          trackModalContent.innerHTML = `
            <div style="background: rgba(15,23,42,0.8); padding: 16px; border-radius: var(--radius-md); margin-bottom: 14px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong style="font-family: monospace; font-size: 1.15rem; color: #60a5fa;">${inc.incident_code}</strong>
                <span class="badge badge-${inc.urgency_level.toLowerCase()}">${inc.urgency_level} PRIORITY</span>
              </div>
              <div style="font-weight: 600; color: #fff; margin-bottom: 4px;">${inc.emergency_type}: ${inc.title}</div>
              <div style="font-size: 0.8rem; color: var(--text-muted);"><i class="fa-solid fa-location-dot"></i> ${inc.location_address}</div>
            </div>

            <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 12px; border-radius: 4px; margin-bottom: 14px;">
              <div style="font-size: 0.8rem; color: var(--text-muted);">Current Response Progress:</div>
              <div style="font-size: 1.1rem; font-weight: bold; color: #34d399; margin-top: 2px;">
                <i class="fa-solid fa-circle-check"></i> Status: ${inc.status}
              </div>
              <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 4px;">
                Incident verified and triaged. Official coordination protocol is active.
              </div>
            </div>

            <div style="margin-bottom: 16px;">
              <strong style="font-size: 0.85rem; color: var(--text-muted);">Assigned Response Channels:</strong>
              <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 6px;">
                ${(data.alerts || []).map(a => `
                  <div style="display: flex; justify-content: space-between; font-size: 0.8rem; background: rgba(0,0,0,0.3); padding: 6px 10px; border-radius: 4px;">
                    <span><strong>${a.agency_name}</strong> (${a.alert_channel})</span>
                    <span class="badge" style="background:#2563eb; color:#fff;">${a.status}</span>
                  </div>
                `).join('')}
              </div>
            </div>

            <div style="display: flex; justify-content: flex-end;">
              <button type="button" class="btn btn-secondary btn-sm" id="track-modal-done">Close</button>
            </div>
          `;

          const doneBtn = document.getElementById('track-modal-done');
          if (doneBtn) {
            doneBtn.addEventListener('click', () => {
              trackModal.classList.remove('active');
            });
          }
        } else {
          trackModalContent.innerHTML = `
            <div style="text-align: center; padding: 25px; color: #f87171;">
              <i class="fa-solid fa-circle-xmark" style="font-size: 2rem; margin-bottom: 8px;"></i>
              <div>${data.error || 'Incident tracking ID not found.'}</div>
              <button type="button" class="btn btn-secondary btn-sm" style="margin-top: 14px;" id="track-modal-retry">Try Again</button>
            </div>
          `;
          const retryBtn = document.getElementById('track-modal-retry');
          if (retryBtn) {
            retryBtn.addEventListener('click', () => {
              trackModal.classList.remove('active');
            });
          }
        }
      } catch (err) {
        trackModalContent.innerHTML = `
          <div style="text-align: center; padding: 20px; color: #f87171;">
            Failed to contact tracking registry.
          </div>
        `;
      }
    });
  }

  if (trackModalClose && trackModal) {
    trackModalClose.addEventListener('click', () => {
      trackModal.classList.remove('active');
    });
  }
});

