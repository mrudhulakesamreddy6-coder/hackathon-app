class FireRescueAgent:
    """
    Fire & Rescue Agent:
    Summarizes rescue-related requests, access constraints, containment,
    and equipment requirements (boats, ladders, hydraulic tools).
    """

    @staticmethod
    def analyze(incident):
        emergency_type = (incident.get('emergency_type') or '').lower()
        people_affected = int(incident.get('people_affected') or 0)
        trapped_count = int(incident.get('trapped_count') or 0)
        is_sos = bool(incident.get('is_sos'))
        desc = (incident.get('description') or '').lower()

        actions = []
        priority = "Normal"
        confidence = 0.92
        evidence = f"Incident Type: {incident.get('emergency_type')}, Trapped Citizens: {trapped_count}, Affected: {people_affected}."

        if trapped_count > 0 or is_sos or 'trapped' in desc or 'roof' in desc:
            priority = "CRITICAL RESCUE"
            actions.append(f"Deploy specialized Search & Rescue squad immediately targeting {trapped_count or 'unconfirmed'} trapped individuals.")
        
        if 'flood' in emergency_type or 'water' in desc or 'rising' in desc:
            priority = "HIGH" if priority != "CRITICAL RESCUE" else priority
            actions.append("Mobilize motorized inflatable rescue boats (IRBs) and life jackets for water rescue.")
            actions.append("Conduct high-ground rooftop extractions for stranded residents.")
            actions.append("Assess flood water velocity and identify underwater powerline / hazard zones.")
            evidence += " Rapid water accumulation / flood inundation constraints."
        elif 'fire' in emergency_type or 'smoke' in desc or 'flames' in desc:
            priority = "CRITICAL RESCUE" if trapped_count > 0 else "HIGH"
            actions.append("Dispatch Heavy Water Tenders and Foam Extinguishers for active blaze containment.")
            actions.append("Position hydraulic aerial ladder platforms for upper-floor rescues.")
            actions.append("Check for hazardous materials, LPG cylinders, and toxic smoke spread.")
            evidence += " Thermal radiant heat, active flames, and smoke inhalation threat."
        elif 'earthquake' in emergency_type or 'collapse' in desc or 'debris' in desc:
            priority = "CRITICAL RESCUE"
            actions.append("Mobilize Urban Search and Rescue (USAR) team equipped with acoustic listening devices and thermal search cameras.")
            actions.append("Deploy hydraulic concrete spreaders and diamond-tipped cutters for rubble breaching.")
            actions.append("Monitor structure for secondary collapse before entering debris voids.")
            evidence += " Structural failure and heavy debris entrapment."
        elif 'accident' in emergency_type:
            actions.append("Deploy Heavy Rescue Tender with hydraulic cutters ('Jaws of Life') to extricate pinned vehicle occupants.")
            actions.append("Apply dry chemical extinguishing powder to control fuel spill ignition risks.")
            evidence += " Pinned vehicular entrapment and flammable fuel residue."
        else:
            actions.append("Deploy rapid assessment reconnaissance squad to survey incident perimeter.")

        summary = (
            f"Fire & Rescue Agent recommends {priority} response. Immediate equipment: "
            f"{'Inflatable Boats' if 'flood' in emergency_type else 'Hydraulic Cutters/Tenders' if 'accident' in emergency_type or 'fire' in emergency_type else 'USAR Heavy Tools'}."
        )

        return {
            'agent_name': "Fire & Rescue Agent",
            'priority_level': priority,
            'summary': summary,
            'suggested_actions': actions,
            'evidence_refs': evidence,
            'confidence': confidence
        }

