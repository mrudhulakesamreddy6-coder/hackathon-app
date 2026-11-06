import uuid
from datetime import datetime
from agents.duplicate_agent import DuplicateDetectionAgent
from agents.police_agent import PoliceCoordinationAgent
from agents.fire_rescue_agent import FireRescueAgent
from agents.medical_agent import MedicalAssistanceAgent
from agents.resource_agent import ResourceManagementAgent
from agents.comms_agent import CommunicationAgent

class CoordinatorAgent:
    """
    Coordinator Agent:
    Central orchestrator of DisasterSync AI.
    - Validates intake
    - Computes transparent urgency score & explainability breakdown
    - Delegates to specialized agents
    - Integrates duplicate detection
    - Formulates unified incident response plan for Human Officer approval
    """

    @classmethod
    def process_incident(cls, incident_data, existing_incidents=None, available_resources=None):
        if existing_incidents is None:
            existing_incidents = []
        if available_resources is None:
            available_resources = []

        # 1. Calculate Urgency Score & Reasons
        urgency_score, urgency_level, urgency_reasons = cls.calculate_urgency(incident_data)
        incident_data['urgency_score'] = urgency_score
        incident_data['urgency_level'] = urgency_level
        incident_data['urgency_reasons'] = urgency_reasons

        # 2. Duplicate Detection
        dup_result = DuplicateDetectionAgent.evaluate(incident_data, existing_incidents)
        incident_data['is_duplicate'] = 1 if dup_result['is_duplicate'] else 0
        incident_data['parent_incident_id'] = dup_result['parent_id']

        # 3. Specialized Agent Delegations
        police_rec = PoliceCoordinationAgent.analyze(incident_data)
        fire_rec = FireRescueAgent.analyze(incident_data)
        med_rec = MedicalAssistanceAgent.analyze(incident_data)
        res_rec = ResourceManagementAgent.analyze(incident_data, available_resources)
        
        # 4. Simulated Alerts Generation
        simulated_alerts, public_bulletin = CommunicationAgent.generate_alerts(incident_data)

        # 5. Coordinator Synthesis
        coordinator_plan = cls.synthesize_plan(
            incident_data,
            urgency_score,
            urgency_level,
            dup_result,
            police_rec,
            fire_rec,
            med_rec,
            res_rec
        )

        all_recommendations = [
            coordinator_plan,
            police_rec,
            fire_rec,
            med_rec,
            res_rec
        ]

        return {
            'incident': incident_data,
            'urgency_score': urgency_score,
            'urgency_level': urgency_level,
            'urgency_reasons': urgency_reasons,
            'duplicate_analysis': dup_result,
            'recommendations': all_recommendations,
            'simulated_alerts': simulated_alerts,
            'public_bulletin': public_bulletin
        }

    @staticmethod
    def calculate_urgency(incident):
        """
        Calculates a 0-100 score with explicit mathematical factors for explainability.
        """
        score = 20  # Base score
        reasons = []

        is_sos = bool(incident.get('is_sos'))
        em_type = (incident.get('emergency_type') or '').lower()
        trapped = int(incident.get('trapped_count') or 0)
        injured = int(incident.get('injured_count') or 0)
        people = int(incident.get('people_affected') or 0)
        desc = (incident.get('description') or '').lower()

        # SOS Trigger
        if is_sos:
            score += 40
            reasons.append("+40 Instant SOS distress signal triggered by citizen")

        # Threat to life / Trapped
        if trapped > 0:
            trapped_pts = min(30, trapped * 10)
            score += trapped_pts
            reasons.append(f"+{trapped_pts} Direct human entrapment ({trapped} confirmed trapped)")

        # Casualties / Injured
        if injured > 0:
            injured_pts = min(25, injured * 5)
            score += injured_pts
            reasons.append(f"+{injured_pts} Casualties reported ({injured} injured)")

        # Disaster Type Severity
        if 'earthquake' in em_type or 'collapse' in desc:
            score += 15
            reasons.append("+15 High-risk seismic/structural collapse category")
        elif 'flood' in em_type or 'water' in desc:
            score += 12
            reasons.append("+12 Flood inundation hazard & access restriction")
        elif 'fire' in em_type or 'flames' in desc or 'smoke' in desc:
            score += 15
            reasons.append("+15 Thermal fire hazard / rapid spread potential")
        elif 'accident' in em_type:
            score += 10
            reasons.append("+10 High-impact vehicular collision")

        # Population impact
        if people > 50:
            score += 15
            reasons.append(f"+15 Mass population exposure (~{people} people affected)")
        elif people > 10:
            score += 8
            reasons.append(f"+8 Localized crowd exposure (~{people} people affected)")

        # Keywords of acute distress
        for word in ['critical', 'drowning', 'explosion', 'bleeding', 'collapsed', 'roof', 'unconscious']:
            if word in desc:
                score += 5
                reasons.append(f"+5 Acute threat keyword flagged: '{word}'")
                break

        # Cap score between 10 and 100
        score = max(10, min(100, score))

        if score >= 80:
            level = "CRITICAL"
        elif score >= 60:
            level = "HIGH"
        elif score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        return score, level, "; ".join(reasons)

    @staticmethod
    def synthesize_plan(incident, urgency_score, urgency_level, dup_result, police_rec, fire_rec, med_rec, res_rec):
        actions = []
        if dup_result['is_duplicate']:
            actions.append(f"⚠️ Merge with parent Incident #{dup_result['parent_id']}. Verify field report overlap.")
        
        actions.append(f"Authorize immediate alert dispatches for {urgency_level} priority emergency.")
        actions.append(f"Deploy resources: {res_rec['summary']}")
        actions.append("Establish unified command post and maintain radio frequency 154.280 MHz.")

        evidence = (
            f"Synthesized from 4 specialist agents. "
            f"Urgency Score: {urgency_score}/100 ({urgency_level}). "
            f"Duplicate Confidence: {round(dup_result['confidence'] * 100)}%."
        )

        return {
            'agent_name': "Coordinator Agent",
            'priority_level': urgency_level,
            'summary': f"Synthesized Response Plan: Priority {urgency_level} ({urgency_score}/100). Coordinated dispatch ready for Officer approval.",
            'suggested_actions': actions,
            'evidence_refs': evidence,
            'confidence': 0.95
        }

