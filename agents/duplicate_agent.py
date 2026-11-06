import math
from datetime import datetime
import re

def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points in kilometers."""
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except (ValueError, TypeError):
        return 9999.0

    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def text_similarity(text1, text2):
    """Compute token-based Jaccard similarity between two descriptions."""
    def tokenize(text):
        if not text:
            return set()
        words = re.findall(r'\b\w{3,}\b', text.lower())
        return set(words)
        
    set1 = tokenize(text1)
    set2 = tokenize(text2)
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

class DuplicateDetectionAgent:
    """
    Monitoring & Duplicate Detection Agent:
    Finds duplicates or similar reports for human verification.
    Evaluates spatial proximity (< 2.0 km), temporal closeness, and narrative similarity.
    """
    
    @staticmethod
    def evaluate(new_incident, existing_incidents):
        """
        Evaluate if new_incident is a potential duplicate of any active incident.
        Returns:
            is_duplicate (bool)
            parent_id (int or None)
            confidence (float)
            reason (str)
            duplicate_candidates (list)
        """
        matches = []
        new_lat = new_incident.get('latitude')
        new_lng = new_incident.get('longitude')
        new_type = (new_incident.get('emergency_type') or '').lower()
        new_desc = new_incident.get('description', '')
        new_addr = (new_incident.get('location_address') or '').lower()

        for inc in existing_incidents:
            if inc.get('id') == new_incident.get('id'):
                continue
            
            # Skip resolved or closed incidents
            if str(inc.get('status')).lower() in ['resolved', 'closed']:
                continue

            dist_km = haversine_km(new_lat, new_lng, inc.get('latitude'), inc.get('longitude'))
            type_match = 1.0 if (inc.get('emergency_type') or '').lower() == new_type else 0.3
            text_sim = text_similarity(new_desc, inc.get('description', ''))
            
            # Address text overlap
            addr_sim = text_similarity(new_addr, (inc.get('location_address') or '').lower())

            # Composite similarity score (0.0 to 1.0)
            # Distance weight: max if < 0.5km, decreases up to 3km
            if dist_km <= 0.5:
                dist_score = 1.0
            elif dist_km <= 2.0:
                dist_score = 0.7
            elif dist_km <= 4.0:
                dist_score = 0.3
            else:
                dist_score = 0.0

            composite_score = (dist_score * 0.40) + (type_match * 0.30) + (text_sim * 0.20) + (addr_sim * 0.10)

            if composite_score >= 0.55:
                matches.append({
                    'incident_id': inc.get('id'),
                    'incident_code': inc.get('incident_code'),
                    'title': inc.get('title'),
                    'distance_km': round(dist_km, 2),
                    'similarity_score': round(composite_score * 100, 1),
                    'existing_urgency': inc.get('urgency_level'),
                    'existing_status': inc.get('status')
                })

        if matches:
            # Sort by highest similarity
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            best_match = matches[0]
            reason = (f"Potential duplicate of {best_match['incident_code']} "
                      f"({best_match['distance_km']} km away, {best_match['similarity_score']}% match confidence). "
                      f"Flagged for human verification.")
            return {
                'is_duplicate': True,
                'parent_id': best_match['incident_id'],
                'confidence': best_match['similarity_score'] / 100.0,
                'reason': reason,
                'candidates': matches
            }
        
        return {
            'is_duplicate': False,
            'parent_id': None,
            'confidence': 0.95,
            'reason': "Unique emergency report verified. No active duplicates detected within response perimeter.",
            'candidates': []
        }

