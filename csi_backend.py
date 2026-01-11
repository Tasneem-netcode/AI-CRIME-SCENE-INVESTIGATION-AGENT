
import os
import json
import uuid
from typing import List, Dict, Any
from pathlib import Path
from fpdf import FPDF
import pandas as pd
import sqlite3
import google.generativeai as genai
import textwrap
import time

# --- Configuration & Setup ---
APP_NAME = "CSI_APP"
DB_FILE = "csi_app.db"

# Ensure output directory exists
OUT_DIR = Path("csi_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Database / Persistence Layer (Replaces DatabaseSessionService) ---
class CaseManager:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sessions
                     (session_id TEXT PRIMARY KEY, state TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def save_session(self, session_id: str, state: dict):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO sessions (session_id, state) VALUES (?, ?)",
                  (session_id, json.dumps(state)))
        conn.commit()
        conn.close()

    def get_session(self, session_id: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT state FROM sessions WHERE session_id = ?", (session_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None

    def delete_session(self, session_id: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    def list_sessions(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT session_id, state, updated_at FROM sessions ORDER BY updated_at DESC")
        rows = c.fetchall()
        conn.close()
        sessions = []
        for r in rows:
            try:
                state = json.loads(r[1])
            except:
                state = {}
            sessions.append({
                "session_id": r[0],
                "state": state,
                "updated_at": r[2]
            })
        return sessions

# Global instance
case_manager = CaseManager()

# --- Helper Functions ---
def save_json(obj, filename):
    path = OUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    return str(path)

def write_markdown(text, filename="case_report.md"):
    path = OUT_DIR / filename
    path.write_text(text, encoding="utf-8")
    return str(path)

def markdown_to_pdf(md_text, filename="case_report.pdf"):
    filename = filename.strip().replace("\n", "").replace("\r", "")
    safe_text = (
        md_text.replace("—", "-")
               .replace("–", "-")
               .replace("’", "'")
               .replace("“", '"')
               .replace("”", '"')
    )
    safe_text = safe_text.encode("latin-1", "ignore").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in safe_text.splitlines():
        pdf.multi_cell(0, 6, line)

    out_path = OUT_DIR / filename
    pdf.output(str(out_path))
    return str(out_path)

# --- Vision Stubs ---
CRIME_KEYWORDS = {
    "knife": "a sharp knife",
    "gun": "a firearm or gun",
    "pistol": "a pistol",
    "blood": "blood stains or pooling",
    "stain": "blood stains",
    "pool": "a pool of blood",
    "footprint": "a visible footprint",
    "shoeprint": "a shoeprint impression",
    "fingerprint": "a visible fingerprint",
    "wallet": "a dropped wallet",
    "phone": "a mobile phone",
    "glass": "broken glass pieces",
    "bottle": "a bottle that may contain prints",
    "rope": "a rope possibly used in struggle",
    "body": "a human body or figure",
    "victim": "a potential victim lying",
    "mask": "a mask possibly used by suspect",
    "glove": "a glove indicating suspect presence",
    "bullet": "bullet casings",
    "casing": "a bullet casing"
}

def image_caption_stub(image_path: str) -> str:
    name = Path(image_path).stem.lower()
    tokens = name.replace("_", " ").replace("-", " ").split()
    found = []
    for t in tokens:
        if t in CRIME_KEYWORDS:
            found.append(CRIME_KEYWORDS[t])
    if found:
        return "Photo appears to show " + ", ".join(found) + "."
    else:
        return "Crime scene photo; no clear objects detected by stub."

# --- Core Forensic Tools (Deterministic Logic) ---

def make_description(scene_text: str, image_captions: List[str] | None = None) -> dict:
    text = scene_text.lower()
    desc = scene_text.strip().replace("\n", " ")
    objects = []
    forensic_clues = []
    
    keywords = {
        "blood": "blood_stain", "stain": "blood_stain", "knife": "knife", 
        "gun": "gun", "shell": "shell_casing", "footprint": "footprint",
        "window": "window", "broken glass": "broken_glass", "chair": "chair",
        "table": "table", "door": "door"
    }

    for word, label in keywords.items():
        if word in text:
            objects.append(label)
    
    if image_captions:
        for cap in image_captions:
            cap = cap.lower()
            for word, label in keywords.items():
                if word in cap:
                    objects.append(label)

    objects = list(dict.fromkeys(objects))

    if any(w in text for w in ["kitchen", "sink", "pan", "tile"]):
        scene_context = ["indoor", "kitchen"]
    elif any(w in text for w in ["bed", "pillow", "wardrobe"]):
        scene_context = ["indoor", "bedroom"]
    elif any(w in text for w in ["street", "alley", "road"]):
        scene_context = ["outdoor", "public"]
    else:
        scene_context = ["unknown"]

    if "blood spatter" in text or "spatter" in text:
        forensic_clues.append("high-velocity blood spatter (possible weapon impact)")
    if "pool of blood" in text:
        forensic_clues.append("pooled blood (injury occurred at location)")
    if "trail of blood" in text:
        forensic_clues.append("movement after injury")
    if "broken window" in text or "broken_glass" in objects:
        forensic_clues.append("forced entry or exit")
    if "footprint" in objects:
        forensic_clues.append("footprints suggest movement or arrival path")
    if "chair overturned" in text:
        forensic_clues.append("signs of struggle")

    return {
        "description": desc[:800],
        "objects": objects,
        "scene_context": scene_context,
        "forensic_clues": forensic_clues
    }

def extract_evidence(scene_description: dict) -> dict:
    evidence_items = []
    base_id = uuid.uuid4().hex[:8]
    idx = 1
    objs = scene_description.get("objects", [])
    clues = scene_description.get("forensic_clues", [])

    for obj in objs:
        evidence_items.append({
            "id": f"EV-{base_id}-{idx}",
            "type": obj,
            "location_text": "derived from scene text",
            "description": f"Detected {obj} based on description or image.",
            "confidence": 0.75
        })
        idx += 1

    for clue in clues:
        evidence_items.append({
            "id": f"EV-{base_id}-{idx}",
            "type": "forensic_clue",
            "location_text": "contextual",
            "description": clue,
            "confidence": 0.85
        })
        idx += 1

    if not evidence_items:
        evidence_items.append({
            "id": f"EV-{base_id}-1",
            "type": "scene_note",
            "location_text": "unspecified",
            "description": scene_description.get("description", "")[:300],
            "confidence": 0.6
        })

    return {"evidence_items": evidence_items}

def calculate_confidence(evidence_items: List[dict]) -> float:
    score = 0.0
    strong_types = ["knife", "gun", "shell_casing", "blood_stain", "blood_pool"]
    medium_types = ["footprint", "shoeprint", "broken_glass"]
    
    for ev in evidence_items:
        ev_type = ev.get("type", "")
        if ev_type in strong_types: score += 0.20
        elif ev_type in medium_types: score += 0.10
    
    if len(evidence_items) >= 3: score += 0.15
    if len(evidence_items) >= 5: score += 0.10
    if len(evidence_items) == 0: score = 0.10
    
    return round(min(max(score, 0.15), 0.98), 2)

def analyze_weapon_and_injury(evidence_items: List[dict]) -> dict:
    weapons = []
    injuries = []
    scene_conf = calculate_confidence(evidence_items)
    
    has_knife = any("knife" in ev["type"] for ev in evidence_items)
    has_gun = any("shell" in ev["type"] or "firearm" in ev["type"] for ev in evidence_items)
    has_blood = any("blood" in ev["type"] for ev in evidence_items)

    if has_knife:
        weapons.append({"weapon": "knife", "confidence": round(min(scene_conf + 0.10, 0.97), 2), 
                        "force_required": "medium", "engagement_distance": "close-range", "reason": "Knife evidence directly detected."})
    if has_gun:
        weapons.append({"weapon": "firearm", "confidence": round(min(scene_conf + 0.10, 0.97), 2), 
                        "force_required": "high", "engagement_distance": "short–medium range", "reason": "Shell casing or firearm markers detected."})
    if not weapons:
        weapons.append({"weapon": "unknown object", "confidence": round(scene_conf, 2), 
                        "force_required": "unknown", "engagement_distance": "unknown", "reason": "No direct weapon evidence — inferred only."})

    if has_blood:
        injuries.append({"injury": "significant bleeding", "confidence": round(min(scene_conf + 0.05, 0.95), 2), 
                         "lethality_probability": "medium–high", "reason": "Blood evidence strongly supports injury."})
    else:
        injuries.append({"injury": "unknown injury", "confidence": round(scene_conf - 0.10, 2), 
                         "lethality_probability": "unknown", "reason": "No strong blood evidence detected."})

    return {"weapons": weapons, "injuries": injuries}

def generate_suspect_profiles(all_inputs: dict) -> dict:
    scene = all_inputs.get("description", {}).get("description", "").lower()
    evidence = all_inputs.get("evidence_items", [])
    profiles = []
    
    has_knife = any("knife" in ev.get("type","") for ev in evidence)
    has_footprints = any("footprint" in ev.get("type","") for ev in evidence)
    heavy_blood = sum(1 for ev in evidence if "blood" in ev.get("type","")) >= 2
    
    profiles.append({
        "id": "SP-" + uuid.uuid4().hex[:6],
        "gender_probability": {"male": 0.55, "female": 0.35, "unknown": 0.10},
        "age_range": "25–40", "build": "medium", "height_estimate_cm": "165–180",
        "shoe_size_estimate": "8–10 US" if has_footprints else "unknown",
        "dominant_hand": "right" if has_knife else "unknown",
        "experience_level": "low–moderate",
        "likely_intent": "assault" if has_knife else "unknown",
        "possible_emotional_state": "agitated / impulsive",
        "confidence": 0.45,
        "reason": "Based on knife evidence, probable right-hand usage, medium build typical for single aggressor."
    })
    profiles.append({
        "id": "SP-" + uuid.uuid4().hex[:6],
        "gender_probability": {"male": 0.40, "female": 0.50, "unknown": 0.10},
        "age_range": "18–28", "build": "slim", "height_estimate_cm": "155–170",
        "shoe_size_estimate": "6–8 US" if has_footprints else "unknown",
        "dominant_hand": "left" if "left" in scene else "unknown",
        "experience_level": "low",
        "likely_intent": "robbery / conflict",
        "possible_emotional_state": "panic / stress",
        "confidence": 0.28,
        "reason": "Lighter build hypothesis due to limited physical disturbance at the scene."
    })
    
    return {"suspect_hypotheses": profiles}

def reconstruct_timeline(evidence_items: List[dict]) -> dict:
    timeline = []
    step = 1
    has_entry = False
    has_weapon = False
    has_blood = False
    has_footprints = False
    has_shell = False
    
    for ev in evidence_items:
        t = ev.get("type", "").lower()
        d = ev.get("description", "").lower()
        if "footprint" in t or "shoeprint" in t: has_footprints = True
        if "broken_glass" in t or "window" in d: has_entry = True
        if "knife" in t or "gun" in t: has_weapon = True
        if "shell" in t or "casing" in t: has_shell = True
        if "blood" in t: has_blood = True
        
    if has_entry or has_footprints:
        timeline.append({"step": step, "event": "Suspect arrived at the scene", "reason": "Movement or entry indicators detected"})
        step += 1
    if has_weapon or has_shell:
        timeline.append({"step": step, "event": "Weapon discharged or used", "reason": "Ballistic or weapon evidence present"})
        step += 1
    if has_blood:
        timeline.append({"step": step, "event": "Victim sustained injuries", "reason": "Blood evidence confirms impact"})
        step += 1
    if has_footprints:
        timeline.append({"step": step, "event": "Suspect fled the scene", "reason": "Footwear patterns indicate exit path"})
        step += 1
    if not timeline:
        timeline.append({"step": 1, "event": "Scene documented", "reason": "Insufficient evidence to reconstruct events"})

    return {"timeline": timeline}

def write_case_report(aggregate: dict) -> str:
    lines = []
    lines.append("# CSI Case Report\n")
    lines.append("## Executive Summary\n")
    lines.append(aggregate.get("executive_summary","(summary not provided)") + "\n")
    lines.append("## Scene Description\n")
    lines.append(aggregate.get("description", {}).get("description", "") + "\n")
    lines.append("## Evidence Table\n")
    lines.append("| ID | Type | Location | Description | Confidence |\n")
    lines.append("|---|---|---|---|---|\n")
    for ev in aggregate.get("evidence_items", []):
        lines.append(f"| {ev['id']} | {ev['type']} | {ev['location_text']} | {ev['description']} | {ev.get('confidence', '')} |\n")
    lines.append("\n## Timeline\n")
    for t in aggregate.get("timeline", []):
        lines.append(f"- Step {t['step']}: {t['event']} — Evidence {t.get('evidence_id','-')} — {t.get('reason','')}\n")
    lines.append("\n## Suspect Hypotheses\n")
    for s in aggregate.get("suspect_hypotheses", []):
        lines.append(f"- {s['id']}: age {s['age_range']}, build {s['build']}, confidence {s['confidence']}. Reason: {s['reason']}\n")
    return "\n".join(lines)

# --- Orchestrator ---

def run_full_investigation(scene_text: str, image_paths=None, case_id=None, api_key=None):
    if case_id is None:
        case_id = f"CASE-{uuid.uuid4().hex[:8]}"
    if image_paths is None:
        image_paths = []

    # 1. Description
    captions = [image_caption_stub(p) for p in image_paths]
    description = make_description(scene_text, image_captions=captions)

    # 2. Evidence
    evidence = extract_evidence(description)
    evidence_items = evidence.get("evidence_items", [])

    # 3. Weapon
    weapon_result = analyze_weapon_and_injury(evidence_items)

    # 4. Profiling
    profile_result = generate_suspect_profiles({
        "description": description,
        "evidence_items": evidence_items,
        "weapons": weapon_result.get("weapons", [])
    })

    # 5. Timeline
    timeline_result = reconstruct_timeline(evidence_items)

    # 6. Aggregate
    aggregate = {
        "case_id": case_id,
        "description": description,
        "evidence_items": evidence_items,
        "weapons": weapon_result.get("weapons", []),
        "injuries": weapon_result.get("injuries", []),
        "suspect_hypotheses": profile_result.get("suspect_hypotheses", []),
        "timeline": timeline_result.get("timeline", [])
    }

    # 7. Executive Summary (Gemini)
    summary_text = "(Gemini API Key missing - analysis skipped)"
    if api_key:
        genai.configure(api_key=api_key)
        
        # Helper to find a working model
        def get_available_model():
            try:
                # Prioritize these models in order
                candidates = [
                    "gemini-1.5-flash",
                    "gemini-1.5-pro",
                    "gemini-2.0-flash-exp",
                    "gemini-2.0-flash",
                    "gemini-pro"
                ]
                available_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # Check for matches
                for cand in candidates:
                    if cand in available_models:
                        return cand
                
                # Fallback to first available if no candidates match
                if available_models:
                    return available_models[0]
            except:
                pass
            return "gemini-1.5-flash" # Default fallback
            
        model_name = get_available_model()
        model = genai.GenerativeModel(model_name)

        prompt = f"""
        You are a senior forensic crime analyst.
        Write a sharp, professional forensic executive summary based on the following case data.

        Rules:
        - Use formal crime analysis language
        - Emphasize cause-effect logic
        - Avoid emotional or casual tone
        - Do NOT invent facts not present in the data
        - 4–6 strong sentences maximum

        Data:
        {json.dumps(aggregate, indent=2)}
        """
        
        # Retry logic for 429 (Quota) or 404 (Not Found)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                if response.text:
                    summary_text = response.text.strip()
                    break
            except Exception as e:
                err_msg = str(e)
                if ("429" in err_msg or "404" in err_msg) and attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                elif "429" in err_msg:
                    summary_text = "(Summary unavailable: API Quota Exceeded. Please try again later.)"
                elif "404" in err_msg:
                     summary_text = f"(Summary unavailable: Model {model_name} not found.)"
                else:
                    summary_text = f"(Error generating summary: {err_msg})"
                pass
    
    aggregate["executive_summary"] = summary_text

    # 8. Risk Score
    score = 0
    if aggregate["weapons"] and aggregate["weapons"][0]["confidence"] > 0.85: score += 2
    if aggregate["injuries"] and aggregate["injuries"][0]["confidence"] > 0.85: score += 2
    if len(evidence_items) > 3: score += 1
    if calculate_confidence(evidence_items) > 0.80: score += 1
    aggregate["risk_score"] = score

    # 9. Save to DB
    case_manager.save_session(case_id, {
        "case:aggregate": aggregate,
        "case:risk_score": aggregate["risk_score"],
        "case:summary": aggregate["executive_summary"]
    })

    # 10. Memory Save (Simplified logic)
    # We just store the condensed memory into another table or just rely on the session state
    # For compatibility with 'ask_memory', we'll store a mock memory state in the same session or separate?
    # The original used a separate Memory key structure. We'll simulate it in the same state object.
    memory_state = {
        "mem:primary_weapon": aggregate.get("weapons", [{}])[0].get("weapon", "unknown"),
        "mem:injury": aggregate.get("injuries", [{}])[0].get("injury", "unknown"),
        "mem:evidence_list": [e.get("type") for e in aggregate.get("evidence_items", [])],
        "mem:risk_score": aggregate.get("risk_score", 0),
        "mem:summary": aggregate.get("executive_summary", "")
    }
    # Update state with memory
    current_state = case_manager.get_session(case_id)
    current_state.update(memory_state)
    case_manager.save_session(case_id, current_state)

    # 11. Files
    json_path = save_json(aggregate, f"{case_id}.json")
    md_text = write_case_report(aggregate)
    md_path = write_markdown(md_text, f"{case_id}.md")
    pdf_path = markdown_to_pdf(md_text, f"{case_id}.pdf")

    return {
        "case_id": case_id,
        "aggregate": aggregate,
        "json_path": json_path,
        "md_path": md_path,
        "pdf_path": pdf_path
    }

def ask_memory_helper(question: str, case_id: str):
    state = case_manager.get_session(case_id)
    if not state: 
        return "Case not found."
    
    q = question.lower()
    if "weapon" in q: return state.get("mem:primary_weapon", "unknown")
    if "injury" in q: return state.get("mem:injury", "unknown")
    if "where" in q or "location" in q: return state.get("mem:summary", "")
    if "risk" in q: return state.get("mem:risk_score", None)
    if "evidence" in q: return state.get("mem:evidence_list", [])
    
    return state.get("mem:summary", "No memory summary found.")

def list_all_cases_df():
    sessions = case_manager.list_sessions()
    rows = []
    for s in sessions:
        state = s["state"]
        rows.append({
            "case_id": s["session_id"],
            "mem_primary_weapon": state.get("mem:primary_weapon"),
            "mem_injury": state.get("mem:injury"),
            "num_evidence": len(state.get("mem:evidence_list", [])),
            "risk_score": state.get("mem:risk_score"),
            "has_summary": bool(state.get("mem:summary")),
            "updated_at": s["updated_at"]
        })
    return pd.DataFrame(rows)
