// DisasterSync AI - Interactive Geospatial Leaflet Map
window.DisasterSyncMap = {
  map: null,
  markersLayer: null,
  defaultCenter: [15.9080, 80.4730], // Centered around Bapatla, AP

  init: function () {
    const mapElement = document.getElementById('map-container');
    if (!mapElement || typeof L === 'undefined') return;

    this.map = L.map('map-container').setView(this.defaultCenter, 13);

    // Dark-themed or standard OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);

    this.markersLayer = L.layerGroup().addTo(this.map);
  },

  getMarkerColor: function (incident) {
    if (incident.is_sos || incident.urgency_level === 'CRITICAL') return '#ef4444';
    const type = (incident.emergency_type || '').toLowerCase();
    if (type.includes('flood')) return '#3b82f6';
    if (type.includes('fire')) return '#f97316';
    if (type.includes('accident')) return '#a855f7';
    if (type.includes('earthquake')) return '#eab308';
    return '#10b981';
  },

  getIconClass: function (incident) {
    if (incident.is_sos) return 'fa-bell';
    const type = (incident.emergency_type || '').toLowerCase();
    if (type.includes('flood')) return 'fa-house-flood-water';
    if (type.includes('fire')) return 'fa-fire';
    if (type.includes('accident')) return 'fa-car-burst';
    if (type.includes('earthquake')) return 'fa-volcano';
    return 'fa-triangle-exclamation';
  },

  loadIncidents: function (incidents) {
    if (!this.map || !this.markersLayer) return;
    this.markersLayer.clearLayers();

    const bounds = [];

    incidents.forEach(inc => {
      if (!inc.latitude || !inc.longitude) return;

      const lat = parseFloat(inc.latitude);
      const lng = parseFloat(inc.longitude);
      bounds.push([lat, lng]);

      const color = this.getMarkerColor(inc);
      const iconClass = this.getIconClass(inc);
      const isCritical = inc.is_sos || inc.urgency_level === 'CRITICAL';

      // Custom HTML Marker with pulsing glow
      const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `
          <div style="
            background: ${color};
            width: 34px;
            height: 34px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 0 ${isCritical ? '18px #ef4444' : '8px rgba(0,0,0,0.5)'};
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 14px;
            animation: ${isCritical ? 'pulse-red 1.5s infinite' : 'none'};
          ">
            <i class="fa-solid ${iconClass}"></i>
          </div>
        `,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
        popupAnchor: [0, -18]
      });

      const marker = L.marker([lat, lng], { icon: customIcon });

      const photoThumb = inc.photo_url ? `
        <div style="width:100%; height:110px; border-radius:4px; overflow:hidden; margin-bottom:8px; border:1px solid #cbd5e1; position:relative;">
          <img src="${inc.photo_url}" alt="Ground Scene" style="width:100%; height:100%; object-fit:cover; display:block;">
          <div style="position:absolute; bottom:2px; left:4px; background:rgba(0,0,0,0.75); color:#38bdf8; font-size:9px; font-family:monospace; padding:1px 5px; border-radius:2px;">
            📍 ${parseFloat(inc.latitude).toFixed(4)}, ${parseFloat(inc.longitude).toFixed(4)}
          </div>
        </div>
      ` : '';

      const popupContent = `
        <div style="font-family:sans-serif; min-width:210px; color:#1e293b;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <strong style="color:${color}; font-size:1.05rem;">${inc.incident_code}</strong>
            <span style="font-size:0.75rem; background:#e2e8f0; padding:2px 6px; border-radius:4px; font-weight:bold;">${inc.urgency_level}</span>
          </div>
          ${photoThumb}
          <div style="font-weight:600; font-size:0.88rem; margin-bottom:4px;">${inc.emergency_type}: ${inc.title}</div>
          <div style="font-size:0.8rem; color:#64748b; margin-bottom:6px;"><i class="fa-solid fa-location-dot"></i> ${inc.location_address}</div>
          <div style="font-size:0.78rem; margin-bottom:8px;">
            <strong>Affected:</strong> ${inc.people_affected} | <strong>Trapped:</strong> ${inc.trapped_count}
          </div>
          <a href="/incident/${inc.id}" style="
            display:inline-block;
            background:#2563eb;
            color:white;
            text-decoration:none;
            padding:6px 10px;
            border-radius:4px;
            font-size:0.78rem;
            font-weight:bold;
            text-align:center;
            width:100%;
          ">View Multi-Agent Plan &rarr;</a>
        </div>
      `;

      marker.bindPopup(popupContent);
      this.markersLayer.addLayer(marker);
    });

    if (bounds.length > 0) {
      this.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    }
  }
};

