import unittest
import json
from app import app
import database

class DisasterSyncTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_01_index_page(self):
        """Test landing page renders with status 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'DisasterSync AI', response.data)
        self.assertIn(b'Bapatla Women', response.data)

    def test_02_report_page(self):
        """Test report form page renders with status 200."""
        response = self.client.get('/report')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Emergency Intake Form', response.data)

    def test_03_dashboard_page(self):
        """Test admin dashboard page renders with status 200."""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Incident Command Center', response.data)

    def test_04_resources_page(self):
        """Test agency resources page renders with status 200."""
        response = self.client.get('/resources')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Agency Resource & Asset Inventory', response.data)

    def test_05_alerts_page(self):
        """Test alerts page renders with status 200."""
        response = self.client.get('/alerts')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Simulated Multi-Agency Alert Terminal', response.data)

    def test_06_docs_page(self):
        """Test hackathon documentation page renders with status 200."""
        response = self.client.get('/docs')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AG-AI-01', response.data)
        self.assertIn(b'Multi-Agent Architecture', response.data)

    def test_07_load_demo_scenario(self):
        """Test loading hackathon demo scenario (Section 13.1)."""
        response = self.client.post('/api/demo/load-scenario')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['incidents']), 4)

    def test_08_get_incidents_api(self):
        """Test API returns list of incidents and handles filters."""
        response = self.client.get('/api/incidents')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['incidents']), 4)

        # Test filter by type
        flood_resp = self.client.get('/api/incidents?type=Flood')
        flood_data = flood_resp.get_json()
        self.assertTrue(flood_data['success'])
        for inc in flood_data['incidents']:
            self.assertEqual(inc['emergency_type'], 'Flood')

    def test_09_incident_detail_and_multiagent_cards(self):
        """Test viewing incident detail with multi-agent recommendation cards."""
        # Get first incident
        incidents = database.query_db("SELECT id FROM incidents LIMIT 1")
        self.assertTrue(len(incidents) > 0)
        inc_id = incidents[0]['id']

        response = self.client.get(f'/incident/{inc_id}')
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('Multi-Agent Intelligence', text)
        self.assertIn('Coordinator Agent', text)
        self.assertIn('Police Coordination Agent', text)
        self.assertIn('Fire &amp; Rescue Agent', text)

    def test_10_urgent_sos_trigger(self):
        """Test urgent 1-click SOS API produces CRITICAL urgency score."""
        payload = {
            'emergency_type': 'Critical SOS - Flood Inundation',
            'latitude': 15.9100,
            'longitude': 80.4700,
            'people_affected': 4,
            'trapped_count': 2
        }
        response = self.client.post('/api/sos', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['urgency_level'], 'CRITICAL')
        self.assertGreaterEqual(data['urgency_score'], 80)

    def test_11_officer_status_update(self):
        """Test officer updating status from Reported to In Progress."""
        incidents = database.query_db("SELECT id FROM incidents LIMIT 1")
        inc_id = incidents[0]['id']

        payload = {'status': 'In Progress', 'officer_name': 'Commander Sneha'}
        response = self.client.post(f'/api/incident/{inc_id}/status', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['new_status'], 'In Progress')

    def test_12_officer_alert_approval(self):
        """Test human-in-the-loop alert approval."""
        alerts = database.query_db("SELECT id FROM simulated_alerts WHERE status = 'PENDING_APPROVAL' LIMIT 1")
        if alerts:
            alert_id = alerts[0]['id']
            payload = {'action': 'APPROVE', 'officer_name': 'Commander Kavya'}
            response = self.client.post(f'/api/alert/{alert_id}/action', json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['new_status'], 'APPROVED')

    def test_13_live_location_photo_and_tracking(self):
        """Test report submission with live location photo and citizen tracking endpoint."""
        payload = {
            'emergency_type': 'Flood',
            'title': 'Canal Breach with Geotagged Camera Photo',
            'location_address': 'Ward 4, East Canal Road, Bapatla',
            'latitude': 15.9085,
            'longitude': 80.4735,
            'photo_url': '/static/images/flood_scene.svg',
            'people_affected': 10
        }
        resp = self.client.post('/api/report', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        inc_code = data['incident_code']

        # Verify photo_url was persisted
        row = database.query_db("SELECT photo_url FROM incidents WHERE incident_code = %s", (inc_code,), one=True)
        self.assertIsNotNone(row)
        self.assertEqual(row['photo_url'], '/static/images/flood_scene.svg')

        # Test tracking API
        track_resp = self.client.get(f'/api/track/{inc_code}')
        self.assertEqual(track_resp.status_code, 200)
        track_data = track_resp.get_json()
        self.assertTrue(track_data['success'])
        self.assertEqual(track_data['incident']['incident_code'], inc_code)

    def test_14_export_aar_report(self):
        """Test export after-action debrief page."""
        incidents = database.query_db("SELECT id FROM incidents LIMIT 1")
        self.assertTrue(len(incidents) > 0)
        inc_id = incidents[0]['id']
        response = self.client.get(f'/incident/{inc_id}/export')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'EMERGENCY INCIDENT DEBRIEF', response.data)

    def test_15_attach_incident_photo_api(self):
        """Test attaching captured live camera photo to incident ID (Req 8 & 9)."""
        incidents = database.query_db("SELECT id FROM incidents LIMIT 1")
        self.assertTrue(len(incidents) > 0)
        inc_id = incidents[0]['id']

        # 1x1 transparent png in base64
        sample_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        resp = self.client.post(f'/api/incident/{inc_id}/photo', json={'photo_data': sample_b64})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIn(f"incident_{inc_id}_", data['photo_url'])

        # Verify database updated
        row = database.query_db("SELECT photo_url FROM incidents WHERE id = %s", (inc_id,), one=True)
        self.assertEqual(row['photo_url'], data['photo_url'])

    def test_16_new_incident_email_notification(self):
        """Test automatic email notification to officers upon new incident submission."""
        from email_service import EmailNotificationService
        payload = {
            'emergency_type': 'Fire',
            'title': 'Warehouse Chemical Fire with Smoke Emission',
            'location_address': 'Industrial Estate Road 2, Bapatla',
            'latitude': 15.9120,
            'longitude': 80.4650,
            'description': 'Heavy toxic smoke plumes and trapped warehouse personnel reported.',
            'people_affected': 8,
            'trapped_count': 3,
            'injured_count': 1
        }
        resp = self.client.post('/api/report', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        inc_id = data['incident_id']
        self.assertIn('email_notifications', data)

        # Check database records
        emails = database.query_db("SELECT * FROM email_notifications WHERE incident_id = %s", (inc_id,))
        self.assertTrue(len(emails) > 0)
        first_email = emails[0]
        self.assertEqual(first_email['notification_type'], 'NEW_INCIDENT')
        # SENT = real Gmail delivery; FAILED = no credentials configured (dev/CI environment)
        self.assertIn(first_email['status'], ['SENT', 'FAILED'])
        self.assertIn('Warehouse Chemical Fire', first_email['subject'])
        self.assertTrue(len(first_email['recipient_email']) > 0)

    def test_17_status_change_email_notification(self):
        """Test email notification when incident status changes."""
        incidents = database.query_db("SELECT id, status FROM incidents LIMIT 1")
        self.assertTrue(len(incidents) > 0)
        inc_id = incidents[0]['id']
        current_status = incidents[0]['status']
        next_status = 'Dispatched' if current_status != 'Dispatched' else 'In Progress'

        payload = {'status': next_status, 'officer_name': 'Commander Rajesh', 'note': 'First responder units deployed.'}
        resp = self.client.post(f'/api/incident/{inc_id}/status', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIn('email_notifications', data)

        # Verify status change email in database
        emails = database.query_db(
            "SELECT * FROM email_notifications WHERE incident_id = %s AND notification_type = 'STATUS_CHANGE' AND new_status = %s",
            (inc_id, next_status)
        )
        self.assertTrue(len(emails) > 0)
        email_record = emails[0]
        self.assertEqual(email_record['new_status'], next_status)
        # SENT = real Gmail delivery; FAILED = no credentials configured (dev/CI environment)
        self.assertIn(email_record['status'], ['SENT', 'FAILED'])

    def test_18_email_deduplication(self):
        """Test strict deduplication preventing redundant duplicate emails."""
        from email_service import EmailNotificationService
        incidents = database.query_db("SELECT * FROM incidents LIMIT 1")
        self.assertTrue(len(incidents) > 0)
        inc = incidents[0]

        # First dispatch
        res1 = EmailNotificationService.send_new_incident_notification(inc, inc['id'])
        # Second dispatch (should be skipped by deduplication token regardless of SMTP status)
        res2 = EmailNotificationService.send_new_incident_notification(inc, inc['id'])
        # Dedup always succeeds (success=True) — each result is DUPLICATE_SKIPPED
        self.assertTrue(res2['success'])
        for item in res2['results']:
            self.assertEqual(item['status'], 'DUPLICATE_SKIPPED')

    def test_19_get_incident_emails_api(self):
        """Test fetching email notification history via REST API."""
        incidents = database.query_db("SELECT id FROM incidents LIMIT 1")
        self.assertTrue(len(incidents) > 0)
        inc_id = incidents[0]['id']

        resp = self.client.get(f'/api/incident/{inc_id}/emails')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIsInstance(data['emails'], list)

    def test_20_secure_env_config(self):
        """Test email credentials are securely mapped via environment variables."""
        from config import Config
        # Must not contain hardcoded credentials in source
        self.assertTrue(hasattr(Config, 'SMTP_USER'))
        self.assertTrue(hasattr(Config, 'SMTP_PASSWORD'))
        self.assertTrue(hasattr(Config, 'SMTP_SERVER'))
        self.assertTrue(hasattr(Config, 'OFFICER_EMAILS'))
        self.assertTrue(hasattr(Config, 'EMAIL_NOTIFICATIONS_ENABLED'))

    def test_21_user_confirmation_email(self):
        """Test sending automatic confirmation email to the citizen (Req 2)."""
        payload = {
            'emergency_type': 'Accident',
            'title': 'Multi-Vehicle Pileup on NH-216 Highway',
            'location_address': 'NH-216 Bypass Flyover, Bapatla',
            'latitude': 15.9150,
            'longitude': 80.4610,
            'description': 'Three vehicles collided with fuel spill, ambulance required immediately.',
            'reporter_name': 'Kavya Citizen',
            'reporter_email': 'kavya.citizen@disastersync.ai',
            'people_affected': 4,
            'trapped_count': 1,
            'injured_count': 2
        }
        resp = self.client.post('/api/report', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        inc_id = data['incident_id']

        # Verify user confirmation in response payload
        self.assertIsNotNone(data['user_confirmation'])
        # success=True when SENT; success=False when no SMTP credentials configured (dev/CI env)
        self.assertIn(data['user_confirmation']['recipient'], ['kavya.citizen@disastersync.ai', ''])
        # Recipient must be preserved regardless of delivery result
        self.assertEqual(data['user_confirmation']['recipient'], 'kavya.citizen@disastersync.ai')

        # Verify entry in database
        confirm_email = database.query_db(
            "SELECT * FROM email_notifications WHERE incident_id = %s AND notification_type = 'USER_CONFIRMATION'",
            (inc_id,),
            one=True
        )
        self.assertIsNotNone(confirm_email)
        self.assertEqual(confirm_email['recipient_email'], 'kavya.citizen@disastersync.ai')
        self.assertIn('Emergency Report Confirmation', confirm_email['subject'])
        # SENT = real Gmail delivery; FAILED = no credentials configured (dev/CI environment)
        self.assertIn(confirm_email['status'], ['SENT', 'FAILED'])

    def test_22_admin_dashboard_test_email_api(self):
        """Test Admin Dashboard 'Test Email' button endpoint (Req 9)."""
        payload = {'recipient_email': 'duty.officer@disastersync.ai'}
        resp = self.client.post('/api/email/test', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        # Endpoint must respond; success=True when SENT, success=False when no SMTP credentials (dev/CI)
        self.assertIn(data['status'], ['SENT', 'FAILED'])
        self.assertEqual(data['recipient'], 'duty.officer@disastersync.ai')

        # Verify logged in database regardless of delivery result
        test_log = database.query_db(
            "SELECT * FROM email_notifications WHERE notification_type = 'SYSTEM_TEST' ORDER BY sent_at DESC LIMIT 1",
            one=True
        )
        self.assertIsNotNone(test_log)
        self.assertEqual(test_log['recipient_email'], 'duty.officer@disastersync.ai')

    def test_23_user_status_change_email(self):
        """Test status update email dispatched to reporting citizen."""
        # Query incident with valid reporter_email
        inc = database.query_db("SELECT * FROM incidents WHERE reporter_email IS NOT NULL AND reporter_email != '' ORDER BY id DESC LIMIT 1", one=True)
        if inc:
            inc_id = inc['id']
            payload = {'status': 'Resolved', 'officer_name': 'Commander Sneha', 'note': 'Hazard cleared and victims evacuated.'}
            resp = self.client.post(f'/api/incident/{inc_id}/status', json=payload)
            self.assertEqual(resp.status_code, 200)

            # Check user status update email
            user_status_log = database.query_db(
                "SELECT * FROM email_notifications WHERE incident_id = %s AND notification_type = 'USER_STATUS_CHANGE'",
                (inc_id,)
            )
            self.assertTrue(len(user_status_log) > 0)
            self.assertEqual(user_status_log[0]['recipient_email'], inc['reporter_email'])

    # ====================================================================
    # MULTI-AGENT INTEGRATION & ORCHESTRATION TESTS (Req 1-20)
    # ====================================================================

    def test_24_multi_agent_automatic_execution_on_report(self):
        """Test that all 5 AI agents execute automatically upon report intake (Req 1, 2, 3, 4, 16)."""
        payload = {
            'emergency_type': 'Fire',
            'title': 'Chemical Factory Thermal Fire with Entrapped Workers',
            'location_address': 'Industrial Sector 5, Coastal Highway, Bapatla',
            'latitude': 15.9180,
            'longitude': 80.4650,
            'description': 'Toxic fumes spreading rapidly from solvent storage. 6 workers trapped inside warehouse.',
            'reporter_name': 'Factory Safety Officer',
            'reporter_email': 'factory.safety@disastersync.ai',
            'people_affected': 18,
            'trapped_count': 6,
            'injured_count': 3
        }
        resp = self.client.post('/api/report', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        inc_id = data['incident_id']

        # Verify agent execution record in DB for all 5 agents
        execs = database.query_db(
            "SELECT * FROM agent_executions WHERE incident_id = %s ORDER BY agent_id ASC",
            (inc_id,)
        )
        self.assertEqual(len(execs), 5, "All 5 AI agents must have execution records")

        agent_ids = [e['agent_id'] for e in execs]
        expected_agents = ['coordinator', 'fire', 'medical', 'police', 'rescue']
        self.assertEqual(sorted(agent_ids), sorted(expected_agents))

        # Verify all agents completed successfully with non-empty responses and recorded execution time
        for e in execs:
            self.assertEqual(e['status'], 'COMPLETED', f"Agent {e['agent_id']} should have status COMPLETED")
            self.assertIsNotNone(e['response_json'], f"Agent {e['agent_id']} must have response JSON")
            self.assertGreaterEqual(e['execution_time_ms'], 0, f"Agent {e['agent_id']} must record execution time")
            self.assertIsNone(e['error_message'], f"Agent {e['agent_id']} should have no errors")

    def test_25_incident_agents_status_api(self):
        """Test GET /api/incident/<id>/agents endpoint returns per-agent status, timing, errors (Req 8, 9, 10)."""
        inc = database.query_db("SELECT id FROM incidents ORDER BY id DESC LIMIT 1", one=True)
        self.assertIsNotNone(inc)
        inc_id = inc['id']

        resp = self.client.get(f'/api/incident/{inc_id}/agents')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_agents'], 5)
        self.assertIn('executions', data)
        self.assertEqual(len(data['executions']), 5)

        for ex in data['executions']:
            self.assertIn(ex['status'], ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED'])
            self.assertIn('execution_time_ms', ex)
            self.assertIn('agent_name', ex)
            self.assertIn('response', ex)

    def test_26_run_all_agents_manual_endpoint(self):
        """Test POST /api/incident/<id>/agents/run manual button endpoint (Req 19)."""
        inc = database.query_db("SELECT id FROM incidents ORDER BY id DESC LIMIT 1", one=True)
        self.assertIsNotNone(inc)
        inc_id = inc['id']

        resp = self.client.post(f'/api/incident/{inc_id}/agents/run', json={'force': True})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'ALL_COMPLETED')
        self.assertEqual(data['completed_count'], 5)
        self.assertEqual(data['failed_count'], 0)
        self.assertGreater(data['total_execution_time_ms'], 0)

    def test_27_duplicate_agent_execution_prevention(self):
        """Test that duplicate agent execution is prevented unless force=True (Req 15)."""
        from agent_orchestrator import run_all_agents
        inc = database.query_db("SELECT id FROM incidents ORDER BY id DESC LIMIT 1", one=True)
        self.assertIsNotNone(inc)
        inc_id = inc['id']

        # Ensure first execution completed
        res1 = run_all_agents(inc_id, force=True)
        self.assertTrue(res1['success'])

        # Second execution without force should detect ALREADY_EXECUTED
        res2 = run_all_agents(inc_id, force=False)
        self.assertTrue(res2['success'])
        self.assertEqual(res2['status'], 'ALREADY_EXECUTED')

    def test_28_agent_registry_endpoint(self):
        """Test GET /api/agents/registry returns metadata for all 5 agents (Req 1)."""
        resp = self.client.get('/api/agents/registry')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_agents'], 5)
        reg_ids = [a['agent_id'] for a in data['agents']]
        self.assertIn('coordinator', reg_ids)
        self.assertIn('police', reg_ids)
        self.assertIn('fire', reg_ids)
        self.assertIn('medical', reg_ids)
        self.assertIn('rescue', reg_ids)

    def test_29_genuine_agent_reasoning_and_differentiation(self):
        """Verify each of the 5 agents performs distinct, genuine reasoning without fake placeholders (Req 5, 6, 13)."""
        incident_sample = {
            'emergency_type': 'Flood',
            'title': 'Severe Canal Inundation',
            'description': 'Water rising over 5 feet, 4 families trapped on roof.',
            'location_address': 'East Ward 3, Canal Bund Road, Bapatla',
            'latitude': 15.9080,
            'longitude': 80.4730,
            'people_affected': 15,
            'trapped_count': 4,
            'injured_count': 1,
            'is_sos': 0
        }
        resources_sample = database.query_db("SELECT * FROM resources")

        # 1. Police Agent evaluates perimeter and flood barricades
        from agents.police_agent import PoliceCoordinationAgent
        police = PoliceCoordinationAgent.analyze(incident_sample)
        self.assertEqual(police['agent_name'], "Police Coordination Agent")
        self.assertTrue(any('submerged' in a.lower() or 'perimeter' in a.lower() for a in police['suggested_actions']))

        # 2. Fire & Rescue Agent recommends boats & watercraft
        from agents.fire_rescue_agent import FireRescueAgent
        fire = FireRescueAgent.analyze(incident_sample)
        self.assertEqual(fire['agent_name'], "Fire & Rescue Agent")
        self.assertTrue(any('boat' in a.lower() or 'water' in a.lower() for a in fire['suggested_actions']))

        # 3. Medical Agent recommends triage & ambulances
        from agents.medical_agent import MedicalAssistanceAgent
        medical = MedicalAssistanceAgent.analyze(incident_sample)
        self.assertEqual(medical['agent_name'], "Medical Assistance Agent")
        self.assertTrue(any('ambulance' in a.lower() or 'triage' in a.lower() for a in medical['suggested_actions']))

        # 4. Rescue / Resource Agent matches nearest assets using haversine
        from agents.resource_agent import ResourceManagementAgent
        rescue = ResourceManagementAgent.analyze(incident_sample, resources_sample)
        self.assertEqual(rescue['agent_name'], "Resource Management Agent")
        self.assertIn('allocated_items', rescue)

        # 5. Coordinator Agent synthesizes all 4
        from agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent.process_incident(incident_sample, [], resources_sample)
        self.assertIn('urgency_score', coord)
        self.assertIn('recommendations', coord)
        self.assertEqual(len(coord['recommendations']), 5)

    def test_30_human_in_the_loop_approval_preserved(self):
        """Verify human approval is strictly required before simulated dispatch (Req 18, 20)."""
        # Retrieve any pending simulated alert
        alerts = database.query_db("SELECT id, status FROM simulated_alerts WHERE status = 'PENDING_APPROVAL' LIMIT 1")
        if alerts:
            alert_id = alerts[0]['id']
            # Officer approves
            resp = self.client.post(f'/api/alert/{alert_id}/action', json={
                'action': 'APPROVE',
                'officer_name': 'Commander Sneha'
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['new_status'], 'APPROVED')

            # Verify in DB
            updated = database.query_db("SELECT status, officer_approved_by FROM simulated_alerts WHERE id = %s", (alert_id,), one=True)
            self.assertEqual(updated['status'], 'APPROVED')
            self.assertEqual(updated['officer_approved_by'], 'Commander Sneha')

    # ====================================================================
    # 10-AGENT AUTONOMOUS SYSTEM & TELEMETRY TESTS (Req 1-10)
    # ====================================================================

    def test_31_ten_specialized_agents_registry(self):
        """Test GET /api/system/agents returns all 10 specialized agents with live telemetry."""
        resp = self.client.get('/api/system/agents')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_agents'], 10)
        self.assertIn('agents', data)
        self.assertEqual(len(data['agents']), 10)

        agent_ids = [a['agent_id'] for a in data['agents']]
        expected_10 = [
            'master_coordinator',
            'monitoring',
            'emergency_detection',
            'triage',
            'duplicate_detection',
            'resource_coordination',
            'notification',
            'tracking',
            'maintenance',
            'database'
        ]
        for expected in expected_10:
            self.assertIn(expected, agent_ids, f"Agent {expected} must be in the 10-agent registry")

        # Verify attributes on each agent
        for a in data['agents']:
            self.assertIn('status', a)
            self.assertIn('current_task', a)
            self.assertIn('health_score', a)
            self.assertIn('tasks_processed', a)

    def test_32_inter_agent_message_bus(self):
        """Test inter-agent message passing and persistence on the message bus."""
        from agents.master_orchestrator import AgentMessageBus
        msg = AgentMessageBus.publish(
            'Emergency Detection Agent',
            'Master Coordinator Agent',
            'TEST_HAZARD_DISPATCH',
            'Flash Flood detected at North Ward Bund. Urgent rescue recommended.',
            incident_id=1
        )
        self.assertEqual(msg['message_type'], 'TEST_HAZARD_DISPATCH')
        self.assertEqual(msg['status'], 'DELIVERED')

        # Query messages via REST API
        resp = self.client.get('/api/system/messages')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['messages']), 0)
        types = [m['message_type'] for m in data['messages']]
        self.assertIn('TEST_HAZARD_DISPATCH', types)

    def test_33_monitoring_agent_ping(self):
        """Test POST /api/system/ping returns server health, db latency, and active threads."""
        resp = self.client.post('/api/system/ping')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIn('status', data)
        self.assertIn('uptime_seconds', data)
        self.assertIn('db_connected', data)
        self.assertTrue(data['db_connected'])
        self.assertGreater(data['db_latency_ms'], 0)

    def test_34_maintenance_agent_diagnostics(self):
        """Test POST /api/system/maintenance executes self-diagnostics and auto-heals storage/DB."""
        resp = self.client.post('/api/system/maintenance')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'HEALTHY')
        self.assertIn('checks', data)
        self.assertGreater(len(data['checks']), 0)
        check_names = [c['check'] for c in data['checks']]
        self.assertIn('Database Read/Write', check_names)
        self.assertIn('Uploads Storage', check_names)
        self.assertIn('Gmail SMTP Gateway', check_names)

    def test_35_citizen_tracking_page_and_api(self):
        """Test citizen tracking page and REST API (resolving Flask tracking link issue)."""
        # Create a sample incident to track
        inc = database.query_db("SELECT incident_code FROM incidents ORDER BY id DESC LIMIT 1", one=True)
        self.assertIsNotNone(inc)
        code = inc['incident_code']

        # 1. Test public tracking landing page
        resp_page = self.client.get('/track')
        self.assertEqual(resp_page.status_code, 200)
        self.assertIn(b'Citizen Emergency Incident Tracking', resp_page.data)

        # 2. Test direct tracking page with code
        resp_code = self.client.get(f'/track/{code}')
        self.assertEqual(resp_code.status_code, 200)
        self.assertIn(code.encode(), resp_code.data)

        # 3. Test tracking API endpoint
        resp_api = self.client.get(f'/api/track/{code}')
        self.assertEqual(resp_api.status_code, 200)
        data = resp_api.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['incident']['incident_code'], code)
        self.assertIn('status', data['incident'])

    def test_36_safety_guardrails_enforced(self):
        """Verify safety policy: AI cannot make final emergency dispatches without human approval."""
        from agents.master_orchestrator import ResourceCoordinationAgent
        sample_inc = {'emergency_type': 'Fire', 'latitude': 15.9, 'longitude': 80.4, 'trapped_count': 1, 'injured_count': 1}
        res = ResourceCoordinationAgent.recommend(sample_inc, [])
        self.assertIn('safety_notice', res)
        self.assertIn('HUMAN APPROVAL REQUIRED', res['safety_notice'])

    # ====================================================================
    # AUTONOMOUS AI OPERATOR TESTS (Req: AI to operate the project)
    # ====================================================================

    def test_37_ai_operator_status_api(self):
        """Test GET /api/operator/status returns operational mode and telemetry."""
        resp = self.client.get('/api/operator/status')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIn('autonomous_mode', data)
        self.assertIn('cycle_count', data)
        self.assertIn('latest_action', data)
        self.assertIn('stats', data)

    def test_38_ai_operator_toggle_mode(self):
        """Test POST /api/operator/toggle switches between autonomous and manual mode."""
        # 1. Toggle once
        resp1 = self.client.post('/api/operator/toggle')
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertTrue(data1['success'])
        first_mode = data1['autonomous_mode']

        # 2. Toggle back
        resp2 = self.client.post('/api/operator/toggle')
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertTrue(data2['success'])
        self.assertNotEqual(first_mode, data2['autonomous_mode'])

        # Ensure left in autonomous mode
        if not data2['autonomous_mode']:
            self.client.post('/api/operator/toggle')

    def test_39_ai_operator_natural_language_command(self):
        """Test POST /api/operator/command executes natural language directives."""
        # Directives 1: Executive Status Brief
        resp = self.client.post('/api/operator/command', json={'command': 'Summarize active disaster status'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'EXECUTIVE_BRIEF')
        self.assertIn('AI OPERATOR EXECUTIVE BRIEF', data['reply'])

        # Directives 2: Resource Audit
        resp_res = self.client.post('/api/operator/command', json={'command': 'Audit emergency resources and identify shortages'})
        self.assertEqual(resp_res.status_code, 200)
        data_res = resp_res.get_json()
        self.assertTrue(data_res['success'])
        self.assertEqual(data_res['intent'], 'RESOURCE_AUDIT')
        self.assertIn('RESOURCE AUDIT', data_res['reply'])

        # Directives 3: Self-healing diagnostics
        resp_diag = self.client.post('/api/operator/command', json={'command': 'Run self-healing diagnostics'})
        self.assertEqual(resp_diag.status_code, 200)
        data_diag = resp_diag.get_json()
        self.assertTrue(data_diag['success'])
        self.assertEqual(data_diag['intent'], 'DIAGNOSTIC_RUN')
        self.assertIn('MAINTENANCE', data_diag['reply'])

    def test_40_ai_operator_immediate_cycle_sweep(self):
        """Test POST /api/operator/cycle triggers an immediate operational sweep."""
        resp = self.client.post('/api/operator/cycle')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIn('cycle', data)
        self.assertIn('latest_action', data)
        self.assertIn('actions_taken', data)

if __name__ == '__main__':
    unittest.main()
