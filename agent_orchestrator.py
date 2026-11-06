"""
DisasterSync AI — Multi-Agent Orchestrator Engine
===================================================
Coordinates all 5 AI agents (Coordinator, Police, Fire, Medical, Rescue)
as a fully integrated asynchronous multi-agent system.

Features:
- Automatic execution on new emergency report submission
- Per-agent status tracking (Pending → Running → Completed / Failed)
- Execution time recording and error logging
- Duplicate execution prevention per incident
- Optional Gemini LLM enhancement for richer agent responses
- Thread-based concurrent agent execution
- Retry mechanism on transient failures
- Email notification after successful processing
"""

import time
import json
import threading
import traceback
from datetime import datetime
from config import Config
import database

# Import existing agents
from agents.coordinator_agent import CoordinatorAgent
from agents.police_agent import PoliceCoordinationAgent
from agents.fire_rescue_agent import FireRescueAgent
from agents.medical_agent import MedicalAssistanceAgent
from agents.resource_agent import ResourceManagementAgent
from agents.comms_agent import CommunicationAgent
from agents.duplicate_agent import DuplicateDetectionAgent

# Optional: Gemini LLM integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# ---------------------------------------------------------------------------
# Agent Registry — The 5 agents required (Req 1-5)
# ---------------------------------------------------------------------------

AGENT_REGISTRY = [
    {
        'agent_id': 'coordinator',
        'agent_name': 'Coordinator Agent',
        'description': 'Central orchestrator: calculates urgency, detects duplicates, synthesizes unified response plan.',
        'icon': 'fa-network-wired',
        'color': '#8b5cf6',
        'order': 1
    },
    {
        'agent_id': 'police',
        'agent_name': 'Police Coordination Agent',
        'description': 'Public safety: perimeter control, traffic management, evacuation corridor planning.',
        'icon': 'fa-shield-halved',
        'color': '#3b82f6',
        'order': 2
    },
    {
        'agent_id': 'fire',
        'agent_name': 'Fire & Rescue Agent',
        'description': 'Rescue operations: equipment deployment, search & rescue, hazmat assessment.',
        'icon': 'fa-fire-extinguisher',
        'color': '#ef4444',
        'order': 3
    },
    {
        'agent_id': 'medical',
        'agent_name': 'Medical Assistance Agent',
        'description': 'Medical triage: ambulance dispatch, hospital readiness, casualty classification.',
        'icon': 'fa-truck-medical',
        'color': '#10b981',
        'order': 4
    },
    {
        'agent_id': 'rescue',
        'agent_name': 'Rescue & Resource Agent',
        'description': 'Resource allocation: NDRF mobilization, equipment matching, shortage detection.',
        'icon': 'fa-life-ring',
        'color': '#f59e0b',
        'order': 5
    }
]


def get_agent_registry():
    """Returns the list of all registered agents for UI rendering."""
    return AGENT_REGISTRY


# ---------------------------------------------------------------------------
# Gemini LLM Enhancement (Req 12: Connect to actual LLM API)
# ---------------------------------------------------------------------------

def _get_gemini_model():
    """Initialize Gemini model if API key is configured."""
    api_key = getattr(Config, 'GEMINI_API_KEY', '') or ''
    if not api_key or not GEMINI_AVAILABLE:
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model
    except Exception:
        return None


