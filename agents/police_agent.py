class PoliceCoordinationAgent:
    """
    Police Coordination Agent:
    Organizes public-safety requests, crowd control, road perimeters,
    evacuation corridors, and agency status tracking.
    """

    @staticmethod
    def analyze(incident):
        emergency_type = (incident.get('emergency_type') or '').lower()
        people_affected = int(incident.get('people_affected') or 0)
        is_sos = bool(incident.get('is_sos'))
        desc = (incident.get('description') or '').lower()

        actions = []
        priority = "Normal"
        confidence = 0.90
        evidence = f"Reported disaster type: {incident.get('emergency_type')}, Location: {incident.get('location_address')}."

        # Public safety logic
        if is_sos or 'trapped' in desc or people_affected > 10:
            priority = "URGENT"
            actions.append("Establish a 500-meter safety perimeter and clear emergency lanes for incoming rescue vehicles.")
            actions.append("Deploy traffic police to key intersections along the arterial access corridor.")
        else:
            actions.append("Dispatch local patrol unit to verify ground conditions and secure incident perimeter.")

        if 'flood' in emergency_type or 'water' in desc:
            actions.append("Block submerged bridges, underpasses, and low-lying roads to prevent civilian vehicular drownings.")
            actions.append("Support local administrative teams in escorting civilians along safe high-ground evacuation routes.")
            evidence += " Waterlogging/submerged roads detected in report."
        elif 'fire' in emergency_type or 'explosion' in desc:
            actions.append("Enforce immediate crowd evacuation to minimum 300m upwind safety zone.")
            actions.append("Prevent unauthorized civilian re-entry into burning/hazardous structures.")
            evidence += " Structural fire / thermal hazard flagged."
        elif 'accident' in emergency_type or 'collision' in desc:
            actions.append("Divert oncoming highway traffic to alternate service lanes immediately.")
            actions.append("Preserve incident site evidence while clearing safe access for ambulances.")
            evidence += " Roadway blockage and vehicular collision present."
        elif 'earthquake' in emergency_type or 'collapse' in desc:
            actions.append("Cordon off cracked structures and high-tension utility poles prone to collapse.")
            actions.append("Monitor for secondary tremors and prevent stampedes in open congregation zones.")
            evidence += " Seismic shock / structural instability risk."
        else:
            actions.append("Maintain situational awareness and prevent panic among bystanders.")

        actions.append("Maintain continuous radio liaison with Incident Command Center.")

        summary = (
            f"Police Coordination recommends {priority} security measures: "
            f"Cordon off {incident.get('location_address')}, clear evacuation paths, and manage traffic flow."
        )

        return {
            'agent_name': "Police Coordination Agent",
            'priority_level': priority,
            'summary': summary,
            'suggested_actions': actions,
            'evidence_refs': evidence,
            'confidence': confidence
        }

