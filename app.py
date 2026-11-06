import os
import json
import random
import string
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from config import Config
import database
from agents.coordinator_agent import CoordinatorAgent
from email_service import EmailNotificationService
from agent_orchestrator import run_all_agents, get_agent_executions, get_agent_registry, AGENT_REGISTRY
from agents.master_orchestrator import (
    MasterCoordinatorAgent, AgentMessageBus, get_all_agents_status,
    MonitoringAgent, MaintenanceAgent, DatabaseAgent, TrackingAgent,
    EmergencyDetectionAgent, TriageAgent, ResourceCoordinationAgent,
    SYSTEM_AGENTS_METADATA
)
from ai_operator import AIOperatorEngine

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Support Public HTTPS & Reverse Proxy Deployments (Req: Deployable on public HTTPS server)
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
except Exception:
    pass

# Ensure database is initialized and start Autonomous AI Operator daemon
with app.app_context():
    database.init_db()
    operator_engine = AIOperatorEngine.get_instance()
    operator_engine.start_worker()

def generate_incident_code():
    """Generates a human-friendly unique incident code like INC-2026-8421."""
    rand_digits = ''.join(random.choices(string.digits, k=4))
    return f"INC-2026-{rand_digits}"

@app.context_processor
def inject_global_data():
    """Injects project metadata into all templates."""
    return {
        'project_name': Config.PROJECT_NAME,
        'project_title': Config.PROJECT_TITLE,
        'project_code': Config.PROJECT_CODE,
        'team_name': Config.TEAM_NAME,
        'team_members': Config.TEAM_MEMBERS,
        'college': Config.COLLEGE,
        'mentor': Config.MENTOR,
        'event_date': Config.EVENT_DATE,
        'agencies': Config.AGENCIES,
        'active_db': database.get_db_type(),
        'app_base_url': Config.APP_BASE_URL
    }

# ====================================================================
# HTML PAGE ROUTES
# ====================================================================

@app.route('/')
def index():
    """Landing portal with quick reporting, SOS trigger, and stats."""
    stats = get_dashboard_stats()
    recent_incidents = database.query_db(
        "SELECT * FROM incidents ORDER BY reported_at DESC LIMIT 5"
    )
    return render_template('index.html', stats=stats, recent_incidents=recent_incidents)

@app.route('/report')
def report_page():
    """Public Emergency Report page with interactive map coordinate picker."""
    return render_template('report.html')

@app.route('/dashboard')
def dashboard_page():
    """Admin & Officer Command Center dashboard."""
    stats = get_dashboard_stats()
    db_type = database.get_db_type()
    return render_template('dashboard.html', stats=stats, db_type=db_type)