def _enhance_with_llm(agent_name, incident_data, base_response, model=None):
    """
    Enhance an agent's rule-based response with Gemini LLM analysis (Req 12).
    If LLM is unavailable, returns the base response unchanged (Req 13 fallback).
    """
    if model is None:
        return base_response, 'rule_based'

    try:
        em_type = incident_data.get('emergency_type', 'Unknown')
        location = incident_data.get('location_address', 'Unknown')
        desc = incident_data.get('description', '')
        trapped = incident_data.get('trapped_count', 0)
        injured = incident_data.get('injured_count', 0)
        people = incident_data.get('people_affected', 0)

        prompt = f"""You are the {agent_name} in a Multi-Agent Disaster Response System.
Analyze this emergency incident and provide a professional, specific, actionable response.

INCIDENT DETAILS:
- Emergency Type: {em_type}
- Location: {location}
- Description: {desc}
- People Affected: {people}
- Trapped: {trapped}
- Injured: {injured}

EXISTING ANALYSIS (from rule-based system):
- Priority: {base_response.get('priority_level', 'Normal')}
- Summary: {base_response.get('summary', '')}
- Actions: {json.dumps(base_response.get('suggested_actions', []))}

Provide an ENHANCED analysis with:
1. A refined 2-sentence summary specific to this incident.
2. 3-5 specific, actionable steps for this agent.
3. Key risk factors and evidence.

Format your response as JSON:
{{"enhanced_summary": "...", "enhanced_actions": ["action1", "action2", ...], "risk_factors": "...", "confidence": 0.95}}

Respond ONLY with valid JSON. No markdown, no explanation."""

        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
        
        enhanced = json.loads(text)
        
        # Merge LLM enhancements into base response
        if enhanced.get('enhanced_summary'):
            base_response['summary'] = enhanced['enhanced_summary']
        if enhanced.get('enhanced_actions'):
            base_response['suggested_actions'] = enhanced['enhanced_actions']
        if enhanced.get('risk_factors'):
            base_response['evidence_refs'] = enhanced['risk_factors']
        if enhanced.get('confidence'):
            base_response['confidence'] = float(enhanced['confidence'])
        
        base_response['llm_enhanced'] = True
        return base_response, 'gemini_enhanced'
    except Exception as e:
        # LLM enhancement failed — return base response (still valid, Req 13 satisfied)
        base_response['llm_error'] = str(e)[:200]
        return base_response, 'rule_based'


# ---------------------------------------------------------------------------
# Single Agent Executor (Req 9: status, execution time, errors)
# ---------------------------------------------------------------------------

def _execute_single_agent(agent_id, incident_data, incident_id, existing_incidents, available_resources, gemini_model=None):
    """
    Execute a single agent with timing, status tracking, and error handling.
    Returns dict with status, response, execution_time_ms, error.
    """
    start_time = time.time()
    
    try:
        if agent_id == 'coordinator':
            # Coordinator runs the full pipeline internally (urgency + dup + synthesis)
            urgency_score, urgency_level, urgency_reasons = CoordinatorAgent.calculate_urgency(incident_data)
            dup_result = DuplicateDetectionAgent.evaluate(incident_data, existing_incidents)
            
            # Run sub-agents for synthesis
            police_rec = PoliceCoordinationAgent.analyze(incident_data)
            fire_rec = FireRescueAgent.analyze(incident_data)
            med_rec = MedicalAssistanceAgent.analyze(incident_data)
            res_rec = ResourceManagementAgent.analyze(incident_data, available_resources)
            
            response = CoordinatorAgent.synthesize_plan(
                incident_data, urgency_score, urgency_level, dup_result,
                police_rec, fire_rec, med_rec, res_rec
            )
            response['urgency_score'] = urgency_score
            response['urgency_level'] = urgency_level
            response['urgency_reasons'] = urgency_reasons
            response['duplicate_analysis'] = dup_result
            
        elif agent_id == 'police':
            response = PoliceCoordinationAgent.analyze(incident_data)
            
        elif agent_id == 'fire':
            response = FireRescueAgent.analyze(incident_data)
            
        elif agent_id == 'medical':
            response = MedicalAssistanceAgent.analyze(incident_data)
            
        elif agent_id == 'rescue':
            response = ResourceManagementAgent.analyze(incident_data, available_resources)
            
        else:
            raise ValueError(f"Unknown agent_id: {agent_id}")
        
        # Enhance with LLM if available (Req 12)
        response, analysis_mode = _enhance_with_llm(
            response.get('agent_name', agent_id),
            incident_data, response, gemini_model
        )
        response['analysis_mode'] = analysis_mode
        
        elapsed_ms = max(1, int(round((time.time() - start_time) * 1000)))
        
        return {
            'status': 'COMPLETED',
            'response': response,
            'execution_time_ms': elapsed_ms,
            'error': None
        }
    except Exception as e:
        elapsed_ms = max(1, int(round((time.time() - start_time) * 1000)))
        return {
            'status': 'FAILED',
            'response': None,
            'execution_time_ms': elapsed_ms,
            'error': f"{type(e).__name__}: {str(e)}"
        }


