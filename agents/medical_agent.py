class MedicalAssistanceAgent:
    """
    Medical Assistance Agent:
    Summarizes reported medical needs, casualty triage classification,
    facility bed capacity, and ambulance dispatch recommendations.
    """

    @staticmethod
    def analyze(incident):
        emergency_type = (incident.get('emergency_type') or '').lower()
        injured_count = int(incident.get('injured_count') or 0)
        people_affected = int(incident.get('people_affected') or 0)
        is_sos = bool(incident.get('is_sos'))
        desc = (incident.get('description') or '').lower()

        actions = []
        priority = "Normal"
        confidence = 0.88
        triage_category = "Green (Minor)"
        evidence = f"Reported Injuries: {injured_count}, People Affected: {people_affected}."

        # Estimate triage category and ambulance demand
        if is_sos or injured_count >= 5 or 'severe' in desc or 'critical' in desc or 'bleeding' in desc or 'unconscious' in desc:
            priority = "URGENT MEDICAL"
            triage_category = "Red (Immediate / Life-Threatening)"
            ambulances_needed = max(2, (injured_count + 1) // 2)
            actions.append(f"Dispatch {ambulances_needed} Advanced Life Support (ALS) Ambulances equipped with portable ventilators and defibrillators.")
            actions.append("Issue Mass Casualty Triage alert to Nearest District Hospital Trauma Center.")
            actions.append("Reserve minimum 5 Emergency ICU beds and activate on-call orthopedic/trauma surgical teams.")
            evidence += " Critical injuries or active SOS requiring immediate advanced trauma stabilization."
        elif injured_count > 0:
            priority = "HIGH"
            triage_category = "Yellow (Delayed / Urgent)"
            actions.append(f"Dispatch {max(1, injured_count // 3)} Basic Life Support (BLS) Ambulances with certified paramedics.")
            actions.append("Establish a temporary Field Triage Station adjacent to the safe zone.")
            evidence += " Non-fatal or moderate trauma requiring on-site stabilization."
        else:
            triage_category = "Green (Preventive / Outpatient)"
            actions.append("Alert Community Health Center to place emergency medicine reserves on standby.")
            actions.append("Prepare emergency medical kits (antiseptics, bandages, hydration solutions).")

        # Specific disaster health advisories
        if 'flood' in emergency_type:
            actions.append("Stock anti-venom, water-purification chlorine tablets, and hypothermia thermal blankets.")
        elif 'fire' in emergency_type:
            actions.append("Mobilize high-flow oxygen therapy supplies and sterile burn-dressing saline kits.")
        elif 'earthquake' in emergency_type:
            actions.append("Prepare for crush syndrome protocols (IV saline rehydration before extrication).")

        summary = (
            f"Medical Assistance Agent reports Triage Status: {triage_category}. "
            f"Priority: {priority}. Recommended medical dispatch: "
            f"{'ALS Ambulances + Trauma Readiness' if 'Red' in triage_category else 'BLS Ambulance + Field First Aid'}."
        )

        return {
            'agent_name': "Medical Assistance Agent",
            'priority_level': priority,
            'summary': summary,
            'suggested_actions': actions,
            'evidence_refs': evidence,
            'confidence': confidence
        }