@app.route('/incident/<int:incident_id>')
def incident_detail_page(incident_id):
    """Detailed multi-agent coordination analysis for a specific incident."""
    incident = database.query_db("SELECT * FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        flash(f"Incident #{incident_id} not found.", "danger")
        return redirect(url_for('dashboard_page'))

    recommendations = database.query_db(
        "SELECT * FROM agent_recommendations WHERE incident_id = %s ORDER BY id ASC",
        (incident_id,)
    )
    for rec in recommendations:
        if rec.get('suggested_actions'):
            try:
                rec['actions_list'] = json.loads(rec['suggested_actions'])
            except Exception:
                rec['actions_list'] = [rec['suggested_actions']]
        else:
            rec['actions_list'] = []

    alerts = database.query_db(
        "SELECT * FROM simulated_alerts WHERE incident_id = %s ORDER BY id ASC",
        (incident_id,)
    )

    logs = database.query_db(
        "SELECT * FROM audit_logs WHERE incident_id = %s ORDER BY timestamp DESC",
        (incident_id,)
    )

    email_logs = database.query_db(
        "SELECT * FROM email_notifications WHERE incident_id = %s ORDER BY sent_at DESC",
        (incident_id,)
    )

    # Check if duplicate and fetch parent
    parent_incident = None
    if incident.get('is_duplicate') and incident.get('parent_incident_id'):
        parent_incident = database.query_db(
            "SELECT * FROM incidents WHERE id = %s",
            (incident['parent_incident_id'],),
            one=True
        )

    # Fetch child duplicates
    child_duplicates = database.query_db(
        "SELECT * FROM incidents WHERE parent_incident_id = %s",
        (incident_id,)
    )

    return render_template(
        'incident_detail.html',
        incident=incident,
        recommendations=recommendations,
        alerts=alerts,
        logs=logs,
        email_logs=email_logs,
        parent_incident=parent_incident,
        child_duplicates=child_duplicates
    )

@app.route('/incident/<int:incident_id>/export')
def export_incident_report(incident_id):
    """Renders a clean printable After-Action Review (AAR) debrief."""
    incident = database.query_db("SELECT * FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        flash(f"Incident #{incident_id} not found.", "danger")
        return redirect(url_for('dashboard_page'))

    recommendations = database.query_db(
        "SELECT * FROM agent_recommendations WHERE incident_id = %s ORDER BY id ASC",
        (incident_id,)
    )
    for rec in recommendations:
        if rec.get('suggested_actions'):
            try:
                rec['actions_list'] = json.loads(rec['suggested_actions'])
            except Exception:
                rec['actions_list'] = [rec['suggested_actions']]
        else:
            rec['actions_list'] = []

    alerts = database.query_db("SELECT * FROM simulated_alerts WHERE incident_id = %s ORDER BY id ASC", (incident_id,))
    logs = database.query_db("SELECT * FROM audit_logs WHERE incident_id = %s ORDER BY timestamp DESC", (incident_id,))
    email_logs = database.query_db("SELECT * FROM email_notifications WHERE incident_id = %s ORDER BY sent_at DESC", (incident_id,))

    return render_template(
        'export_report.html',
        incident=incident,
        recommendations=recommendations,
        alerts=alerts,
        logs=logs,
        email_logs=email_logs,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/track')
@app.route('/track/<string:incident_code>')
def track_page(incident_code=None):
    """
    Public Citizen Incident Tracking Page (Req: Fix tracking link issue).
    Accessible via public HTTPS or mobile with instant tracking ID lookup.
    """
    incident_data = None
    alerts = []
    if incident_code:
        code = incident_code.strip().upper()
        res = TrackingAgent.get_tracking_info(code)
        if res:
            incident_data = res.get('incident')
            alerts = res.get('alerts', [])
    return render_template('track.html', initial_code=incident_code, incident=incident_data, alerts=alerts)

@app.route('/agents')
def agents_dashboard_page():
    """Autonomous Multi-Agent System Live Control & Telemetry Dashboard."""
    return render_template('agents_dashboard.html')

@app.route('/api/system/agents', methods=['GET'])
def api_system_agents():
    """Returns real-time health, tasks, and telemetry for all 10 specialized AI agents."""
    return jsonify(get_all_agents_status())

@app.route('/api/system/messages', methods=['GET'])
def api_system_messages():
    """Returns the recent live feed of inter-agent messages from the message bus."""
    limit = request.args.get('limit', 50, type=int)
    incident_id = request.args.get('incident_id', None, type=int)
    msgs = AgentMessageBus.get_recent_messages(limit=limit, incident_id=incident_id)
    return jsonify({'success': True, 'messages': msgs, 'total': len(msgs)})

@app.route('/api/system/ping', methods=['POST'])
def api_system_ping():
    """Pings all 10 agents and records telemetry heartbeat."""
    metrics = MonitoringAgent.probe_system_health()
    AgentMessageBus.publish('Monitoring Agent', 'Master Coordinator Agent', 'HEARTBEAT_PING',
                            f"System health probe: {metrics['status']} (Latency: {metrics['db_latency_ms']}ms)")
    return jsonify({'success': True, **metrics})

@app.route('/api/system/maintenance', methods=['POST'])
def api_system_maintenance():
    """Runs automated Maintenance Agent self-diagnostics and safe auto-fixes."""
    res = MaintenanceAgent.run_diagnostics()
    AgentMessageBus.publish('Maintenance Agent', 'Master Coordinator Agent', 'MAINTENANCE_SCAN',
                            f"Maintenance scan completed: {len(res['checks'])} checks ({res['diagnostic_time_ms']}ms)")
    return jsonify({'success': True, **res})

# ====================================================================
# AUTONOMOUS AI OPERATOR APIs (Req: AI to operate the project)
# ====================================================================

@app.route('/api/operator/status', methods=['GET'])
def api_operator_status():
    """Returns the live operational status, autonomous mode, and recent decisions of the AI Operator."""
    engine = AIOperatorEngine.get_instance()
    return jsonify({'success': True, **engine.get_status()})

@app.route('/api/operator/toggle', methods=['POST'])
def api_operator_toggle():
    """Toggles AI Autonomous Auto-Pilot Mode (ON/OFF)."""
    engine = AIOperatorEngine.get_instance()
    is_auto = engine.toggle_autonomous()
    return jsonify({'success': True, 'autonomous_mode': is_auto, 'message': f"Autonomous AI Operation mode {'ENABLED' if is_auto else 'DISABLED'}."})

@app.route('/api/operator/command', methods=['POST'])
def api_operator_command():
    """Executes natural language operational directives through the AI Operator Copilot."""
    data = request.get_json() or request.form.to_dict() or {}
    command_text = data.get('command', '').strip()
    engine = AIOperatorEngine.get_instance()
    result = engine.execute_commander_command(command_text)
    return jsonify(result)

@app.route('/api/operator/cycle', methods=['POST'])
def api_operator_cycle():
    """Triggers an immediate autonomous operational sweep across all sectors."""
    engine = AIOperatorEngine.get_instance()
    res = engine.run_operational_cycle()
    return jsonify({'success': True, **res})

@app.route('/api/track/<string:incident_code>', methods=['GET'])
def api_track_incident(incident_code):
    """Allows citizens to query the live operational status of their report."""
    code = incident_code.strip().upper()
    incident = database.query_db("SELECT * FROM incidents WHERE incident_code = %s", (code,), one=True)
    if not incident:
        return jsonify({'success': False, 'error': f"Incident code '{code}' not found."}), 404

    alerts = database.query_db(
        "SELECT agency_name, alert_channel, status FROM simulated_alerts WHERE incident_id = %s",
        (incident['id'],)
    )

    return jsonify({
        'success': True,
        'incident': {
            'incident_code': incident['incident_code'],
            'title': incident['title'],
            'emergency_type': incident['emergency_type'],
            'location_address': incident['location_address'],
            'urgency_level': incident['urgency_level'],
            'status': incident['status'],
            'reported_at': incident['reported_at'],
            'is_sos': bool(incident['is_sos']),
            'is_duplicate': bool(incident['is_duplicate'])
        },
        'alerts': alerts
    })

@app.route('/resources')
def resources_page():
    """Agency resource inventory & readiness status board."""
    resources = database.query_db("SELECT * FROM resources ORDER BY agency_id ASC, id ASC")
    return render_template('resources.html', resources=resources)

@app.route('/alerts')
def alerts_page():
    """Simulated emergency broadcast transmissions and audit logs."""
    alerts = database.query_db(
        """SELECT a.*, i.incident_code, i.emergency_type, i.location_address, i.urgency_level
           FROM simulated_alerts a
           JOIN incidents i ON a.incident_id = i.id
           ORDER BY a.sent_at DESC LIMIT 50"""
    )
    logs = database.query_db("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 40")
    return render_template('alerts.html', alerts=alerts, logs=logs)

@app.route('/docs')
def docs_page():
    """Hackathon documentation, architecture, team details, and test matrix."""
    return render_template('docs.html')

# ====================================================================
# REST APIS FOR MULTI-AGENT SYSTEM & FRONTEND
# ====================================================================

def get_dashboard_stats():
    """Calculates summary KPIs for dashboard."""
    total_incidents = database.query_db("SELECT COUNT(*) as cnt FROM incidents", one=True)['cnt']
    critical_count = database.query_db("SELECT COUNT(*) as cnt FROM incidents WHERE urgency_level = 'CRITICAL' AND status NOT IN ('Resolved', 'Closed')", one=True)['cnt']
    sos_count = database.query_db("SELECT COUNT(*) as cnt FROM incidents WHERE is_sos = 1", one=True)['cnt']
    active_count = database.query_db("SELECT COUNT(*) as cnt FROM incidents WHERE status IN ('Reported', 'Verified', 'Dispatched', 'In Progress')", one=True)['cnt']
    resolved_count = database.query_db("SELECT COUNT(*) as cnt FROM incidents WHERE status IN ('Resolved', 'Closed')", one=True)['cnt']
    dispatches_count = database.query_db("SELECT COUNT(*) as cnt FROM simulated_alerts WHERE status IN ('APPROVED', 'DISPATCHED', 'ACKNOWLEDGED')", one=True)['cnt']
    
    return {
        'total': total_incidents,
        'critical': critical_count,
        'sos': sos_count,
        'active': active_count,
        'resolved': resolved_count,
        'dispatches': dispatches_count
    }

@app.route('/api/stats')
def api_stats():
    return jsonify({'success': True, 'stats': get_dashboard_stats()})

@app.route('/api/incidents', methods=['GET'])
def api_get_incidents():
    """Fetches list of incidents with optional filtering."""
    status_filter = request.args.get('status')
    type_filter = request.args.get('type')
    urgency_filter = request.args.get('urgency')
    sos_filter = request.args.get('sos')

    query = "SELECT * FROM incidents WHERE 1=1"
    params = []

    if status_filter and status_filter != 'all':
        query += " AND status = %s"
        params.append(status_filter)
    if type_filter and type_filter != 'all':
        query += " AND emergency_type = %s"
        params.append(type_filter)
    if urgency_filter and urgency_filter != 'all':
        query += " AND urgency_level = %s"
        params.append(urgency_filter)
    if sos_filter == '1':
        query += " AND is_sos = 1"

    query += " ORDER BY CASE urgency_level WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, reported_at DESC"
    incidents = database.query_db(query, params)
    return jsonify({'success': True, 'incidents': incidents})

@app.route('/api/incident/<int:incident_id>', methods=['GET'])
def api_get_incident(incident_id):
    """Returns single incident with recommendations, alerts, and logs."""
    incident = database.query_db("SELECT * FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        return jsonify({'success': False, 'error': 'Incident not found'}), 404

    recommendations = database.query_db(
        "SELECT * FROM agent_recommendations WHERE incident_id = %s", (incident_id,)
    )
    for rec in recommendations:
        if rec.get('suggested_actions'):
            try:
                rec['actions_list'] = json.loads(rec['suggested_actions'])
            except Exception:
                rec['actions_list'] = [rec['suggested_actions']]

    alerts = database.query_db("SELECT * FROM simulated_alerts WHERE incident_id = %s", (incident_id,))
    logs = database.query_db("SELECT * FROM audit_logs WHERE incident_id = %s ORDER BY timestamp DESC", (incident_id,))

    return jsonify({
        'success': True,
        'incident': incident,
        'recommendations': recommendations,
        'alerts': alerts,
        'logs': logs
    })

@app.route('/api/report', methods=['POST'])
def api_submit_report():
    """
    Submits a new emergency report, executes the AI multi-agent coordination pipeline,
    records recommendations and simulated alerts in the database.
    """
    data = request.get_json() or request.form.to_dict()

    emergency_type = data.get('emergency_type', 'General Emergency').strip()
    title = data.get('title', f"{emergency_type} Emergency").strip()
    description = data.get('description', '').strip()
    location_address = data.get('location_address', 'Location not specified').strip()
    landmark = data.get('landmark', '').strip()
    reporter_name = data.get('reporter_name', 'Anonymous Citizen').strip() or 'Anonymous Citizen'
    reporter_email = data.get('reporter_email', '').strip()
    reporter_contact = data.get('reporter_contact', 'Simulated Contact').strip() or 'Simulated Contact'
    source = data.get('source', 'Citizen Web Form')

    # Coordinates
    try:
        latitude = float(data.get('latitude', 15.9054))
        longitude = float(data.get('longitude', 80.4682))
    except (ValueError, TypeError):
        latitude = 15.9054
        longitude = 80.4682

    # Counts
    try:
        people_affected = int(data.get('people_affected', 1))
    except (ValueError, TypeError):
        people_affected = 1

    try:
        trapped_count = int(data.get('trapped_count', 0))
    except (ValueError, TypeError):
        trapped_count = 0

    try:
        injured_count = int(data.get('injured_count', 0))
    except (ValueError, TypeError):
        injured_count = 0

    is_sos = 1 if str(data.get('is_sos', '0')).lower() in ['1', 'true', 'yes'] else 0
    incident_code = generate_incident_code()

    # Live Location Photo Handling
    photo_url = data.get('photo_url')
    photo_data = data.get('photo_data')  # Base64 string from live camera/canvas

    if photo_data and str(photo_data).startswith('data:image'):
        try:
            header, encoded = photo_data.split(',', 1)
            file_ext = 'png' if 'png' in header else 'jpg'
            # Save the photo specifically named with the incident code / ID (Requirement 9)
            file_name = f"{incident_code}_live_scene.{file_ext}"
            file_path = os.path.join(app.root_path, 'static', 'uploads', file_name)
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(encoded))
            photo_url = f"/static/uploads/{file_name}"
        except Exception as e:
            print("Error decoding image:", e)

    if not photo_url:
        em_lower = emergency_type.lower()
        if 'flood' in em_lower or 'water' in em_lower:
            photo_url = '/static/images/flood_scene.svg'
        elif 'fire' in em_lower or 'smoke' in em_lower:
            photo_url = '/static/images/fire_scene.svg'
        elif 'accident' in em_lower or 'collision' in em_lower:
            photo_url = '/static/images/accident_scene.svg'
        elif 'earthquake' in em_lower or 'collapse' in em_lower:
            photo_url = '/static/images/earthquake_scene.svg'
        else:
            photo_url = '/static/images/flood_scene.svg'

    incident_dict = {
        'incident_code': incident_code,
        'emergency_type': emergency_type,
        'title': title,
        'description': description,
        'location_address': location_address,
        'landmark': landmark,
        'latitude': latitude,
        'longitude': longitude,
        'people_affected': people_affected,
        'trapped_count': trapped_count,
        'injured_count': injured_count,
        'is_sos': is_sos,
        'photo_url': photo_url,
        'reporter_name': reporter_name,
        'reporter_email': reporter_email,
        'reporter_contact': reporter_contact,
        'source': source
    }

    # Fetch active incidents and resources for initial urgency calculation
    existing_incidents = database.query_db(
        "SELECT id, incident_code, emergency_type, title, description, location_address, latitude, longitude, urgency_level, status FROM incidents WHERE status NOT IN ('Resolved', 'Closed')"
    )

    # Quick urgency pre-calculation for incident insertion (Coordinator does full analysis later)
    urgency_score, urgency_level, urgency_reasons = CoordinatorAgent.calculate_urgency(incident_dict)
    from agents.duplicate_agent import DuplicateDetectionAgent
    dup_result = DuplicateDetectionAgent.evaluate(incident_dict, existing_incidents)
    incident_dict['is_duplicate'] = 1 if dup_result['is_duplicate'] else 0
    incident_dict['parent_incident_id'] = dup_result['parent_id']

    # Insert Incident into database FIRST (so agents can reference it)
    insert_sql = """
    INSERT INTO incidents (
        incident_code, emergency_type, title, description, location_address, landmark,
        latitude, longitude, urgency_level, urgency_score, urgency_reasons,
        people_affected, trapped_count, injured_count, status, is_sos, is_duplicate,
        parent_incident_id, reporter_name, reporter_email, reporter_contact, source, confidence_score, photo_url
    ) VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s
    )
    """
    incident_id = database.execute_db(insert_sql, (
        incident_code,
        emergency_type,
        title,
        description,
        location_address,
        landmark,
        latitude,
        longitude,
        urgency_level,
        urgency_score,
        urgency_reasons,
        people_affected,
        trapped_count,
        injured_count,
        'Reported',
        is_sos,
        incident_dict['is_duplicate'],
        incident_dict['parent_incident_id'],
        reporter_name,
        reporter_email,
        reporter_contact,
        source,
        0.95,
        photo_url
    ))

    # Record Audit Log for report submission
    database.execute_db(
        "INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details) VALUES (%s, %s, %s, %s, %s)",
        (
            incident_id,
            reporter_name,
            'Citizen / Reporter',
            'REPORT_SUBMITTED',
            f"Emergency reported ({emergency_type}) at {location_address}. Urgent SOS: {'YES' if is_sos else 'NO'}."
        )
    )

    # ===================================================================
    # AUTO-TRIGGER MULTI-AGENT ORCHESTRATOR (Req 2, 3, 4)
    # All agents execute automatically with concurrent threading
    # ===================================================================
    agent_result = run_all_agents(incident_id, force=False)

    # Inter-Agent Message Bus Traffic (10-Agent System Communication)
    AgentMessageBus.publish('Emergency Detection Agent', 'Master Coordinator Agent', 'EMERGENCY_DETECTED',
                            f"Intake verified: {emergency_type} at {location_address}. SOS: {'YES' if is_sos else 'NO'}.", incident_id)
    AgentMessageBus.publish('Master Coordinator Agent', 'Triage Agent', 'REQUEST_TRIAGE',
                            f"Evaluate urgency and casualties ({injured_count} injured, {trapped_count} trapped).", incident_id)
    AgentMessageBus.publish('Triage Agent', 'Master Coordinator Agent', 'TRIAGE_COMPLETE',
                            f"Urgency evaluated: {urgency_score}/100 ({urgency_level}).", incident_id)
    AgentMessageBus.publish('Master Coordinator Agent', 'Tracking Agent', 'TRACKING_REGISTERED',
                            f"Incident {incident_code} tracking active at /track/{incident_code}.", incident_id)
    AgentMessageBus.publish('Master Coordinator Agent', 'Notification Agent', 'DISPATCH_NOTIFICATIONS',
                            f"Routing Gmail SMTP dispatches to duty commanders.", incident_id)

    # Trigger Officer Email Notification (Req 17: email after successful processing)
    incident_dict['urgency_level'] = urgency_level
    incident_dict['urgency_score'] = urgency_score
    email_result = EmailNotificationService.send_new_incident_notification(incident_dict, incident_id)

    # Trigger User Confirmation Email with public tracking link
    user_confirm_result = None
    if reporter_email and '@' in reporter_email:
        user_confirm_result = EmailNotificationService.send_user_confirmation_email(
            incident_dict, incident_id, reporter_email
        )

    base_url = Config.APP_BASE_URL.rstrip('/')
    tracking_url = f"{base_url}/track/{incident_code}"

    return jsonify({
        'success': True,
        'incident_id': incident_id,
        'incident_code': incident_code,
        'tracking_url': tracking_url,
        'urgency_score': urgency_score,
        'urgency_level': urgency_level,
        'is_duplicate': bool(incident_dict['is_duplicate']),
        'parent_id': incident_dict['parent_incident_id'],
        'agent_execution': agent_result,
        'email_notifications': email_result,
        'user_confirmation': user_confirm_result,
        'email_sender': Config.GMAIL_USER or 'Not Configured',
        'public_bulletin': agent_result.get('public_bulletin', ''),
        'recommendations_count': agent_result.get('completed_count', 0),
        'alerts_count': agent_result.get('alerts_generated', 0),
        'message': f"Emergency {incident_code} successfully reported. 10-Agent pipeline active. Officer alerts dispatched."
    })

@app.route('/api/sos', methods=['POST'])
def api_sos_trigger():
    """
    Urgent 1-Click SOS Trigger:
    Instantly fires a critical distress emergency with high priority.
    """
    data = request.get_json() or {}
    try:
        lat = float(data.get('latitude', 15.9054))
        lng = float(data.get('longitude', 80.4682))
    except (ValueError, TypeError):
        lat = 15.9054
        lng = 80.4682

    sos_payload = {
        'emergency_type': data.get('emergency_type', 'Critical SOS Alert'),
        'title': '🚨 CRITICAL CITIZEN SOS DISTRESS SIGNAL',
        'description': data.get('description', 'Instant SOS triggered via 1-click distress beacon. Urgent rescue and police assistance requested.'),
        'location_address': data.get('location_address', f'GPS Coordinates: {lat:.4f}, {lng:.4f}'),
        'landmark': data.get('landmark', 'Immediate Geolocation Pin'),
        'latitude': lat,
        'longitude': lng,
        'people_affected': int(data.get('people_affected', 1)),
        'trapped_count': int(data.get('trapped_count', 1)),
        'injured_count': int(data.get('injured_count', 0)),
        'is_sos': 1,
        'reporter_name': data.get('reporter_name', 'Distressed Citizen (SOS Beacon)'),
        'reporter_contact': 'SOS Emergency Channel',
        'source': 'Citizen Urgent SOS Beacon'
    }

    # Pass to report intake
    with app.test_request_context(json=sos_payload):
        return api_submit_report()

@app.route('/api/incident/<int:incident_id>/status', methods=['POST'])
def api_update_incident_status(incident_id):
    """
    Allows authorized officers to update incident status:
    'Reported', 'Verified', 'Dispatched', 'In Progress', 'Resolved', 'Closed'
    """
    data = request.get_json() or request.form.to_dict()
    new_status = data.get('status')
    officer_name = data.get('officer_name', 'Duty Commander Officer')
    note = data.get('note', '')

    valid_statuses = ['Reported', 'Verified', 'Dispatched', 'In Progress', 'Resolved', 'Closed']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': f"Invalid status. Must be one of: {valid_statuses}"}), 400

    incident = database.query_db("SELECT * FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        return jsonify({'success': False, 'error': 'Incident not found'}), 404

    old_status = incident['status']
    database.execute_db(
        "UPDATE incidents SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (new_status, incident_id)
    )

    # Record Audit Log
    database.execute_db(
        "INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details) VALUES (%s, %s, %s, %s, %s)",
        (
            incident_id,
            officer_name,
            'Incident Officer',
            'STATUS_UPDATED',
            f"Status updated from '{old_status}' to '{new_status}'. Officer note: {note or 'Standard progression'}"
        )
    )

    # Trigger Officer Email Notification on Status Change (Req: Send email notifications when incident status changes)
    email_result = EmailNotificationService.send_status_change_notification(
        incident, old_status, new_status, officer_name, note
    )

    return jsonify({
        'success': True,
        'incident_id': incident_id,
        'old_status': old_status,
        'new_status': new_status,
        'email_notifications': email_result,
        'message': f"Incident #{incident_id} status updated to '{new_status}'."
    })

@app.route('/api/incident/<int:incident_id>/emails', methods=['GET'])
def api_get_incident_emails(incident_id):
    """Fetches all email notification dispatch records for a specific incident."""
    incident = database.query_db("SELECT id, incident_code FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        return jsonify({'success': False, 'error': 'Incident not found'}), 404
    emails = EmailNotificationService.get_incident_emails(incident_id)
    return jsonify({
        'success': True,
        'incident_id': incident_id,
        'incident_code': incident['incident_code'],
        'emails': emails
    })

@app.route('/api/email/test', methods=['POST'])
def api_test_email():
    """
    Test Email Diagnostic API (Req 9: Add a Test Email button in the admin dashboard).
    Sends a test email to verify SMTP gateway configuration and environment settings.
    """
    data = request.get_json() or request.form.to_dict() or {}
    recipient_email = data.get('recipient_email', '').strip()
    result = EmailNotificationService.send_test_email(recipient_email or None)
    return jsonify(result)

# ====================================================================
# MULTI-AGENT ORCHESTRATOR APIs (Req 8, 9, 10, 19)
# ====================================================================

@app.route('/api/agents/registry', methods=['GET'])
def api_agent_registry():
    """Returns the list of all registered AI agents and their metadata."""
    return jsonify({
        'success': True,
        'agents': get_agent_registry(),
        'total_agents': len(AGENT_REGISTRY)
    })

@app.route('/api/incident/<int:incident_id>/agents', methods=['GET'])
def api_get_agent_executions(incident_id):
    """
    Fetch per-agent execution status for an incident (Req 8, 9, 10).
    Returns each agent's status, response, execution time, and errors.
    """
    incident = database.query_db("SELECT id, incident_code FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        return jsonify({'success': False, 'error': 'Incident not found'}), 404

    executions = get_agent_executions(incident_id)
    execution_list = []
    for ex in executions:
        ex_dict = dict(ex)
        # Parse response_json for frontend consumption
        if ex_dict.get('response_json'):
            try:
                ex_dict['response'] = json.loads(ex_dict['response_json'])
            except Exception:
                ex_dict['response'] = None
        else:
            ex_dict['response'] = None
        # Find icon/color from registry
        for reg in AGENT_REGISTRY:
            if reg['agent_id'] == ex_dict.get('agent_id'):
                ex_dict['icon'] = reg['icon']
                ex_dict['color'] = reg['color']
                break
        execution_list.append(ex_dict)

    return jsonify({
        'success': True,
        'incident_id': incident_id,
        'incident_code': incident['incident_code'],
        'executions': execution_list,
        'total_agents': len(AGENT_REGISTRY),
        'completed': sum(1 for e in execution_list if e.get('status') == 'COMPLETED'),
        'failed': sum(1 for e in execution_list if e.get('status') == 'FAILED'),
        'pending': sum(1 for e in execution_list if e.get('status') in ('PENDING', 'RUNNING'))
    })

@app.route('/api/incident/<int:incident_id>/agents/run', methods=['POST'])
def api_run_all_agents(incident_id):
    """
    Run All Agents button endpoint (Req 19).
    Manually triggers re-execution of all 5 agents for an incident.
    force=True bypasses duplicate execution guard.
    """
    incident = database.query_db("SELECT id FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        return jsonify({'success': False, 'error': 'Incident not found'}), 404

    data = request.get_json() or {}
    force = data.get('force', True)  # Default to force=True for manual button

    result = run_all_agents(incident_id, force=force)

    # Trigger email notification after successful agent processing (Req 17)
    if result.get('success') and result.get('status') != 'ALL_FAILED':
        inc = database.query_db("SELECT * FROM incidents WHERE id = %s", (incident_id,), one=True)
        if inc:
            inc_dict = dict(inc)
            EmailNotificationService.send_new_incident_notification(inc_dict, incident_id)

    return jsonify(result)

@app.route('/api/incident/<int:incident_id>/operate-auto', methods=['POST'])
def api_operate_incident_auto(incident_id):
    """
    Agentic AI Autonomous Operations Execution endpoint.
    Automatically steps through multi-agency response, dispatches alerts,
    advances status, logs audit trails, and transmits real Gmail status notifications.
    """
    data = request.get_json() or {}
    target_status = data.get('target_status', 'Dispatched')
    engine = AIOperatorEngine.get_instance()
    res = engine.operate_incident_automatically(incident_id, target_status=target_status)
    return jsonify(res)

@app.route('/api/incident/<int:incident_id>/photo', methods=['POST'])
def api_attach_incident_photo(incident_id):
    """
    Saves and attaches a captured live camera photo named with the incident ID (Req 8 & 9).
    """
    incident = database.query_db("SELECT * FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        return jsonify({'success': False, 'error': 'Incident not found'}), 404

    data = request.get_json() or request.form.to_dict()
    photo_data = data.get('photo_data')
    inc_code = incident['incident_code']

    if not photo_data or not str(photo_data).startswith('data:image'):
        return jsonify({'success': False, 'error': 'Invalid or missing image data'}), 400

    try:
        header, encoded = photo_data.split(',', 1)
        file_ext = 'png' if 'png' in header else 'jpg'
        # Saved with Incident ID (Req 9)
        file_name = f"incident_{incident_id}_{inc_code}_scene.{file_ext}"
        file_path = os.path.join(app.root_path, 'static', 'uploads', file_name)
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(encoded))
        photo_url = f"/static/uploads/{file_name}"

        database.execute_db(
            "UPDATE incidents SET photo_url = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (photo_url, incident_id)
        )

        database.execute_db(
            "INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details) VALUES (%s, %s, %s, %s, %s)",
            (
                incident_id,
                'Field Reporter',
                'Camera Operator',
                'LIVE_PHOTO_ATTACHED',
                f"Live location photo captured and attached to incident #{incident_id} ({file_name})."
            )
        )

        return jsonify({
            'success': True,
            'incident_id': incident_id,
            'incident_code': inc_code,
            'photo_url': photo_url,
            'message': f"Photo attached successfully to incident #{incident_id}."
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f"Failed to save photo: {str(e)}"}), 500

@app.route('/api/alert/<int:alert_id>/action', methods=['POST'])
def api_alert_action(alert_id):
    """
    Allows officers to approve, dispatch, or acknowledge a simulated alert.
    Human-in-the-Loop decision point.
    """
    data = request.get_json() or request.form.to_dict()
    action = data.get('action', 'APPROVE').upper()
    officer_name = data.get('officer_name', 'Duty Dispatch Officer')

    alert = database.query_db("SELECT * FROM simulated_alerts WHERE id = %s", (alert_id,), one=True)
    if not alert:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404

    if action == 'APPROVE':
        new_status = 'APPROVED'
    elif action == 'DISPATCH':
        new_status = 'DISPATCHED'
    elif action == 'ACKNOWLEDGE':
        new_status = 'ACKNOWLEDGED'
    else:
        new_status = 'APPROVED'

    database.execute_db(
        "UPDATE simulated_alerts SET status = %s, officer_approved_by = %s, acknowledged_at = CURRENT_TIMESTAMP WHERE id = %s",
        (new_status, officer_name, alert_id)
    )

    # Audit log
    database.execute_db(
        "INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details) VALUES (%s, %s, %s, %s, %s)",
        (
            alert['incident_id'],
            officer_name,
            'Dispatch Officer',
            'SIMULATED_ALERT_APPROVED',
            f"Officer approved simulated dispatch for {alert['agency_name']} via {alert['alert_channel']} with status '{new_status}'."
        )
    )

    return jsonify({
        'success': True,
        'alert_id': alert_id,
        'new_status': new_status,
        'message': f"Simulated alert #{alert_id} updated to {new_status}."
    })

@app.route('/api/resources', methods=['GET'])
def api_get_resources():
    """Fetches all resources with agency grouping."""
    resources = database.query_db("SELECT * FROM resources ORDER BY agency_id ASC, id ASC")
    return jsonify({'success': True, 'resources': resources})

@app.route('/api/resource/<int:res_id>/update', methods=['POST'])
def api_update_resource(res_id):
    """Updates resource availability or status."""
    data = request.get_json() or request.form.to_dict()
    status = data.get('status', 'Available')
    avail = int(data.get('available_capacity', 1))

    database.execute_db(
        "UPDATE resources SET status = %s, available_capacity = %s, last_updated = CURRENT_TIMESTAMP WHERE id = %s",
        (status, avail, res_id)
    )
    return jsonify({'success': True, 'message': 'Resource updated successfully.'})

# ====================================================================
# HACKATHON DEMO SCENARIO LOADER (As specified in Section 13.1 of docs)
# ====================================================================

@app.route('/api/demo/load-scenario', methods=['POST'])
def api_load_demo_scenario():
    """
    Loads the official hackathon test scenario:
    Fictional flood disaster across three neighborhoods with duplicate detection,
    critical rooftop rescues, hospital alerts, and police perimeter cordons.
    """
    # Clear existing demo incidents first
    database.execute_db("DELETE FROM agent_executions")
    database.execute_db("DELETE FROM simulated_alerts")
    database.execute_db("DELETE FROM agent_recommendations")
    database.execute_db("DELETE FROM audit_logs WHERE action_type != 'SYSTEM_INITIALIZED'")
    database.execute_db("DELETE FROM incidents")

    # Reset resources
    database.execute_db("UPDATE resources SET available_capacity = total_capacity, status = 'Available'")

    # Scenario 1: Flood Report in Neighborhood A (Bapatla East Colony)
    inc1 = {
        'emergency_type': 'Flood',
        'title': 'Severe Flash Flood Inundation & Trapped Civilians',
        'description': 'Heavy downpour caused floodwaters to breach the drainage canal. Water is over 4 feet high and rapidly rising into residential ground floors. 4 senior citizens trapped on roof.',
        'location_address': 'East Colony, Ward 4, Near Water Tank, Bapatla',
        'landmark': 'Overhead Municipal Water Tank',
        'latitude': 15.9080,
        'longitude': 80.4730,
        'people_affected': 25,
        'trapped_count': 4,
        'injured_count': 1,
        'is_sos': 0,
        'photo_url': '/static/images/flood_scene.svg',
        'reporter_name': 'Ramesh Kumar (Resident)',
        'reporter_contact': '98480-12345',
        'source': 'Citizen Web Form'
    }

    # Scenario 2: Potential Duplicate Report in Neighborhood A (Same flood, 200m away, different phone)
    inc2_dup = {
        'emergency_type': 'Flood',
        'title': 'Flood water entering houses near water tank',
        'description': 'Water level rising quickly near municipal tank. Families stranded on top floor terrace. Please send rescue boats immediately.',
        'location_address': 'Ward 4, East Colony Main Road, Bapatla',
        'landmark': 'Near Water Tank',
        'latitude': 15.9090,
        'longitude': 80.4740,
        'people_affected': 20,
        'trapped_count': 3,
        'injured_count': 0,
        'is_sos': 0,
        'photo_url': '/static/images/flood_scene.svg',
        'reporter_name': 'Lakshmi Devi (Local Shopkeeper)',
        'reporter_contact': '98480-54321',
        'source': 'Citizen Web Form'
    }

    # Scenario 3: Neighborhood B - Urgent Critical SOS: Fire breakout caused by electrical short circuit in flood
    inc3_sos = {
        'emergency_type': 'Fire',
        'title': '🚨 SOS: Electrical Transformer Explosion & Residential Blaze',
        'description': 'Submerged transformer exploded causing active fire in 2-story building. Thick black smoke, children trapped on balcony!',
        'location_address': 'Market Yard Road, Sector 2, Bapatla',
        'landmark': 'Old Grain Market Complex',
        'latitude': 15.9150,
        'longitude': 80.4610,
        'people_affected': 15,
        'trapped_count': 5,
        'injured_count': 2,
        'is_sos': 1,
        'photo_url': '/static/images/fire_scene.svg',
        'reporter_name': 'K. Suresh (Distressed Citizen)',
        'reporter_contact': 'SOS Emergency Trigger',
        'source': 'Citizen Urgent SOS Beacon'
    }

    # Scenario 4: Neighborhood C - High-Impact Highway Accident on Evacuation Route
    inc4_acc = {
        'emergency_type': 'Accident',
        'title': 'Multi-Vehicle Collision on Evacuation Bypass Highway',
        'description': 'Supply transport truck collided with passenger bus due to poor visibility and wet roads. Overturned vehicle blocking two lanes. Multiple passengers with lacerations.',
        'location_address': 'North Bypass Highway KM 14, Bapatla',
        'landmark': 'Toll Plaza Junction',
        'latitude': 15.9250,
        'longitude': 80.4520,
        'people_affected': 30,
        'trapped_count': 2,
        'injured_count': 6,
        'is_sos': 0,
        'photo_url': '/static/images/accident_scene.svg',
        'reporter_name': 'Highway Patrol Observer',
        'reporter_contact': '99887-11223',
        'source': 'Field Agency Report'
    }

    # Submit each scenario report through the multi-agent pipeline
    scenario_list = [inc1, inc2_dup, inc3_sos, inc4_acc]
    created_ids = []

    for item in scenario_list:
        with app.test_request_context(json=item):
            resp = api_submit_report()
            res_json = resp.get_json()
            created_ids.append(res_json.get('incident_code'))

    return jsonify({
        'success': True,
        'message': f"Hackathon Demo Scenario loaded with {len(scenario_list)} coordinated incidents.",
        'incidents': created_ids
    })

if __name__ == '__main__':
    # Start Flask development server on 0.0.0.0:5000
    print(f"================================================================")
    print(f" {Config.PROJECT_NAME} - {Config.PROJECT_TITLE}")
    print(f" Project Code: {Config.PROJECT_CODE} | Hackathon Date: {Config.EVENT_DATE}")
    print(f" Team: {', '.join(Config.TEAM_MEMBERS)}")
    print(f" Institution: {Config.COLLEGE}")
    print(f" Connected DB: {database.get_db_type()}")
    print(f" Active Port: http://127.0.0.1:5000")
    print(f"================================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)

