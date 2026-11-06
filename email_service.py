import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import Config
import database

# RFC 5322 compliant email validation regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class EmailNotificationService:
    """
    Real Gmail SMTP Emergency Notification Service:
    - Real email delivery using Python smtplib and Gmail (smtp.gmail.com:587) with App Password.
    - Secure environment configuration from .env (never hardcodes passwords).
    - Sends automated emergency alerts to response officers on report submission.
    - Sends automated confirmation emails to citizens with tracking ID and safety advice.
    - Sends status update emails to citizens when operational status progresses.
    - Admin Dashboard diagnostic test email integration.
    - Strict duplicate prevention to eliminate redundant spam.
    - Genuine status reporting: 'SENT' (Email Sent), 'FAILED' (Email Failed), 'PENDING' (Email Pending).
      Removes false simulated success claims.
    """

    @classmethod
    def is_valid_email(cls, email_str):
        """Validates email format using standard regular expression."""
        if not email_str or not isinstance(email_str, str):
            return False
        return bool(EMAIL_REGEX.match(email_str.strip()))

    @classmethod
    def get_recipient_list(cls):
        """Retrieves list of registered emergency officer emails from Config."""
        raw_emails = Config.OFFICER_EMAILS or ''
        recipients = [e.strip() for e in raw_emails.split(',') if e.strip() and cls.is_valid_email(e.strip())]
        if not recipients:
            recipients = ['officer.emergency@disastersync.ai']
        return recipients

    @classmethod
    def get_safety_guidelines(cls, emergency_type):
        """Returns specific safety guidelines based on emergency disaster type (Req 4)."""
        em = (emergency_type or '').lower()
        if 'flood' in em or 'water' in em or 'inundation' in em:
            return (
                "Move immediately to higher ground or upper building levels. "
                "Never walk, swim, or drive through flowing water — 6 inches of moving water can knock you down. "
                "Disconnect electrical appliances and avoid contact with submerged power lines or electrical equipment."
            )
        elif 'fire' in em or 'smoke' in em:
            return (
                "Evacuate the premises immediately via marked emergency exits. Do NOT use elevators. "
                "Stay low beneath the smoke layer where air is cooler and clearer. "
                "Feel door handles before opening — if hot, do not open. Assemble at least 300 meters away upwind."
            )
        elif 'accident' in em or 'collision' in em or 'crash' in em:
            return (
                "Turn on hazard warning lights and set safety triangles/flares if available. "
                "Do NOT move injured victims unless there is immediate risk of fire or vehicle explosion. "
                "Keep oncoming lanes clear for ambulances and emergency rescue vehicles."
            )
        elif 'earthquake' in em or 'collapse' in em or 'tremor' in em:
            return (
                "Drop, Cover, and Hold On beneath sturdy furniture. "
                "Stay clear of glass windows, mirrors, hanging fixtures, and unanchored tall furniture. "
                "If outdoors, move to an open area away from buildings, utility poles, and streetlights."
            )
        else:
            return (
                "Remain calm and stay in a secure, stable location. Conserve mobile phone battery for emergency communications. "
                "Keep phone lines open for responder calls and follow official emergency directives."
            )

    @classmethod
    def get_duplicate_status_text(cls, incident_dict):
        """Returns clean duplicate status description (Req 4)."""
        if incident_dict.get('is_duplicate'):
            parent_id = incident_dict.get('parent_incident_id')
            return f"⚠️ Duplicate Incident Cluster (Correlated and merged with Primary Incident #{parent_id})"
        return "✅ Unique Incident Verified (Passed Spatial Proximity & Temporal Cluster Checks)"

    @classmethod
    def get_ai_prompt_text(cls, emergency_type, location, urgency_reasons=None):
        """Returns the Multi-Agent coordinator prompt and triage summary for email body."""
        prompt = (
            f"AI Pipeline Directive: Coordinate real-time multi-agent triage for disaster type '{emergency_type}' at {location}. "
            "Synthesize citizen report telemetry, calculate geospatial priority score (0-100), identify duplicate clusters, "
            "and alert Police, Fire & Rescue, and Medical EMS units."
        )
        triage_note = urgency_reasons or "Evaluated high-priority threat factors, casualty risk, and access constraints."
        return prompt, triage_note

    @classmethod
    def send_new_incident_notification(cls, incident_dict, incident_id):
        """
        Sends email notification to emergency response officers when a new incident is submitted.
        Includes all required fields: ID, Type, Urgency, Location, Description, Duplicate Status, Date/Time, Safety Guidelines, Dashboard Link.
        """
        if not Config.EMAIL_NOTIFICATIONS_ENABLED:
            return {'success': False, 'status': 'DISABLED', 'message': 'Email notifications disabled in configuration.'}

        recipients = cls.get_recipient_list()
        results = []

        code = incident_dict.get('incident_code', f'INC-{incident_id}')
        em_type = incident_dict.get('emergency_type', 'General Emergency')
        title = incident_dict.get('title', f'{em_type} Emergency')
        location = incident_dict.get('location_address', 'Unknown Location')
        landmark = incident_dict.get('landmark', '')
        lat = incident_dict.get('latitude', 15.9080)
        lng = incident_dict.get('longitude', 80.4730)
        desc = incident_dict.get('description', 'No description provided.')
        urgency = incident_dict.get('urgency_level', 'MEDIUM')
        score = incident_dict.get('urgency_score', 50)
        urgency_reasons = incident_dict.get('urgency_reasons', '')
        is_sos = bool(incident_dict.get('is_sos'))
        sub_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
        people = incident_dict.get('people_affected', 0)
        trapped = incident_dict.get('trapped_count', 0)
        injured = incident_dict.get('injured_count', 0)

        dup_status_text = cls.get_duplicate_status_text(incident_dict)
        safety_guidelines = cls.get_safety_guidelines(em_type)
        ai_prompt, ai_triage = cls.get_ai_prompt_text(em_type, location, urgency_reasons)
        base_url = getattr(Config, 'APP_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
        dashboard_link = f"{base_url}/incident/{incident_id}"
        tracking_link = f"{base_url}/track/{code}"

        subject = f"{'🚨 CRITICAL SOS' if is_sos else '⚠️ EMERGENCY ALERT'}: [{code}] {title} ({em_type.upper()}) at {location[:40]} - Priority: {urgency}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f1f5f9; padding: 20px; }}
            .container {{ max-width: 680px; margin: 0 auto; background: #111827; border: 1px solid #374151; border-top: 5px solid {'#ef4444' if urgency == 'CRITICAL' else '#3b82f6'}; border-radius: 8px; overflow: hidden; }}
            .header {{ padding: 22px; background: rgba(0,0,0,0.35); border-bottom: 1px solid #374151; }}
            .title {{ font-size: 20px; font-weight: bold; color: {'#f87171' if urgency == 'CRITICAL' else '#60a5fa'}; margin: 0 0 8px; }}
            .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
            .badge-crit {{ background: #dc2626; color: #fff; }}
            .content {{ padding: 22px; }}
            .item {{ margin-bottom: 14px; }}
            .label {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: bold; letter-spacing: 0.5px; }}
            .val {{ font-size: 14px; color: #e2e8f0; margin-top: 3px; line-height: 1.4; }}
            .desc-box {{ background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; padding: 12px 14px; border-radius: 6px; margin-top: 4px; font-size: 13px; line-height: 1.5; color: #cbd5e1; }}
            .prompt-box {{ background: rgba(30, 41, 59, 0.7); border-left: 4px solid #8b5cf6; padding: 12px 14px; border-radius: 4px; margin: 16px 0; font-size: 12px; color: #ddd6fe; line-height: 1.5; }}
            .safety-box {{ background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 12px 14px; border-radius: 4px; margin: 16px 0; font-size: 13px; color: #a7f3d0; line-height: 1.5; }}
            .footer {{ padding: 16px 22px; background: rgba(0,0,0,0.4); border-top: 1px solid #374151; font-size: 11px; color: #64748b; text-align: center; }}
            .btn {{ display: inline-block; background: #2563eb; color: #fff; text-decoration: none; padding: 11px 24px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px; font-weight: bold;">DISASTERSYNC AI &bull; MULTI-AGENCY EMERGENCY DISPATCH</div>
              <h1 class="title">{code}: {title}</h1>
              <div>
                <span class="badge badge-crit">{urgency} (Score: {score}/100)</span>
                {'<span class="badge" style="background:#b91c1c; color:#fff; margin-left:6px;">CITIZEN 1-CLICK SOS BEACON</span>' if is_sos else ''}
              </div>
            </div>
            <div class="content">
              <div class="item">
                <div class="label">Incident Tracking ID</div>
                <div class="val"><strong style="color:#60a5fa; font-family:monospace; font-size:16px;">{code}</strong></div>
              </div>
              <div class="item">
                <div class="label">Emergency Type</div>
                <div class="val"><strong>{em_type}</strong></div>
              </div>
              <div class="item">
                <div class="label">AI Urgency Priority and Score</div>
                <div class="val"><strong>{urgency}</strong> &bull; Priority Score: <strong>{score}/100</strong></div>
              </div>
              <div class="item">
                <div class="label">Incident Location &amp; Coordinates</div>
                <div class="val">{location} {'(Landmark: ' + landmark + ')' if landmark else ''}<br><span style="color:#94a3b8; font-size:12px;">📍 GPS Geotag: {lat}° N, {lng}° E</span></div>
              </div>
              <div class="item">
                <div class="label">Duplicate Incident Status</div>
                <div class="val">{dup_status_text}</div>
              </div>
              <div class="item">
                <div class="label">Submission Date and Time</div>
                <div class="val">{sub_time}</div>
              </div>
              <div class="item">
                <div class="label">Citizens in Danger / Casualties</div>
                <div class="val">Affected: <strong>{people}</strong> | Trapped: <strong style="color:#f87171;">{trapped}</strong> | Injured: <strong style="color:#fbbf24;">{injured}</strong></div>
              </div>
              <div class="item">
                <div class="label">Emergency Description</div>
                <div class="desc-box">{desc}</div>
              </div>

              <!-- AI Multi-Agent Prompt & Reasoning Context -->
              <div class="prompt-box">
                <div style="font-weight: bold; margin-bottom: 4px; text-transform: uppercase; font-size: 11px;">🤖 AI Multi-Agent Coordinator Prompt &amp; Triage Assessment</div>
                <div style="margin-bottom: 6px;"><em>"{ai_prompt}"</em></div>
                <div><strong>Evaluation:</strong> {ai_triage}</div>
              </div>

              <!-- Citizen Safety Guidelines -->
              <div class="safety-box">
                <strong>Citizen Safety Guidelines:</strong><br>
                {safety_guidelines}
              </div>

              <div style="text-align: center; margin-top: 20px;">
                <a href="{dashboard_link}" class="btn">Open Command Center Action Plan &rarr;</a>
              </div>
            </div>
            <div class="footer">
              This emergency dispatch notification was generated by DisasterSync AI Coordinator Agent.<br>
              Delivered via Python SMTP &bull; Gmail Gateway &bull; AG-AI-01
            </div>
          </div>
        </body>
        </html>
        """

        plain_text = (
            f"DISASTERSYNC AI EMERGENCY DISPATCH ALERT\n"
            f"=========================================\n"
            f"Incident Tracking ID: {code}\n"
            f"Emergency Type: {em_type}\n"
            f"AI Urgency Priority: {urgency} (Score: {score}/100)\n"
            f"Location: {location} {'(Landmark: ' + landmark + ')' if landmark else ''}\n"
            f"Coordinates: {lat}° N, {lng}° E\n"
            f"Duplicate Status: {dup_status_text}\n"
            f"Submission Time: {sub_time}\n"
            f"Casualties: Affected: {people} | Trapped: {trapped} | Injured: {injured}\n\n"
            f"Emergency Description:\n{desc}\n\n"
            f"AI Multi-Agent Coordinator Prompt:\n{ai_prompt}\n"
            f"AI Triage Verdict: {ai_triage}\n\n"
            f"Citizen Safety Guidelines:\n{safety_guidelines}\n\n"
            f"Incident Dashboard Link: {dashboard_link}\n"
        )

        for recipient in recipients:
            # Enforce deduplication (Req 8 & 12)
            dedup_key = f"NEW_INCIDENT_{incident_id}_{recipient}"
            existing = database.query_db(
                "SELECT id, status FROM email_notifications WHERE dedup_key = %s",
                (dedup_key,),
                one=True
            )
            if existing:
                results.append({
                    'recipient': recipient,
                    'status': 'DUPLICATE_SKIPPED',
                    'message': f"Skipped duplicate email to {recipient}."
                })
                continue

            # Real SMTP dispatch
            status, error_msg = cls._dispatch_email(recipient, subject, plain_text, html_body)

            # Record in database
            database.execute_db(
                """INSERT INTO email_notifications 
                   (incident_id, recipient_email, subject, notification_type, status, error_message, dedup_key)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (incident_id, recipient, subject, 'NEW_INCIDENT', status, error_msg, dedup_key)
            )

            # Record in audit trail
            database.execute_db(
                """INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    incident_id,
                    'Email Notification Service',
                    'Automated Notifier',
                    'OFFICER_EMAIL_DISPATCHED',
                    f"Officer emergency alert to {recipient} result: {status}. {'Error: ' + str(error_msg) if error_msg else ''}"
                )
            )

            results.append({
                'recipient': recipient,
                'status': status,
                'error': error_msg
            })

        return {
            'success': any(r['status'] in ('SENT', 'DUPLICATE_SKIPPED') for r in results),
            'results': results,
            'incident_code': code
        }

    @classmethod
    def send_user_confirmation_email(cls, incident_dict, incident_id, user_email):
        """
        Sends an automatic confirmation email to the citizen who reported the emergency (Req 3).
        Includes all 9 required fields + AI prompt context.
        """
        if not Config.EMAIL_NOTIFICATIONS_ENABLED:
            return {'success': False, 'status': 'DISABLED', 'message': 'Email notifications disabled.'}

        if not cls.is_valid_email(user_email):
            return {'success': False, 'status': 'FAILED', 'message': f"Invalid citizen email format: '{user_email}'"}

        user_email = user_email.strip().lower()
        code = incident_dict.get('incident_code', f'INC-{incident_id}')
        em_type = incident_dict.get('emergency_type', 'General Emergency')
        title = incident_dict.get('title', f'{em_type} Emergency')
        location = incident_dict.get('location_address', 'Unknown Location')
        landmark = incident_dict.get('landmark', '')
        lat = incident_dict.get('latitude', 15.9080)
        lng = incident_dict.get('longitude', 80.4730)
        desc = incident_dict.get('description', 'No description provided.')
        urgency = incident_dict.get('urgency_level', 'MEDIUM')
        score = incident_dict.get('urgency_score', 50)
        urgency_reasons = incident_dict.get('urgency_reasons', '')
        sub_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')

        dup_status_text = cls.get_duplicate_status_text(incident_dict)
        safety_guidelines = cls.get_safety_guidelines(em_type)
        ai_prompt, ai_triage = cls.get_ai_prompt_text(em_type, location, urgency_reasons)
        base_url = getattr(Config, 'APP_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
        dashboard_link = f"{base_url}/incident/{incident_id}"
        tracking_link = f"{base_url}/track/{code}"

        # Deduplication check
        dedup_key = f"USER_CONFIRM_{incident_id}_{user_email}"
        existing = database.query_db(
            "SELECT id, status FROM email_notifications WHERE dedup_key = %s",
            (dedup_key,),
            one=True
        )
        if existing:
            return {
                'success': True,
                'status': 'DUPLICATE_SKIPPED',
                'recipient': user_email,
                'message': f"Confirmation email already dispatched to {user_email}."
            }

        subject = f"✅ Emergency Report Confirmation: [{code}] {em_type.upper()} Received - DisasterSync AI"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f1f5f9; padding: 20px; }}
            .container {{ max-width: 680px; margin: 0 auto; background: #111827; border: 1px solid #374151; border-top: 5px solid #10b981; border-radius: 8px; overflow: hidden; }}
            .header {{ padding: 22px; background: rgba(0,0,0,0.35); border-bottom: 1px solid #374151; }}
            .title {{ font-size: 20px; font-weight: bold; color: #34d399; margin: 0 0 8px; }}
            .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
            .badge-green {{ background: #065f46; color: #34d399; border: 1px solid #10b981; }}
            .content {{ padding: 22px; }}
            .item {{ margin-bottom: 14px; }}
            .label {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: bold; letter-spacing: 0.5px; }}
            .val {{ font-size: 14px; color: #e2e8f0; margin-top: 3px; line-height: 1.4; }}
            .desc-box {{ background: rgba(15, 23, 42, 0.85); border: 1px solid #334155; padding: 12px 14px; border-radius: 6px; margin-top: 4px; font-size: 13px; line-height: 1.5; color: #cbd5e1; }}
            .prompt-box {{ background: rgba(30, 41, 59, 0.7); border-left: 4px solid #8b5cf6; padding: 12px 14px; border-radius: 4px; margin: 16px 0; font-size: 12px; color: #ddd6fe; line-height: 1.5; }}
            .safety-box {{ background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 14px 16px; border-radius: 4px; margin: 16px 0; font-size: 13px; color: #a7f3d0; line-height: 1.5; }}
            .footer {{ padding: 16px 22px; background: rgba(0,0,0,0.4); border-top: 1px solid #374151; font-size: 11px; color: #64748b; text-align: center; }}
            .btn {{ display: inline-block; background: #10b981; color: #fff; text-decoration: none; padding: 11px 24px; border-radius: 6px; font-weight: bold; font-size: 14px; margin-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px; font-weight: bold;">DISASTERSYNC AI &bull; CITIZEN EMERGENCY ACKNOWLEDGEMENT</div>
              <h1 class="title">Emergency Report Received &amp; Verified</h1>
              <div>
                <span class="badge badge-green">Incident Tracking ID: {code}</span>
              </div>
            </div>
            <div class="content">
              <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5; margin-top: 0;">
                Dear Citizen,<br>
                Thank you for reporting this incident. Your report has been accepted and triaged by the <strong>DisasterSync AI Multi-Agent Coordination Platform</strong>.
                Authorized emergency response commanders and field units have received your alert.
              </p>

              <div class="item">
                <div class="label">Incident Tracking ID</div>
                <div class="val"><strong style="color: #60a5fa; font-family: monospace; font-size: 16px;">{code}</strong></div>
              </div>
              <div class="item">
                <div class="label">Emergency Type</div>
                <div class="val"><strong>{em_type}</strong></div>
              </div>
              <div class="item">
                <div class="label">AI Urgency Priority and Score</div>
                <div class="val"><strong>{urgency}</strong> &bull; Priority Score: <strong>{score}/100</strong></div>
              </div>
              <div class="item">
                <div class="label">Incident Location</div>
                <div class="val">{location} {'(Landmark: ' + landmark + ')' if landmark else ''}<br><span style="color:#94a3b8; font-size:12px;">📍 GPS Geotag: {lat}° N, {lng}° E</span></div>
              </div>
              <div class="item">
                <div class="label">Duplicate Incident Status</div>
                <div class="val">{dup_status_text}</div>
              </div>
              <div class="item">
                <div class="label">Submission Date and Time</div>
                <div class="val">{sub_time}</div>
              </div>
              <div class="item">
                <div class="label">Your Submitted Description</div>
                <div class="desc-box">{desc}</div>
              </div>

              <!-- AI Multi-Agent Prompt & Reasoning Context -->
              <div class="prompt-box">
                <div style="font-weight: bold; margin-bottom: 4px; text-transform: uppercase; font-size: 11px;">🤖 AI Multi-Agent Coordinator Prompt &amp; Triage Assessment</div>
                <div style="margin-bottom: 6px;"><em>"{ai_prompt}"</em></div>
                <div><strong>Evaluation:</strong> {ai_triage}</div>
              </div>

              <!-- Citizen Safety Guidelines -->
              <div class="safety-box">
                <strong>Citizen Safety Guidelines:</strong><br>
                {safety_guidelines}
              </div>

              <div style="text-align: center; margin-top: 20px;">
                <a href="{dashboard_link}" class="btn">Track Your Incident Live &rarr;</a>
              </div>
            </div>
            <div class="footer">
              DisasterSync AI Emergency Coordination Center &bull; Automated citizen receipt<br>
              Delivered via Python SMTP &bull; Gmail Gateway &bull; AG-AI-01
            </div>
          </div>
        </body>
        </html>
        """

        plain_text = (
            f"DISASTERSYNC AI EMERGENCY REPORT CONFIRMATION\n"
            f"============================================\n"
            f"Dear Citizen,\n"
            f"Your emergency report has been received and triaged by DisasterSync AI.\n\n"
            f"Incident Tracking ID: {code}\n"
            f"Emergency Type: {em_type}\n"
            f"AI Urgency Priority: {urgency} (Score: {score}/100)\n"
            f"Location: {location} {'(Landmark: ' + landmark + ')' if landmark else ''}\n"
            f"Coordinates: {lat}° N, {lng}° E\n"
            f"Duplicate Status: {dup_status_text}\n"
            f"Submission Date & Time: {sub_time}\n\n"
            f"Description:\n{desc}\n\n"
            f"AI Multi-Agent Coordinator Prompt:\n{ai_prompt}\n"
            f"AI Triage Verdict: {ai_triage}\n\n"
            f"Citizen Safety Guidelines:\n{safety_guidelines}\n\n"
            f"Incident Dashboard Link: {dashboard_link}\n"
        )

        status, error_msg = cls._dispatch_email(user_email, subject, plain_text, html_body)

        database.execute_db(
            """INSERT INTO email_notifications 
               (incident_id, recipient_email, subject, notification_type, status, error_message, dedup_key)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (incident_id, user_email, subject, 'USER_CONFIRMATION', status, error_msg, dedup_key)
        )

        database.execute_db(
            """INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                incident_id,
                'Citizen Notifier',
                'Automated Notifier',
                'USER_CONFIRMATION_EMAIL_DISPATCHED',
                f"Confirmation email dispatched to citizen ({user_email}) with status {status}. {'Error: ' + str(error_msg) if error_msg else ''}"
            )
        )

        return {
            'success': (status == 'SENT'),
            'status': status,
            'recipient': user_email,
            'error': error_msg,
            'message': f"Confirmation email {status.lower()} for {user_email}."
        }

    @classmethod
    def send_status_change_notification(cls, incident, old_status, new_status, officer_name, note=''):
        """
        Sends email notification when incident status changes (Req 5).
        Dispatches to emergency officers and to the citizen who reported the incident.
        """
        if not Config.EMAIL_NOTIFICATIONS_ENABLED:
            return {'success': False, 'status': 'DISABLED'}

        incident_id = incident['id']
        code = incident['incident_code']
        em_type = incident['emergency_type']
        location = incident['location_address']
        urgency = incident.get('urgency_level', 'MEDIUM')
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
        safety_guidelines = cls.get_safety_guidelines(em_type)
        base_url = getattr(Config, 'APP_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
        dashboard_link = f"{base_url}/incident/{incident_id}"
        tracking_link = f"{base_url}/track/{code}"

        recipients = cls.get_recipient_list()
        results = []

        subject = f"🔔 [DisasterSync AI] Status Update: {code} ({em_type}) is now '{new_status}'"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f1f5f9; padding: 20px; }}
            .container {{ max-width: 650px; margin: 0 auto; background: #111827; border: 1px solid #374151; border-top: 5px solid #10b981; border-radius: 8px; overflow: hidden; }}
            .header {{ padding: 20px; background: rgba(0,0,0,0.3); border-bottom: 1px solid #374151; }}
            .title {{ font-size: 18px; font-weight: bold; color: #34d399; margin: 0; }}
            .content {{ padding: 20px; }}
            .status-pill {{ display: inline-block; padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; }}
            .item {{ margin-bottom: 12px; }}
            .label {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: bold; }}
            .val {{ font-size: 14px; color: #e2e8f0; margin-top: 2px; }}
            .footer {{ padding: 14px 20px; background: rgba(0,0,0,0.4); border-top: 1px solid #374151; font-size: 11px; color: #64748b; text-align: center; }}
            .btn {{ display: inline-block; background: #2563eb; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; margin-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px; font-weight: bold;">DISASTERSYNC AI &bull; STATUS CHANGE ADVISORY</div>
              <h1 class="title">Incident #{code} Status Progressed to '{new_status}'</h1>
            </div>
            <div class="content">
              <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 16px;">
                <span class="status-pill" style="background:#374151; color:#9ca3af;">{old_status}</span>
                <span style="font-size: 18px; color: #60a5fa;">&rarr;</span>
                <span class="status-pill" style="background:#065f46; color:#34d399; border:1px solid #10b981;">{new_status}</span>
              </div>
              <div class="item">
                <div class="label">Emergency Type</div>
                <div class="val"><strong>{em_type}</strong> (Priority: {urgency})</div>
              </div>
              <div class="item">
                <div class="label">Location</div>
                <div class="val">{location}</div>
              </div>
              <div class="item">
                <div class="label">Updated By Authorized Officer</div>
                <div class="val">{officer_name} &bull; {update_time}</div>
              </div>
              {f'<div class="item"><div class="label">Officer Operational Note</div><div class="val" style="background:rgba(255,255,255,0.05); padding:8px 12px; border-radius:4px;">{note}</div></div>' if note else ''}
              
              <div style="background:rgba(16, 185, 129, 0.1); border-left:4px solid #10b981; padding:10px 14px; border-radius:4px; margin-top:14px; font-size:12px; color:#a7f3d0;">
                <strong>Ongoing Safety Guidance:</strong> {safety_guidelines}
              </div>

              <div style="text-align: center;">
                <a href="{dashboard_link}" class="btn">View Updated Status in Command Center &rarr;</a>
              </div>
            </div>
            <div class="footer">
              DisasterSync AI Incident Governance &bull; Delivered via Python SMTP
            </div>
          </div>
        </body>
        </html>
        """

        plain_text = (
            f"DISASTERSYNC AI STATUS CHANGE ADVISORY\n"
            f"Incident: {code} ({em_type})\n"
            f"Status: {old_status} -> {new_status}\n"
            f"Location: {location}\n"
            f"Updated By: {officer_name} at {update_time}\n"
            f"Note: {note or 'None'}\n"
            f"Safety: {safety_guidelines}\n\n"
            f"Dashboard: {dashboard_link}\n"
        )

        for recipient in recipients:
            dedup_key = f"STATUS_CHANGE_{incident_id}_{old_status}_{new_status}_{recipient}"
            existing = database.query_db(
                "SELECT id, status FROM email_notifications WHERE dedup_key = %s",
                (dedup_key,),
                one=True
            )
            if existing:
                results.append({
                    'recipient': recipient,
                    'status': 'DUPLICATE_SKIPPED',
                    'message': f"Skipped duplicate status email to {recipient}."
                })
                continue

            status, error_msg = cls._dispatch_email(recipient, subject, plain_text, html_body)

            database.execute_db(
                """INSERT INTO email_notifications 
                   (incident_id, recipient_email, subject, notification_type, old_status, new_status, status, error_message, dedup_key)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (incident_id, recipient, subject, 'STATUS_CHANGE', old_status, new_status, status, error_msg, dedup_key)
            )

            database.execute_db(
                """INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    incident_id,
                    officer_name,
                    'Incident Officer',
                    'STATUS_CHANGE_EMAIL_DISPATCHED',
                    f"Email alert sent to {recipient} for status change to '{new_status}' (Status: {status})."
                )
            )

            results.append({
                'recipient': recipient,
                'status': status,
                'error': error_msg
            })

        # Also dispatch status progression advisory to reporting citizen (Req 5)
        user_email = incident.get('reporter_email')
        if user_email and cls.is_valid_email(user_email):
            user_email = user_email.strip().lower()
            user_dedup = f"USER_STATUS_CHANGE_{incident_id}_{old_status}_{new_status}_{user_email}"
            existing_user = database.query_db(
                "SELECT id FROM email_notifications WHERE dedup_key = %s",
                (user_dedup,),
                one=True
            )
            if not existing_user:
                u_subj = f"🔔 Status Update: Emergency [{code}] is now '{new_status}' - DisasterSync AI"
                u_html = f"""
                <!DOCTYPE html>
                <html>
                <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f1f5f9; padding: 20px;">
                  <div style="max-width: 620px; margin: 0 auto; background: #111827; border: 1px solid #374151; border-top: 5px solid #3b82f6; border-radius: 8px; padding: 22px;">
                    <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px; font-weight: bold;">DISASTERSYNC AI &bull; CITIZEN STATUS UPDATE</div>
                    <h2 style="color: #60a5fa; margin: 8px 0 16px;">Incident Status Progressed: {new_status}</h2>
                    <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5;">
                      Dear Citizen, your reported incident <strong>{code}</strong> ({em_type}) has been updated by authorized emergency commanders.
                    </p>
                    <div style="background: rgba(15,23,42,0.85); border: 1px solid #334155; padding: 14px; border-radius: 6px; margin: 16px 0;">
                      <div><strong>Operational Status:</strong> <span style="color:#34d399; font-weight:bold;">{old_status} &rarr; {new_status}</span></div>
                      <div style="margin-top:6px;"><strong>Updated At:</strong> {update_time}</div>
                      <div style="margin-top:6px;"><strong>Duty Officer:</strong> {officer_name}</div>
                      {f'<div style="margin-top:8px; padding-top:8px; border-top:1px solid #334155; font-size:13px; color:#cbd5e1;"><strong>Officer Note:</strong> {note}</div>' if note else ''}
                    </div>
                    <div style="background:rgba(16, 185, 129, 0.1); border-left:4px solid #10b981; padding:10px 14px; border-radius:4px; margin-top:14px; font-size:12px; color:#a7f3d0;">
                      <strong>Safety Guidelines:</strong> {safety_guidelines}
                    </div>
                    <div style="text-align: center; margin-top: 20px;">
                      <a href="{tracking_link}" style="display:inline-block; background:#2563eb; color:#fff; padding:11px 24px; text-decoration:none; border-radius:6px; font-weight:bold;">Track Incident Live &rarr;</a>
                    </div>
                  </div>
                </body>
                </html>
                """
                u_plain = f"DISASTERSYNC AI CITIZEN STATUS UPDATE\nIncident: {code} ({em_type})\nStatus: {old_status} -> {new_status}\nUpdated At: {update_time}\nTrack Online: {tracking_link}\n"
                u_status, u_err = cls._dispatch_email(user_email, u_subj, u_plain, u_html)
                database.execute_db(
                    """INSERT INTO email_notifications 
                       (incident_id, recipient_email, subject, notification_type, old_status, new_status, status, error_message, dedup_key)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (incident_id, user_email, u_subj, 'USER_STATUS_CHANGE', old_status, new_status, u_status, u_err, user_dedup)
                )
                results.append({'recipient': user_email, 'status': u_status, 'error': u_err, 'type': 'user_status'})

        return {'success': any(r['status'] == 'SENT' for r in results), 'results': results}

    @classmethod
    def send_test_email(cls, recipient_email=None):
        """
        Sends an instant real test email to verify Gmail SMTP gateway configuration (Req 6).
        Triggered from the Admin Dashboard 'Test Email' button.
        """
        if not recipient_email or not recipient_email.strip():
            recipients = cls.get_recipient_list()
            recipient = recipients[0] if recipients else 'officer.emergency@disastersync.ai'
        else:
            recipient = recipient_email.strip().lower()

        if not cls.is_valid_email(recipient):
            return {
                'success': False,
                'status': 'FAILED',
                'recipient': recipient,
                'error': f"Invalid email format: '{recipient}'",
                'message': f"Email Failed: Invalid recipient address format."
            }

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
        minute_token = datetime.now().strftime('%Y%m%d%H%M')
        dedup_key = f"TEST_EMAIL_{recipient}_{minute_token}"

        subject = f"🧪 [DisasterSync AI] Gmail SMTP Gateway Diagnostic Test ({datetime.now().strftime('%H:%M:%S')})"

        smtp_server = Config.SMTP_SERVER
        smtp_port = Config.SMTP_PORT
        smtp_user = Config.SMTP_USER or "Not configured in .env"
        tls_enabled = "Enabled (STARTTLS)" if Config.SMTP_USE_TLS else "Disabled"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f1f5f9; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #111827; border: 1px solid #374151; border-top: 5px solid #38bdf8; border-radius: 8px; overflow: hidden; }}
            .header {{ padding: 20px; background: rgba(0,0,0,0.3); border-bottom: 1px solid #374151; }}
            .title {{ font-size: 18px; font-weight: bold; color: #38bdf8; margin: 0; }}
            .content {{ padding: 20px; }}
            .table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
            .table td {{ padding: 8px 10px; border-bottom: 1px solid #1f2937; font-size: 13px; }}
            .table td.lbl {{ color: #94a3b8; font-weight: bold; width: 40%; }}
            .table td.val {{ color: #e2e8f0; font-family: monospace; }}
            .badge-ok {{ background: #065f46; color: #34d399; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
            .footer {{ padding: 14px 20px; background: rgba(0,0,0,0.4); border-top: 1px solid #374151; font-size: 11px; color: #64748b; text-align: center; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px; font-weight: bold;">DISASTERSYNC AI &bull; SMTP DIAGNOSTIC SUITE</div>
              <h1 class="title">Gmail SMTP Gateway Live Connection Test</h1>
            </div>
            <div class="content">
              <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5; margin-top: 0;">
                This diagnostic transmission confirms that your DisasterSync AI Gmail SMTP notification gateway is actively configured and successfully transmitting emergency dispatches.
              </p>
              <table class="table">
                <tr><td class="lbl">Gateway Status</td><td class="val"><span class="badge-ok">ACTIVE / VERIFIED</span></td></tr>
                <tr><td class="lbl">Target Recipient</td><td class="val">{recipient}</td></tr>
                <tr><td class="lbl">SMTP Host</td><td class="val">{smtp_server}</td></tr>
                <tr><td class="lbl">SMTP Port</td><td class="val">{smtp_port}</td></tr>
                <tr><td class="lbl">Encryption</td><td class="val">{tls_enabled}</td></tr>
                <tr><td class="lbl">Authenticated User</td><td class="val">{smtp_user}</td></tr>
                <tr><td class="lbl">Transmission Time</td><td class="val">{now_str}</td></tr>
              </table>
            </div>
            <div class="footer">
              DisasterSync AI Incident Governance &bull; Live SMTP Audit<br>
              Delivered via Python SMTP &bull; Gmail Gateway &bull; AG-AI-01
            </div>
          </div>
        </body>
        </html>
        """

        plain_text = (
            f"DISASTERSYNC AI GMAIL SMTP GATEWAY TEST\n"
            f"Status: Active / Verified\n"
            f"Recipient: {recipient}\n"
            f"SMTP Server: {smtp_server}:{smtp_port}\n"
            f"TLS: {tls_enabled}\n"
            f"Authenticated User: {smtp_user}\n"
            f"Timestamp: {now_str}\n"
        )

        status, error_msg = cls._dispatch_email(recipient, subject, plain_text, html_body)

        database.execute_db(
            """INSERT INTO email_notifications 
               (incident_id, recipient_email, subject, notification_type, status, error_message, dedup_key)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (0, recipient, subject, 'SYSTEM_TEST', status, error_msg, dedup_key)
        )

        database.execute_db(
            """INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                None,
                'System Admin',
                'Command Duty Officer',
                'SMTP_TEST_EMAIL_DISPATCHED',
                f"Test email dispatched to {recipient} with status {status}. Server: {smtp_server}:{smtp_port}. {'Error: ' + str(error_msg) if error_msg else ''}"
            )
        )

        if status == 'SENT':
            msg = f"Email Sent: Successfully accepted by Gmail SMTP server for delivery to {recipient}."
        else:
            msg = f"Email Failed: {error_msg}"

        return {
            'success': (status == 'SENT'),
            'status': status,
            'recipient': recipient,
            'error': error_msg,
            'message': msg
        }

    @classmethod
    def _dispatch_email(cls, recipient, subject, plain_text, html_body):
        """
        Dispatches email via Python SMTP and Gmail (or configured SMTP server).
        Returns 'SENT' ONLY after SMTP server confirms acceptance (Req 7, 8, 9).
        Returns 'FAILED' with diagnostic message if credentials are missing or SMTP fails.
        """
        # Validate email syntax (Req 12)
        if not cls.is_valid_email(recipient):
            return 'FAILED', f"Invalid email format: '{recipient}'"

        smtp_user = Config.SMTP_USER
        smtp_pass = Config.SMTP_PASSWORD

        # Check if Gmail credentials are configured in .env file (Req 8 & 10)
        if not smtp_user or not smtp_pass:
            return 'FAILED', 'Gmail credentials (GMAIL_USER / GMAIL_APP_PASSWORD) not configured in .env file. Real email cannot be sent.'

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"DisasterSync AI Alerts <{smtp_user}>"
            msg['To'] = recipient

            part1 = MIMEText(plain_text, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            # Connect to Gmail SMTP server (smtp.gmail.com:587)
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=12)
            if Config.SMTP_USE_TLS:
                server.starttls()

            # Authenticate using App Password
            server.login(smtp_user, smtp_pass)

            # Send email - accepted by Gmail SMTP server
            server.sendmail(smtp_user, [recipient], msg.as_string())
            server.quit()

            # Only marked 'SENT' after SMTP server has accepted the email for delivery
            return 'SENT', None
        except smtplib.SMTPAuthenticationError as auth_err:
            return 'FAILED', f"Gmail Authentication Error (535): Invalid email or App Password. Check GMAIL_APP_PASSWORD in .env. ({auth_err.smtp_error.decode('utf-8', errors='ignore') if hasattr(auth_err, 'smtp_error') and auth_err.smtp_error else str(auth_err)})"
        except smtplib.SMTPConnectError as conn_err:
            return 'FAILED', f"SMTP Connection Failed: Could not connect to {Config.SMTP_SERVER}:{Config.SMTP_PORT}. ({str(conn_err)})"
        except smtplib.SMTPRecipientsRefused as rec_err:
            return 'FAILED', f"Recipient Refused: Gmail rejected delivery to {recipient}. ({str(rec_err)})"
        except Exception as e:
            return 'FAILED', f"SMTP Delivery Error: {str(e)}"

    @classmethod
    def get_incident_emails(cls, incident_id):
        """Fetches all email notification logs for a specific incident."""
        return database.query_db(
            "SELECT * FROM email_notifications WHERE incident_id = %s ORDER BY sent_at DESC",
            (incident_id,)
        )
