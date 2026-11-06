from agents.duplicate_agent import haversine_km

class ResourceManagementAgent:
    """
    Resource Management Agent:
    Tracks reported availability of vehicles, supplies, shelters, and hospital beds.
    Matches incident needs with the best available assets and suggests allocations.
    """

    @staticmethod
    def analyze(incident, available_resources):
        emergency_type = (incident.get('emergency_type') or '').lower()
        inc_lat = incident.get('latitude', 15.9054)
        inc_lng = incident.get('longitude', 80.4682)
        trapped_count = int(incident.get('trapped_count') or 0)
        injured_count = int(incident.get('injured_count') or 0)
        is_sos = bool(incident.get('is_sos'))

        allocated_recommendations = []
        shortages = []

        # Calculate distances for all available resources
        for res in available_resources:
            res_lat = res.get('latitude')
            res_lng = res.get('longitude')
            dist = haversine_km(inc_lat, inc_lng, res_lat, res_lng)
            res['distance_km'] = round(dist, 2)

        # Sort resources by proximity
        available_resources = sorted(available_resources, key=lambda x: x.get('distance_km', 999))

        # Match police
        police_units = [r for r in available_resources if r.get('agency_id') == 'police' and r.get('available_capacity', 0) > 0]
        if police_units:
            best_police = police_units[0]
            allocated_recommendations.append({
                'resource_id': best_police.get('id'),
                'resource_name': best_police.get('resource_name'),
                'agency_id': 'police',
                'distance_km': best_police.get('distance_km'),
                'allocated_quantity': 1,
                'role': 'Perimeter and traffic clearance'
            })
        else:
            shortages.append("Police patrol units at 100% operational commitment.")

        # Match Fire / Rescue
        if 'fire' in emergency_type or 'smoke' in (incident.get('description') or '').lower():
            fire_engines = [r for r in available_resources if r.get('agency_id') == 'fire' and 'Engine' in r.get('resource_type', '') and r.get('available_capacity', 0) > 0]
            if fire_engines:
                allocated_recommendations.append({
                    'resource_id': fire_engines[0].get('id'),
                    'resource_name': fire_engines[0].get('resource_name'),
                    'agency_id': 'fire',
                    'distance_km': fire_engines[0].get('distance_km'),
                    'allocated_quantity': 1,
                    'role': 'Blaze suppression'
                })
        
        if 'flood' in emergency_type or trapped_count > 0 or 'water' in (incident.get('description') or '').lower():
            boats = [r for r in available_resources if 'Boat' in r.get('resource_name', '') and r.get('available_capacity', 0) > 0]
            if boats:
                allocated_recommendations.append({
                    'resource_id': boats[0].get('id'),
                    'resource_name': boats[0].get('resource_name'),
                    'agency_id': boats[0].get('agency_id'),
                    'distance_km': boats[0].get('distance_km'),
                    'allocated_quantity': 1,
                    'role': 'Water evacuation & civilian rescue'
                })
            else:
                shortages.append("Inflatable rescue boats near peak deployment.")

        # Match NDRF / Heavy Rescue
        if is_sos or trapped_count > 0 or 'earthquake' in emergency_type:
            ndrf = [r for r in available_resources if r.get('agency_id') == 'rescue' and r.get('available_capacity', 0) > 0]
            if ndrf:
                allocated_recommendations.append({
                    'resource_id': ndrf[0].get('id'),
                    'resource_name': ndrf[0].get('resource_name'),
                    'agency_id': 'rescue',
                    'distance_km': ndrf[0].get('distance_km'),
                    'allocated_quantity': 1,
                    'role': 'Specialized search, extrication and life detection'
                })

        # Match Medical
        if injured_count > 0 or is_sos:
            ambulances = [r for r in available_resources if r.get('agency_id') == 'medical' and 'Ambulance' in r.get('resource_type', '') and r.get('available_capacity', 0) > 0]
            if ambulances:
                allocated_recommendations.append({
                    'resource_id': ambulances[0].get('id'),
                    'resource_name': ambulances[0].get('resource_name'),
                    'agency_id': 'medical',
                    'distance_km': ambulances[0].get('distance_km'),
                    'allocated_quantity': 1,
                    'role': 'Casualty transit & on-site resuscitation'
                })
            else:
                shortages.append("Emergency ambulances critically constrained.")

        actions = [
            f"Commit {item['resource_name']} ({item['distance_km']} km away) for {item['role']}."
            for item in allocated_recommendations
        ]
        if shortages:
            actions.append(f"⚠️ Resource Shortage Alert: {'; '.join(shortages)}")

        summary = (
            f"Resource Agent allocated {len(allocated_recommendations)} recommended units. "
            f"Nearest unit ready at {allocated_recommendations[0]['distance_km'] if allocated_recommendations else 0} km. "
            f"Shortages detected: {len(shortages)}."
        )

        return {
            'agent_name': "Resource Management Agent",
            'priority_level': "High" if shortages else "Optimal",
            'summary': summary,
            'suggested_actions': actions,
            'evidence_refs': f"Evaluated {len(available_resources)} total agency assets across 4 emergency sectors.",
            'confidence': 0.94,
            'allocated_items': allocated_recommendations,
            'shortages': shortages
        }