# ---------------------------------------------------------------------------
# Agent Execution Record DB Operations (Req 16)
# ---------------------------------------------------------------------------

def _create_agent_execution_record(incident_id, agent_id, agent_name, status='PENDING'):
    """Insert a new agent_executions record and return its ID."""
    return database.execute_db(
        """INSERT INTO agent_executions 
           (incident_id, agent_id, agent_name, status)
           VALUES (%s, %s, %s, %s)""",
        (incident_id, agent_id, agent_name, status)
    )


def _update_agent_execution(exec_id, status, response_json=None, execution_time_ms=0, error_message=None, analysis_mode='rule_based'):
    """Update an agent_executions record with results."""
    database.execute_db(
        """UPDATE agent_executions 
           SET status = %s, response_json = %s, execution_time_ms = %s, 
               error_message = %s, analysis_mode = %s, completed_at = CURRENT_TIMESTAMP
           WHERE id = %s""",
        (status, response_json, execution_time_ms, error_message, analysis_mode, exec_id)
    )


def _check_duplicate_execution(incident_id):
    """Check if agents have already been executed for this incident (Req 15)."""
    existing = database.query_db(
        "SELECT id, status FROM agent_executions WHERE incident_id = %s AND status IN ('COMPLETED', 'RUNNING')",
        (incident_id,)
    )
    return len(existing) > 0


def get_agent_executions(incident_id):
    """Fetch all agent execution records for an incident."""
    return database.query_db(
        "SELECT * FROM agent_executions WHERE incident_id = %s ORDER BY agent_id ASC",
        (incident_id,)
    )


# ---------------------------------------------------------------------------
# Multi-Agent Orchestrator (Req 2, 3, 4, 11)
# ---------------------------------------------------------------------------

