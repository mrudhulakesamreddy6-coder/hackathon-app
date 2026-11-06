document.addEventListener('DOMContentLoaded', () => {
  // Initialize Leaflet Map
  if (window.DisasterSyncMap) {
    window.DisasterSyncMap.init();
  }

  let allIncidents = [];
  let currentFilter = 'all';

  const tableBody = document.getElementById('incidents-table-body');
  const searchInput = document.getElementById('incident-search-input');
  const filterTabs = document.querySelectorAll('#filter-tabs button');
  const refreshBtn = document.getElementById('refresh-dashboard-btn');

  // Fetch incidents from REST API
  async function fetchIncidents() {
    try {
      const resp = await fetch('/api/incidents');
      const data = await resp.json();

      if (data.success) {
        allIncidents = data.incidents || [];
        renderDashboard();
      }
    } catch (err) {
      console.error('Error loading incidents:', err);
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; color:#f87171; padding:20px;">
            <i class="fa-solid fa-triangle-exclamation"></i> Error loading incident reports from server.
          </td>
        </tr>
      `;
    }
  }

  // Refresh Stats KPIs
  async function fetchStats() {
    try {
      const resp = await fetch('/api/stats');
      const data = await resp.json();
      if (data.success && data.stats) {
        const s = data.stats;
        const setVal = (id, val) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val;
        };
        setVal('dash-stat-total', s.total);
        setVal('dash-stat-critical', s.critical);
        setVal('dash-stat-dispatches', s.dispatches);
        setVal('dash-stat-resolved', s.resolved);
      }
    } catch (err) {
      console.warn('Error refreshing stats:', err);
    }
  }

  // Filter & Render
  function renderDashboard() {
    let filtered = [...allIncidents];
    const searchTerm = (searchInput ? searchInput.value : '').toLowerCase().trim();

    // 1. Tab Filter
    if (currentFilter === 'critical') {
      filtered = filtered.filter(i => i.is_sos || i.urgency_level === 'CRITICAL');
    } else if (currentFilter === 'In Progress') {
      filtered = filtered.filter(i => i.status === 'In Progress' || i.status === 'Dispatched');
    } else if (currentFilter === 'Resolved') {
      filtered = filtered.filter(i => i.status === 'Resolved' || i.status === 'Closed');
    } else if (currentFilter !== 'all') {
      filtered = filtered.filter(i => (i.emergency_type || '').toLowerCase() === currentFilter.toLowerCase());
    }

    // 2. Search Filter
    if (searchTerm) {
      filtered = filtered.filter(i => 
        (i.incident_code || '').toLowerCase().includes(searchTerm) ||
        (i.title || '').toLowerCase().includes(searchTerm) ||
        (i.location_address || '').toLowerCase().includes(searchTerm) ||
        (i.landmark || '').toLowerCase().includes(searchTerm) ||
        (i.description || '').toLowerCase().includes(searchTerm) ||
        (i.emergency_type || '').toLowerCase().includes(searchTerm)
      );
    }

    // Update Map
    if (window.DisasterSyncMap) {
      window.DisasterSyncMap.loadIncidents(filtered);
    }

    // Render Table
    if (filtered.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; padding:32px; color:var(--text-muted);">
            <i class="fa-solid fa-inbox" style="font-size:2rem; margin-bottom:8px; display:block;"></i>
            No incident reports matching current criteria.
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = filtered.map(inc => {
      const isCritical = inc.is_sos || inc.urgency_level === 'CRITICAL';
      const badgeClass = inc.urgency_level ? inc.urgency_level.toLowerCase() : 'medium';
      
      return `
        <tr style="${isCritical ? 'background:rgba(239,68,68,0.04);' : ''}">
          <td>
            <div style="display:flex; align-items:center; gap:10px;">
              ${inc.photo_url ? `
                <a href="${inc.photo_url}" target="_blank" title="View Geotagged Live Photo">
                  <img src="${inc.photo_url}" alt="Live Ground Photo" style="width:44px; height:44px; border-radius:6px; object-fit:cover; border:1px solid #38bdf8; flex-shrink:0;">
                </a>
              ` : ''}
              <div>
                <div style="font-weight:700; font-family:monospace; font-size:0.95rem; color:#fff;">
                  ${inc.incident_code}
                </div>
                <div style="margin-top:4px; display:flex; gap:4px; flex-wrap:wrap;">
                  ${inc.is_sos ? `<span class="badge badge-sos" style="font-size:0.65rem;">SOS</span>` : ''}
                  ${inc.is_duplicate ? `<span class="badge badge-duplicate" style="font-size:0.65rem;">DUP (Parent #${inc.parent_incident_id})</span>` : ''}
                  ${inc.photo_url ? `<span class="badge" style="font-size:0.65rem; background:rgba(56,189,248,0.2); color:#38bdf8;"><i class="fa-solid fa-camera"></i> PHOTO</span>` : ''}
                </div>
              </div>
            </div>
          </td>
          <td>
            <strong style="color:#e2e8f0;">${inc.emergency_type}</strong>
            <div style="font-size:0.75rem; color:var(--text-muted); max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
              ${inc.title}
            </div>
          </td>
          <td>
            <div style="color:#cbd5e1; max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
              <i class="fa-solid fa-location-dot" style="color:#ef4444; font-size:0.8rem;"></i> ${inc.location_address}
            </div>
            ${inc.landmark ? `<div style="font-size:0.75rem; color:var(--text-dim);">Ref: ${inc.landmark}</div>` : ''}
          </td>
          <td>
            <span style="font-size:0.85rem; color:#e2e8f0;">${inc.people_affected || 0} affected</span>
            ${inc.trapped_count > 0 ? `<div style="font-size:0.75rem; color:#f87171; font-weight:bold;">${inc.trapped_count} trapped!</div>` : ''}
          </td>
          <td>
            <span class="badge badge-${badgeClass}">
              ${inc.urgency_level} (${inc.urgency_score})
            </span>
          </td>
          <td>
            <select class="form-control status-change-select" data-id="${inc.id}" style="padding:4px 8px; font-size:0.82rem; height:auto; width:auto; font-weight:600;">
              <option value="Reported" ${inc.status === 'Reported' ? 'selected' : ''}>Reported</option>
              <option value="Verified" ${inc.status === 'Verified' ? 'selected' : ''}>Verified</option>
              <option value="Dispatched" ${inc.status === 'Dispatched' ? 'selected' : ''}>Dispatched</option>
              <option value="In Progress" ${inc.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
              <option value="Resolved" ${inc.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
              <option value="Closed" ${inc.status === 'Closed' ? 'selected' : ''}>Closed</option>
            </select>
          </td>
          <td>
            <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
              <a href="/incident/${inc.id}" class="btn btn-primary btn-sm" style="padding:4px 10px; font-size:0.8rem;">
                <i class="fa-solid fa-brain"></i> Agents Plan
              </a>
              <button type="button" class="btn btn-secondary btn-sm run-agents-btn" data-id="${inc.id}" title="Execute all 5 AI agents now" style="padding:4px 8px; font-size:0.8rem; border-color:#8b5cf6; color:#c084fc;">
                <i class="fa-solid fa-play"></i> Run All
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    // Attach status change listeners
    document.querySelectorAll('.status-change-select').forEach(select => {
      select.addEventListener('change', async (e) => {
        const incId = select.getAttribute('data-id');
        const newStatus = select.value;

        try {
          const resp = await fetch(`/api/incident/${incId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus, officer_name: 'Command Duty Officer' })
          });
          const data = await resp.json();
          if (data.success) {
            window.DisasterSync.showToast(`Incident #${incId} marked ${newStatus}`, 'success');
            fetchStats();
            // Update local object
            const target = allIncidents.find(i => i.id == incId);
            if (target) target.status = newStatus;
          } else {
            window.DisasterSync.showToast(data.error || 'Failed to update status', 'danger');
          }
        } catch (err) {
          window.DisasterSync.showToast('Network error updating status', 'danger');
        }
      });
    });

    // Attach "Run All Agents" button listeners (Req 19)
    document.querySelectorAll('.run-agents-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const incId = btn.getAttribute('data-id');
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;

        try {
          const resp = await fetch(`/api/incident/${incId}/agents/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force: true })
          });
          const data = await resp.json();
          if (data.success) {
            window.DisasterSync.showToast(data.message || `All 5 agents executed for Incident #${incId}`, 'success');
            setTimeout(() => {
              window.location.href = `/incident/${incId}`;
            }, 600);
          } else {
            window.DisasterSync.showToast(data.error || 'Agent execution failed', 'danger');
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-play"></i> Run All`;
          }
        } catch (err) {
          window.DisasterSync.showToast('Network error triggering agents', 'danger');
          btn.disabled = false;
          btn.innerHTML = `<i class="fa-solid fa-play"></i> Run All`;
        }
      });
    });
  }

  // Filter tabs click
  filterTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      filterTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentFilter = tab.getAttribute('data-filter');
      renderDashboard();
    });
  });

  // Search input typing
  if (searchInput) {
    searchInput.addEventListener('input', renderDashboard);
  }

  // Refresh button
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      refreshBtn.disabled = true;
      fetchIncidents().then(() => {
        fetchStats();
        refreshBtn.disabled = false;
        window.DisasterSync.showToast('Incident feed updated', 'info');
      });
    });
  }

  // Test Email Diagnostic Modal Handlers (Req 9)
  const testEmailBtn = document.getElementById('btn-test-email');
  const testEmailModal = document.getElementById('test-email-modal');
  const testEmailCloseBtn = document.getElementById('test-email-modal-close');
  const testEmailCancelBtn = document.getElementById('test-email-cancel-btn');
  const testEmailExecuteBtn = document.getElementById('btn-execute-test-email');
  const testEmailTargetInput = document.getElementById('test-email-target-input');
  const testEmailBanner = document.getElementById('test-email-result-banner');
  const testEmailTitle = document.getElementById('test-email-result-title');
  const testEmailDetails = document.getElementById('test-email-result-details');

  function openTestEmailModal() {
    if (testEmailBanner) testEmailBanner.style.display = 'none';
    if (testEmailModal) testEmailModal.classList.add('active');
  }

  function closeTestEmailModal() {
    if (testEmailModal) testEmailModal.classList.remove('active');
  }

  if (testEmailBtn) testEmailBtn.addEventListener('click', openTestEmailModal);
  if (testEmailCloseBtn) testEmailCloseBtn.addEventListener('click', closeTestEmailModal);
  if (testEmailCancelBtn) testEmailCancelBtn.addEventListener('click', closeTestEmailModal);

  if (testEmailExecuteBtn) {
    testEmailExecuteBtn.addEventListener('click', async () => {
      const recipient = testEmailTargetInput ? testEmailTargetInput.value.trim() : '';
      testEmailExecuteBtn.disabled = true;
      testEmailExecuteBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Transmitting...`;

      try {
        const resp = await fetch('/api/email/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ recipient_email: recipient })
        });
        const data = await resp.json();

        if (testEmailBanner) {
          testEmailBanner.style.display = 'block';
          if (data.status === 'SENT') {
            testEmailBanner.style.background = 'rgba(16, 185, 129, 0.2)';
            testEmailBanner.style.border = '1px solid #10b981';
            testEmailBanner.style.color = '#34d399';
            testEmailTitle.innerHTML = `<i class="fa-solid fa-circle-check"></i> Live Email Transmitted Successfully!`;
            testEmailDetails.textContent = `Delivered to ${data.recipient} via live SMTP gateway.`;
            window.DisasterSync.showToast(`Test email sent to ${data.recipient}!`, 'success');
          } else if (data.status === 'SIMULATED_SENT') {
            testEmailBanner.style.background = 'rgba(2, 132, 199, 0.2)';
            testEmailBanner.style.border = '1px solid #0284c7';
            testEmailBanner.style.color = '#38bdf8';
            testEmailTitle.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Simulated Test Delivery Logged!`;
            testEmailDetails.textContent = `Simulated dispatch to ${data.recipient} recorded in database & audit trail (Live SMTP credentials not set).`;
            window.DisasterSync.showToast(`Simulated test email logged to ${data.recipient}`, 'info');
          } else {
            testEmailBanner.style.background = 'rgba(239, 68, 68, 0.2)';
            testEmailBanner.style.border = '1px solid #ef4444';
            testEmailBanner.style.color = '#f87171';
            testEmailTitle.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Transmission Failed`;
            testEmailDetails.textContent = data.error || 'Could not connect to SMTP server.';
            window.DisasterSync.showToast(`Test email failed: ${data.error}`, 'danger');
          }
        }
      } catch (err) {
        if (testEmailBanner) {
          testEmailBanner.style.display = 'block';
          testEmailBanner.style.background = 'rgba(239, 68, 68, 0.2)';
          testEmailBanner.style.border = '1px solid #ef4444';
          testEmailBanner.style.color = '#f87171';
          testEmailTitle.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Network Error`;
          testEmailDetails.textContent = 'Could not communicate with DisasterSync AI test endpoint.';
        }
        window.DisasterSync.showToast('Network error during test email', 'danger');
      } finally {
        testEmailExecuteBtn.disabled = false;
        testEmailExecuteBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Send Test Email`;
      }
    });
  }

  // Initial load
  fetchIncidents();
  fetchStats();

  // Periodic polling every 12 seconds
  setInterval(() => {
    fetchIncidents();
    fetchStats();
  }, 12000);

  // ====================================================================
  // AUTONOMOUS AI OPERATOR COPILOT (Req: AI to operate the project)
  // ====================================================================
  let voiceRadioActive = true;

  window.toggleVoiceRadio = function() {
    voiceRadioActive = !voiceRadioActive;
    const label = document.getElementById('voice-mode-label');
    const btn = document.getElementById('btn-toggle-voice');
    if (label) label.textContent = voiceRadioActive ? 'ON' : 'OFF';
    if (btn) {
      btn.style.color = voiceRadioActive ? '#c084fc' : '#94a3b8';
      btn.style.borderColor = voiceRadioActive ? '#a855f7' : '#475569';
    }
    if (window.DisasterSync && window.DisasterSync.showToast) {
      window.DisasterSync.showToast(`AI Radio Voice Announcements ${voiceRadioActive ? 'ENABLED' : 'MUTED'}`, 'info');
    }
  };

  window.toggleAIOperatorMode = async function() {
    try {
      const res = await fetch('/api/operator/toggle', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        updateAIOperatorUI(data.autonomous_mode);
        if (window.DisasterSync && window.DisasterSync.showToast) {
          window.DisasterSync.showToast(data.message, data.autonomous_mode ? 'success' : 'warning');
        }
      }
    } catch (e) {
      console.error("Error toggling AI Operator", e);
    }
  };

  window.triggerImmediateAICycle = async function() {
    try {
      const res = await fetch('/api/operator/cycle', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        if (window.DisasterSync && window.DisasterSync.showToast) {
          window.DisasterSync.showToast(`AI Operator Sweep #${data.cycle} executed: ${data.actions_taken ? data.actions_taken.length : 0} actions taken`, 'success');
        }
        await pollAIOperatorStatus();
        fetchIncidents();
        fetchStats();
      }
    } catch (e) {
      console.error("Error triggering AI cycle", e);
    }
  };

  window.runQuickChip = function(cmd) {
    const input = document.getElementById('ai-operator-cmd-input');
    if (input) {
      input.value = cmd;
      submitAIOperatorCommand();
    }
  };

  window.submitAIOperatorCommand = async function(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('ai-operator-cmd-input');
    const cmd = (input ? input.value : '').trim();
    if (!cmd) return;

    const btn = document.getElementById('btn-submit-cmd');
    const outputCard = document.getElementById('ai-operator-output-card');
    const outputText = document.getElementById('ai-operator-output-text');

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing...`;
    }

    try {
      const res = await fetch('/api/operator/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
      });
      const data = await res.json();

      if (outputCard && outputText) {
        outputCard.style.display = 'block';
        outputText.innerHTML = data.reply ? data.reply.replace(/\n/g, '<br>') : 'Instruction executed.';
      }

      if (voiceRadioActive && window.DisasterSync && window.DisasterSync.speakRadioDispatch) {
        const spoken = data.reply ? data.reply.replace(/[*#`•]/g, '').slice(0, 150) : "Operational directive executed.";
        window.DisasterSync.speakRadioDispatch(spoken);
      }

      if (window.DisasterSync && window.DisasterSync.playAlertBeep) {
        window.DisasterSync.playAlertBeep();
      }

      if (input) input.value = '';
      await pollAIOperatorStatus();
      fetchIncidents();
      fetchStats();
    } catch (err) {
      if (outputCard && outputText) {
        outputCard.style.display = 'block';
        outputText.innerHTML = `<span style="color:#f87171;">Error executing directive: ${err.message}</span>`;
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Execute Directive`;
      }
    }
  };

  function updateAIOperatorUI(isAuto) {
    const badge = document.getElementById('ai-operator-badge');
    const modeLabel = document.getElementById('auto-mode-label');
    const toggleBtn = document.getElementById('btn-toggle-auto');

    if (badge) {
      if (isAuto) {
        badge.style.background = 'rgba(16,185,129,0.2)';
        badge.style.color = '#34d399';
        badge.style.borderColor = 'rgba(16,185,129,0.4)';
        badge.innerHTML = `<i class="fa-solid fa-circle" style="font-size:0.5rem; animation:pulse-green 1.5s infinite;"></i> AUTONOMOUS AUTO-PILOT ON`;
      } else {
        badge.style.background = 'rgba(234,179,8,0.2)';
        badge.style.color = '#facc15';
        badge.style.borderColor = 'rgba(234,179,8,0.4)';
        badge.innerHTML = `<i class="fa-solid fa-pause"></i> MANUAL COPILOT MODE`;
      }
    }

    if (modeLabel) modeLabel.textContent = isAuto ? 'ON' : 'OFF';
    if (toggleBtn) {
      toggleBtn.style.color = isAuto ? '#34d399' : '#facc15';
      toggleBtn.style.borderColor = isAuto ? '#10b981' : '#eab308';
    }
  }

  async function pollAIOperatorStatus() {
    try {
      const res = await fetch('/api/operator/status');
      const data = await res.json();
      if (!data.success) return;

      updateAIOperatorUI(data.autonomous_mode);

      const tickerText = document.getElementById('operator-ticker-text');
      if (tickerText && data.latest_action) {
        tickerText.textContent = data.latest_action;
      }
    } catch (e) {
      console.error("AI Operator polling error", e);
    }
  }

  // Poll AI Operator every 10 seconds
  pollAIOperatorStatus();
  setInterval(pollAIOperatorStatus, 10000);
});

