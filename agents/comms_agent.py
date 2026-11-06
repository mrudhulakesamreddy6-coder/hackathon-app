from datetime import datetime

class CommunicationAgent:
    """
    Communication Agent:
    Prepares simulated alert dispatches for Police, Fire, Hospitals, and Rescue.
    Generates draft status bulletins and civilian safety warnings.
    """

    @staticmethod
    def generate_alerts(incident):
        """
        Generates simulated alert drafts for each relevant emergency agency.
        These alerts will be stored in simulated_alerts table as PENDING_APPROVAL
        until an authorized human officer approves them.
        """
        code = incident.get('incident_code', 'INC-UNKNOWN')
        em_type = incident.get('emergency_type', 'General Emergency')
        loc = incident.get('location_address', 'Unknown Location')
        landmark = incident.get('landmark', '')
        desc = incident.get('description', '')
        people = incident.get('people_affected', 0)
        trapped = incident.get('trapped_count', 0)
        injured = incident.get('injured_count', 0)
        urgency = incident.get('urgency_level', 'MEDIUM')
        is_sos = incident.get('is_sos', False)

        alerts = []
        loc_str = f"{loc}" + (f" (Near {landmark})" if landmark else "")

        # 1. Police Alert
        police_msg = (
            f"[SIMULATED CAD DISPATCH] PRIORITY: {urgency} | INCIDENT: {code} | TYPE: {em_type.upper()} | "
            f"LOCATION: {loc_str}. Require traffic perimeter, crowd control, and route clearance for incoming rescue. "
            f"Report details: '{desc[:100]}...'. Affected: ~{people}. Authorized dispatch pending officer confirmation."
        )
        alerts.append({
            'agency_type': 'police',
            'agency_name': 'Police Department Command',
            'alert_channel': 'CAD Terminal & Encrypted APCO-25 Radio',
            'alert_title': f"Simulated 10-33 / Tactical Cordon: {em_type} at {loc_str}",
            'alert_message': police_msg
        })

        # 2. Fire & Rescue Alert
        fire_msg = (
            f"[SIMULATED CAD DISPATCH] PRIORITY: {urgency} | INCIDENT: {code} | TYPE: {em_type.upper()} | "
            f"LOCATION: {loc_str}. Deploy initial response apparatus. "
            f"Trapped persons reported: {trapped}. Environmental hazard check required. "
            f"Report details: '{desc[:100]}...'. Authorized dispatch pending officer confirmation."
        )
        alerts.append({
            'agency_type': 'fire',
            'agency_name': 'Fire & Rescue Operations',
            'alert_channel': 'Firehouse Pager & Mobile Data Computer (MDC)',
            'alert_title': f"Simulated Dispatch: Heavy Rescue / Hazmat at {loc_str}",
            'alert_message': fire_msg
        })

        # 3. Medical Alert (if injuries > 0, SOS, or critical)
        if injured > 0 or is_sos or urgency in ['CRITICAL', 'HIGH']:
            med_msg = (
                f"[SIMULATED EMS DISPATCH] PRIORITY: {urgency} | INCIDENT: {code} | TRIAGE: {'RED' if urgency == 'CRITICAL' else 'YELLOW'} | "
                f"LOCATION: {loc_str}. Reported injuries: {injured}. Prepare Trauma Center ICU & standby ALS/BLS fleet. "
                f"Authorized dispatch pending officer confirmation."
            )
            alerts.append({
                'agency_type': 'medical',
                'agency_name': 'District Emergency Medical Services (EMS)',
                'alert_channel': 'Hospital Trauma Net & EMS Radio',
                'alert_title': f"Simulated Mass Casualty / Trauma Standby: {loc_str}",
                'alert_message': med_msg
            })

        # 4. NDRF / Disaster Rescue Alert (if flood, earthquake, SOS, or trapped > 0)
        if is_sos or trapped > 0 or em_type.lower() in ['flood', 'earthquake', 'landslide', 'cyclone', 'storm']:
            rescue_msg = (
                f"[SIMULATED NDRF DISPATCH] PRIORITY: {urgency} | INCIDENT: {code} | DISASTER: {em_type.upper()} | "
                f"LOCATION: {loc_str}. Mobilize specialized Disaster Response Battalion. "
                f"Trapped: {trapped}, Affected: ~{people}. Prepare boats/shoreside search gear. "
                f"Authorized deployment pending human commander signature."
            )
            alerts.append({
                'agency_type': 'rescue',
                'agency_name': 'NDRF / Disaster Rescue Unit',
                'alert_channel': 'National Emergency Communications Sat-Link',
                'alert_title': f"Simulated SAR Mobilization: {em_type} at {loc_str}",
                'alert_message': rescue_msg
            })

        # Public bulletin
        bulletin = (
            f"PUBLIC SAFETY BULLETIN: Incident {code} reported at {loc_str}. "
            f"Type: {em_type}. Citizens are strongly advised to keep clear of {loc_str} to allow emergency vehicle access. "
            f"If in the affected zone, follow official guidance and remain calm."
        )

        return alerts, bulletin