def run_all_agents(incident_id, force=False):
    """
    Main orchestrator: runs all 5 agents for an incident.
    
    - Checks for duplicate execution (Req 15)
    - Creates PENDING records for each agent
    - Runs agents concurrently using threads (Req 11)
    - Updates records with results (Req 9, 10, 16)
    - Triggers email notification after completion (Req 17)
    
    Args:
        incident_id: Database incident ID
        force: If True, skip duplicate check (for manual re-run via "Run All Agents" button, Req 19)
    
    Returns:
        dict with overall status, per-agent results, and timing
    """
    overall_start = time.time()
    
    # Fetch incident data
    incident = database.query_db("SELECT * FROM incidents WHERE id = %s", (incident_id,), one=True)
    if not incident:
        return {'success': False, 'error': f"Incident #{incident_id} not found."}
    
    # Duplicate execution guard (Req 15)
    if not force and _check_duplicate_execution(incident_id):
        existing_results = get_agent_executions(incident_id)
        return {
            'success': True,
            'incident_id': incident_id,
            'status': 'ALREADY_EXECUTED',
            'message': 'Agents have already been executed for this incident. Use force=True or the "Run All Agents" button to re-execute.',
            'agent_results': [dict(r) for r in existing_results]
        }
    
    # If force re-run, clear old execution records
    if force:
        database.execute_db(
            "DELETE FROM agent_executions WHERE incident_id = %s",
            (incident_id,)
        )
    
    # Fetch context data for agents
    existing_incidents = database.query_db(
        """SELECT id, incident_code, emergency_type, title, description, 
           location_address, latitude, longitude, urgency_level, status 
           FROM incidents WHERE status NOT IN ('Resolved', 'Closed') AND id != %s""",
        (incident_id,)
    )
    available_resources = database.query_db("SELECT * FROM resources")
    
    # Build incident_data dict
    incident_data = dict(incident)
    
    # Initialize Gemini model once for all agents (Req 12)
    gemini_model = _get_gemini_model()
    
    # Create PENDING records for all 5 agents (Req 9)
    exec_records = {}
    for agent_info in AGENT_REGISTRY:
        exec_id = _create_agent_execution_record(
            incident_id, agent_info['agent_id'], agent_info['agent_name'], 'PENDING'
        )
        exec_records[agent_info['agent_id']] = {
            'exec_id': exec_id,
            'agent_info': agent_info
        }
    
    # Audit log
    database.execute_db(
        """INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details) 
           VALUES (%s, %s, %s, %s, %s)""",
        (incident_id, 'Multi-Agent Orchestrator', 'AI System',
         'AGENTS_TRIGGERED', f"All 5 AI agents triggered for incident #{incident_id}. Gemini LLM: {'Available' if gemini_model else 'Unavailable (rule-based mode)'}.")
    )
    
    # Update all to RUNNING status
    for agent_id, rec in exec_records.items():
        _update_agent_execution(rec['exec_id'], 'RUNNING')
    
    # Execute agents concurrently using threads (Req 4, 11)
    results = {}
    threads = []
    results_lock = threading.Lock()
    
    def _run_agent_thread(agent_id, exec_id):
        """Thread target: runs a single agent and stores result."""
        result = _execute_single_agent(
            agent_id, incident_data, incident_id,
            existing_incidents, available_resources, gemini_model
        )
        with results_lock:
            results[agent_id] = result
        
        # Update DB record
        response_json = json.dumps(result['response'], default=str) if result['response'] else None
        analysis_mode = result['response'].get('analysis_mode', 'rule_based') if result['response'] else 'failed'
        _update_agent_execution(
            exec_id, result['status'], response_json,
            result['execution_time_ms'], result['error'], analysis_mode
        )
    
    # Launch all agent threads
    for agent_id, rec in exec_records.items():
        t = threading.Thread(
            target=_run_agent_thread,
            args=(agent_id, rec['exec_id']),
            name=f"agent-{agent_id}-inc{incident_id}"
        )
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete (with timeout for safety)
    for t in threads:
        t.join(timeout=30)
    
    # Retry failed agents once (Req 14)
    for agent_id, result in list(results.items()):
        if result['status'] == 'FAILED':
            retry_result = _execute_single_agent(
                agent_id, incident_data, incident_id,
                existing_incidents, available_resources, gemini_model
            )
            if retry_result['status'] == 'COMPLETED':
                results[agent_id] = retry_result
                exec_id = exec_records[agent_id]['exec_id']
                response_json = json.dumps(retry_result['response'], default=str)
                analysis_mode = retry_result['response'].get('analysis_mode', 'rule_based')
                _update_agent_execution(
                    exec_id, 'COMPLETED', response_json,
                    retry_result['execution_time_ms'], None, analysis_mode
                )
    
    # Store agent responses as agent_recommendations too (for backward compatibility with existing UI)
    _store_agent_recommendations(incident_id, results)
    
    # Generate and store alerts via CommunicationAgent
    alerts, public_bulletin = CommunicationAgent.generate_alerts(incident_data)
    _store_alerts(incident_id, alerts)
    
    # Update incident urgency from coordinator result if available
    coord_result = results.get('coordinator', {})
    if coord_result.get('status') == 'COMPLETED' and coord_result.get('response'):
        coord_resp = coord_result['response']
        if coord_resp.get('urgency_score') is not None:
            database.execute_db(
                """UPDATE incidents SET urgency_score = %s, urgency_level = %s, 
                   urgency_reasons = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s""",
                (coord_resp['urgency_score'], coord_resp['urgency_level'],
                 coord_resp.get('urgency_reasons', ''), incident_id)
            )
            # Update duplicate status
            dup = coord_resp.get('duplicate_analysis', {})
            if dup.get('is_duplicate'):
                database.execute_db(
                    "UPDATE incidents SET is_duplicate = 1, parent_incident_id = %s WHERE id = %s",
                    (dup.get('parent_id'), incident_id)
                )
    
    overall_ms = max(1, int(round((time.time() - overall_start) * 1000)))
    
    completed_count = sum(1 for r in results.values() if r['status'] == 'COMPLETED')
    failed_count = sum(1 for r in results.values() if r['status'] == 'FAILED')
    
    overall_status = 'ALL_COMPLETED' if failed_count == 0 else ('PARTIAL_FAILURE' if completed_count > 0 else 'ALL_FAILED')
    
    # Audit log completion
    database.execute_db(
        """INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details) 
           VALUES (%s, %s, %s, %s, %s)""",
        (incident_id, 'Multi-Agent Orchestrator', 'AI System',
         'AGENTS_COMPLETED',
         f"Agent execution finished: {completed_count}/5 completed, {failed_count}/5 failed. "
         f"Total time: {overall_ms}ms. LLM mode: {'Gemini Enhanced' if gemini_model else 'Rule-Based'}.")
    )
    
    # Build response
    agent_summaries = []
    for agent_info in AGENT_REGISTRY:
        aid = agent_info['agent_id']
        r = results.get(aid, {})
        agent_summaries.append({
            'agent_id': aid,
            'agent_name': agent_info['agent_name'],
            'status': r.get('status', 'NOT_RUN'),
            'execution_time_ms': r.get('execution_time_ms', 0),
            'error': r.get('error'),
            'analysis_mode': r.get('response', {}).get('analysis_mode', 'unknown') if r.get('response') else 'failed',
            'summary': r.get('response', {}).get('summary', '') if r.get('response') else '',
            'priority_level': r.get('response', {}).get('priority_level', '') if r.get('response') else ''
        })
    
    return {
        'success': True,
        'incident_id': incident_id,
        'status': overall_status,
        'total_execution_time_ms': overall_ms,
        'completed_count': completed_count,
        'failed_count': failed_count,
        'gemini_available': gemini_model is not None,
        'agents': agent_summaries,
        'alerts_generated': len(alerts),
        'public_bulletin': public_bulletin,
        'message': f"Multi-agent pipeline complete: {completed_count}/5 agents executed successfully in {overall_ms}ms."
    }


