"""
LOSTLINK - Smart Matching Algorithm
Computes multi-parameter similarity between Lost and Found reports.
Provides college evaluators a clear, algorithmic demonstration of Smart Lost & Found Matching.
"""

import re
from datetime import datetime
from db import get_db, to_object_id, serialize_doc, serialize_docs

def _tokenize(text):
    """Convert text into normalized set of non-trivial words."""
    if not text:
        return set()
    stopwords = {"a", "an", "the", "in", "on", "at", "for", "with", "of", "and", "or", "is", "it", "my", "lost", "found"}
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    return {w for w in words if len(w) > 1 and w not in stopwords}

def _calculate_jaccard_similarity(set_a, set_b):
    """Jaccard similarity coefficient between two word sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def _calculate_date_score(date_lost_str, date_found_str):
    """
    Score date compatibility:
    Items found around or slightly after the lost date get highest score.
    """
    try:
        # Expected format: YYYY-MM-DD
        d1 = datetime.strptime(str(date_lost_str)[:10], "%Y-%m-%d")
        d2 = datetime.strptime(str(date_found_str)[:10], "%Y-%m-%d")
        
        diff_days = (d2 - d1).days
        # If found between 0 and 30 days after lost: 10/10
        if 0 <= diff_days <= 14:
            return 10.0, f"Found within {diff_days} days of loss"
        elif 15 <= diff_days <= 45:
            return 7.0, f"Found {diff_days} days after loss"
        elif diff_days < 0 and diff_days >= -3:
            # Possible date estimate discrepancy
            return 6.0, "Date roughly coincides (estimate window)"
        else:
            return 2.0, "Date gap exceeds typical recovery window"
    except Exception:
        return 5.0, "Date proximity inconclusive"

def calculate_match_score(lost_item, found_item):
    """
    Computes weighted score between 0 and 100 for a pair of Lost and Found items.
    Components:
    1. Category Match (35 points): Exact category match = 35, related = 15, mismatch = 0
    2. Text & Keyword Similarity (35 points): Title, brand, color, description
    3. Location Similarity (20 points): Location strings & campus landmarks
    4. Date Compatibility (10 points): Temporal proximity
    """
    reasons = []
    total_score = 0.0
    
    # 1. Category Matching (Max 35 pts)
    cat_lost = lost_item.get("category", "").lower().strip()
    cat_found = found_item.get("category", "").lower().strip()
    if cat_lost and cat_found and cat_lost == cat_found:
        total_score += 35.0
        reasons.append("Exact category match")
    else:
        # Penalty if categories conflict
        reasons.append("Category does not match")
        # If categories differ completely, cap match potential
        return 0, "No Match", reasons

    # 2. Text / Title & Description Similarity (Max 35 pts)
    # Combine title, brand, color, description
    text_lost = f"{lost_item.get('title', '')} {lost_item.get('brand', '')} {lost_item.get('color', '')} {lost_item.get('description', '')}"
    text_found = f"{found_item.get('title', '')} {found_item.get('brand', '')} {found_item.get('color', '')} {found_item.get('description', '')}"
    
    tokens_lost = _tokenize(text_lost)
    tokens_found = _tokenize(text_found)
    
    text_sim = _calculate_jaccard_similarity(tokens_lost, tokens_found)
    
    # Check title / brand exact word overlaps (bonus emphasis)
    title_lost_words = _tokenize(lost_item.get('title', ''))
    title_found_words = _tokenize(found_item.get('title', ''))
    title_overlap = len(title_lost_words.intersection(title_found_words))
    
    # Check brand / color exact matches
    brand_lost = lost_item.get("brand", "").lower().strip()
    brand_found = found_item.get("brand", "").lower().strip()
    color_lost = lost_item.get("color", "").lower().strip()
    color_found = found_item.get("color", "").lower().strip()
    
    text_points = text_sim * 25.0
    if brand_lost and brand_found and (brand_lost in brand_found or brand_found in brand_lost):
        text_points += 5.0
        reasons.append(f"Matching brand: {brand_lost.title()}")
    if color_lost and color_found and (color_lost in color_found or color_found in color_lost):
        text_points += 5.0
        reasons.append(f"Matching color: {color_lost.title()}")
    elif title_overlap >= 1:
        text_points += 5.0
        reasons.append("Matching title keywords")
        
    text_points = min(35.0, text_points)
    total_score += text_points

    # 3. Location Similarity (Max 20 pts)
    loc_lost = lost_item.get("location", "").lower().strip()
    loc_found = found_item.get("location", "").lower().strip()
    
    loc_tokens_lost = _tokenize(loc_lost)
    loc_tokens_found = _tokenize(loc_found)
    loc_sim = _calculate_jaccard_similarity(loc_tokens_lost, loc_tokens_found)
    
    if loc_lost and loc_found and (loc_lost in loc_found or loc_found in loc_lost or loc_sim > 0.3):
        loc_score = 20.0
        reasons.append(f"High location overlap ({loc_lost})")
    elif loc_sim > 0:
        loc_score = min(20.0, loc_sim * 25.0)
        reasons.append("Nearby or common landmark")
    else:
        loc_score = 5.0  # Items can be moved or found nearby
    total_score += loc_score

    # 4. Date Proximity (Max 10 pts)
    d_lost = lost_item.get("date_lost", lost_item.get("date", ""))
    d_found = found_item.get("date_found", found_item.get("date", ""))
    date_score, date_reason = _calculate_date_score(d_lost, d_found)
    total_score += date_score
    reasons.append(date_reason)

    final_score = int(min(100.0, round(total_score)))
    
    if final_score >= 75:
        confidence = "High Match"
    elif final_score >= 50:
        confidence = "Moderate Match"
    else:
        confidence = "Possible Lead"
        
    return final_score, confidence, reasons

def find_matches_for_item(item_id, limit=6, min_score=35):
    """
    Given an item ID, finds counterpart items and computes ranked match scores.
    If item is 'Lost', searches against 'Found' items.
    If item is 'Found', searches against 'Lost' items.
    """
    db = get_db()
    source_item = db.items.find_one({"_id": to_object_id(item_id)})
    if not source_item:
        return []

    item_type = source_item.get("type", "").lower()
    target_type = "found" if item_type == "lost" else "lost"
    
    # Query counterpart items of the same category (or all if category empty)
    filter_query = {
        "type": target_type,
        "status": {"$nin": ["Recovered", "Returned to Owner", "Archived", "Closed"]}
    }
    if source_item.get("category"):
        filter_query["category"] = source_item["category"]
        
    candidates = list(db.items.find(filter_query))
    
    # If not enough category matches, also search cross-category
    if len(candidates) < 3:
        broad_candidates = list(db.items.find({
            "type": target_type,
            "status": {"$nin": ["Recovered", "Returned to Owner", "Archived", "Closed"]}
        }).limit(20))
        # Merge avoiding duplicates
        existing_ids = {str(c["_id"]) for c in candidates}
        for bc in broad_candidates:
            if str(bc["_id"]) not in existing_ids:
                candidates.append(bc)

    scored_matches = []
    for cand in candidates:
        if item_type == "lost":
            score, confidence, reasons = calculate_match_score(source_item, cand)
        else:
            score, confidence, reasons = calculate_match_score(cand, source_item)
            
        if score >= min_score:
            cand_serialized = serialize_doc(cand)
            cand_serialized["match_score"] = score
            cand_serialized["match_confidence"] = confidence
            cand_serialized["match_reasons"] = reasons
            scored_matches.append(cand_serialized)
            
    # Sort descending by match score
    scored_matches.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_matches[:limit]

def get_smart_alerts_for_user(user_id, limit=5):
    """
    Scans all open items reported by this user and finds high-confidence match alerts.
    """
    db = get_db()
    user_items = list(db.items.find({
        "reporter_id": str(user_id),
        "status": {"$nin": ["Recovered", "Returned to Owner", "Closed"]}
    }))
    
    alerts = []
    for u_item in user_items:
        matches = find_matches_for_item(u_item["_id"], limit=2, min_score=50)
        for m in matches:
            alerts.append({
                "my_item": serialize_doc(u_item),
                "matched_item": m,
                "score": m["match_score"],
                "confidence": m["match_confidence"],
                "reasons": m["match_reasons"]
            })
            
    alerts.sort(key=lambda x: x["score"], reverse=True)
    return alerts[:limit]