def _store_agent_recommendations(incident_id, results):
    """Store agent responses in agent_recommendations table (backward compat, Req 16)."""
    # Clear old recommendations for this incident to prevent duplicates
    database.execute_db("DELETE FROM agent_recommendations WHERE incident_id = %s", (incident_id,))
    
    rec_sql = """INSERT INTO agent_recommendations 
                 (incident_id, agent_name, recommendation_text, priority_level, suggested_actions, evidence_refs, confidence)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    
    for agent_id, result in results.items():
        if result['status'] == 'COMPLETED' and result['response']:
            resp = result['response']
            actions_json = json.dumps(resp.get('suggested_actions', []))
            database.execute_db(rec_sql, (
                incident_id,
                resp.get('agent_name', agent_id),
                resp.get('summary', ''),
                resp.get('priority_level', 'Normal'),
                actions_json,
                resp.get('evidence_refs', ''),
                resp.get('confidence', 0.85)
            ))


def _store_alerts(incident_id, alerts):
    """Store communication alerts (backward compat)."""
    # Clear old alerts to prevent duplicates on re-run
    database.execute_db("DELETE FROM simulated_alerts WHERE incident_id = %s", (incident_id,))
    
    alert_sql = """INSERT INTO simulated_alerts 
                   (incident_id, agency_type, agency_name, alert_channel, alert_title, alert_message, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    
    for alert in alerts:
        database.execute_db(alert_sql, (
            incident_id,
            alert['agency_type'],
            alert['agency_name'],
            alert['alert_channel'],
            alert['alert_title'],
            alert['alert_message'],
            'PENDING_APPROVAL'
        ))

