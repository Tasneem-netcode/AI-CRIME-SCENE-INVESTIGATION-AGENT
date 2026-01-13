
import os
import json
import uuid
import base64
import requests
import random
import sqlite3
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from fpdf import FPDF
import google.generativeai as genai
import textwrap
import time

from dotenv import load_dotenv

load_dotenv()

# --- Configuration & Setup ---
APP_NAME = "CSI_APP"
DB_FILE = "csi_app.db"
# User provided key for OpenRouter / Gemini 2.0 Flash
# User provided key for OpenRouter / Gemini 2.0 Flash
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = "google/gemini-2.0-flash-exp:free"

# Ensure output directory exists
OUT_DIR = Path("csi_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Database / Persistence Layer ---
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
    # Simple fix for utf-8 chars in FPDF
    safe_text = safe_text.encode("latin-1", "ignore").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, safe_text)
    
    out_path = OUT_DIR / filename
    try:
        pdf.output(str(out_path))
    except:
        pass 
    return str(out_path)

def get_random_coordinates():
    # Simulate crime locations (Fictional city spread)
    lat = 40.7128 + (random.uniform(-0.05, 0.05))
    lon = -74.0060 + (random.uniform(-0.05, 0.05))
    return lat, lon

# --- OpenRouter / Gemini Integration ---

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# --- OpenRouter integration (Strict) ---

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image_openrouter(image_path):
    """Real Computer Vision using Gemini 2.0 Flash via OpenRouter"""
    try:
        base64_image = encode_image(image_path)
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8501",
            "X-Title": APP_NAME
        }
        
        # User requested specific model
        model = "google/gemini-2.0-flash-exp:free"
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this forensic image. Identify objects, signs of struggle, weapons, or forensic clues. Be concise but detailed."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }
        
        try:
            # 60 timeout for vision
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                else:
                    return f"[Analysis Empty: {json.dumps(data)}]"
            else:
                return f"[Analysis Failed: {response.status_code} - {response.text}]"

        except Exception as e:
            return f"[Connection Error: {str(e)}]"
            
    except Exception as e:
        return f"[System Error: {str(e)}]"

def call_openrouter_text(prompt):
    """Text generation using Gemini 2.0 Flash via OpenRouter"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8501", 
            "X-Title": APP_NAME
        }
        
        model = "google/gemini-2.0-flash-exp:free"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
            
            return f"(Analysis Failed: {response.status_code} - {response.text})"
            
        except Exception as e:
            return f"(Connection Error: {str(e)})"

    except Exception as e:
        return f"(System Error: {str(e)})"

def generate_victim_profile(description, evidence):
    """Generate Victimology Profile based on scene data"""
    prompt = f"""
    Based on the forensic data below, generate a 'Victim Profile'.
    Infer likely characteristics and risk level.
    
    Description: {description}
    Evidence: {evidence}
    
    Return valid JSON only in this format:
    {{
        "risk_level": "High/Medium/Low",
        "demographics_inferred": "string",
        "relation_to_suspect_hypothesis": "string",
        "notes": "string"
    }}
    """
    res = call_openrouter_text(prompt)
    if res:
        try:
            # clean json wrapper
            res = res.replace("```json", "").replace("```", "").strip()
            return json.loads(res)
        except:
            pass
    
    return {
        "risk_level": "Unknown", 
        "demographics_inferred": "Unknown", 
        "relation_to_suspect_hypothesis": "Undetermined", 
        "notes": "Insufficient data."
    }

# --- Core Forensics Logic ---

def extract_evidence_llm(description_text: str) -> dict:
    """Uses Gemini 2.0 Flash to extract structured evidence from text."""
    prompt = f"""
    Analyze this forensic log and visual description. Extract ALL potential evidence items, clues, and context.
    
    Input:
    {description_text}
    
    Return a JSON object with this key: "evidence_items" (list of objects).
    Each item must have:
    - "type": (e.g. "blood_stain", "weapon", "footprint", "context")
    - "description": specific detail
    - "confidence": decimal 0.0-1.0 (estimate reliability)
    - "location": where it was found/seen
    
    JSON ONLY.
    """
    res = call_openrouter_text(prompt)
    if res:
        try:
            res = res.replace("```json", "").replace("```", "").strip()
            return json.loads(res)
        except:
            pass
            
    # Fallback if LLM fails
    items = []
    text = description_text.lower()
    keywords = {"blood": "blood_stain", "knife": "weapon_blade", "gun": "weapon_firearm", "glass": "broken_glass"}
    for k, v in keywords.items():
        if k in text:
            items.append({"type": v, "description": f"Detected {k}", "confidence": 0.7, "location": "scene"})
    return {"evidence_items": items}

def analyze_weapon_and_injury(evidence_items: List[dict]) -> dict:
    w_list = []
    i_list = []
    
    for e in evidence_items:
        t = e["type"].lower()
        
        if any(x in t for x in ["knife", "blade", "shard", "broken_glass", "sharp"]):
            w_list.append({"weapon": "bladed_object", "confidence": 0.9, "reason": f"Presence of {t}"})
        elif any(x in t for x in ["gun", "firearm", "casing", "bullet", "pistol"]):
            w_list.append({"weapon": "firearm", "confidence": 0.95, "reason": f"Presence of {t}"})
        elif "blood" in t:
             i_list.append({"injury": "bleeding_wound", "lethality_probability": "medium", "reason": "Blood evidence present"})
             
    if not w_list:
         w_list.append({"weapon": "unknown_object", "confidence": 0.35, "reason": "No direct weapon evidence — inferred only."})
    
    if not i_list:
         i_list.append({"injury": "none_detected", "lethality_probability": "low", "reason": "No blood/injury markers."})

    return {"weapons": w_list, "injuries": i_list}

def generate_suspect_profiles(case_data: dict) -> dict:
    hypos = []
    
    weapons = case_data.get("weapons", [])
    main_weapon = weapons[0]["weapon"] if weapons else "unknown"
    
    h1 = {"age_range": "25-40", "build": "medium", "reason": "Standard statistical profile for this weapon type."}
    if main_weapon == "bladed_object":
        h1["reason"] = "Close-quarters combat suggests reactive aggression."
    elif main_weapon == "firearm":
        h1["reason"] = "Premeditated use of force; remote engagement."
        
    hypos.append(h1)
    hypos.append({"age_range": "18-25", "build": "athletic", "reason": "Alternative: impulsive action typically associated with younger demographics."})
    
    return {"suspect_hypotheses": hypos}

def reconstruct_timeline(evidence_items: List[dict]) -> dict:
    timeline = []
    timeline.append({"step": 1, "event": "Suspect arrived at the scene", "reason": "Movement or entry indicators detected"})
    
    has_blood = any("blood" in e["type"] for e in evidence_items)
    if has_blood:
        timeline.append({"step": 2, "event": "Victim sustained injuries", "reason": "Blood evidence confirms impact"})
    else:
        timeline.append({"step": 2, "event": "Interaction occurred", "reason": "Physical displacement of objects"})
        
    timeline.append({"step": 3, "event": "Suspect fled the scene", "reason": "Absence of suspect; open exit paths"})
    
    return {"timeline": timeline}

def calculate_confidence(evidence_items):
    if not evidence_items: return 0.0
    return sum(e["confidence"] for e in evidence_items) / len(evidence_items)

# --- Main Logic ---

def run_full_investigation(scene_text: str, image_paths=None, case_id=None, api_key=None):
    if case_id is None:
        case_id = f"CASE-{uuid.uuid4().hex[:8]}"
    if image_paths is None:
        image_paths = []

    # 1. Real Computer Vision Analysis
    image_analyses = []
    for p in image_paths:
        analysis = analyze_image_openrouter(p)
        image_analyses.append(analysis)
    
    full_visual_context = "\n".join([f"[Image {i+1} Analysis]: {a}" for i, a in enumerate(image_analyses)])
    
    # 2. Combined Context
    combined_context = f"Officer Log: {scene_text}\n\nVisual Forensics Data:\n{full_visual_context}"
    
    # 3. Evidence Extraction (LLM Powered)
    evidence_data = extract_evidence_llm(combined_context)
    evidence_items = evidence_data.get("evidence_items", [])
    
    # Ensure confidence is float
    for item in evidence_items:
        item["confidence"] = float(item.get("confidence", 0.7))

    # 4. Weapon & Injury
    weapon_result = analyze_weapon_and_injury(evidence_items)

    # 5. Suspect Profiling
    profile_result = generate_suspect_profiles({
        "description": combined_context,
        "evidence_items": evidence_items,
        "weapons": weapon_result.get("weapons", [])
    })
    
    # 6. Victim Profiling
    victim_profile = generate_victim_profile(combined_context, evidence_items)

    # 7. Timeline
    timeline_result = reconstruct_timeline(evidence_items)
    
    # 8. GIS Mapping
    lat, lon = get_random_coordinates()

    # 9. Aggregate
    aggregate = {
        "case_id": case_id,
        "description": combined_context, # Full text with visual logs
        "visual_analysis": full_visual_context, # Dedicated field
        "evidence_items": evidence_items,
        "weapons": weapon_result.get("weapons", []),
        "injuries": weapon_result.get("injuries", []),
        "suspect_hypotheses": profile_result.get("suspect_hypotheses", []),
        "victim_profile": victim_profile,
        "timeline": timeline_result.get("timeline", []),
        "gis_location": {"lat": lat, "lon": lon}
    }

    # 10. Executive Summary
    prompt = f"""
    You are a senior forensic crime analyst.
    Write a sharp, professional forensic executive summary.
    
    Data:
    {json.dumps(aggregate, indent=2, default=str)}
    """
    
    summary_text = call_openrouter_text(prompt)
    if not summary_text:
        # Fallback if API fails
        summary_text = f"Automated summary unavailable. Ensure Network/API connectivity.\nKey Findings: {len(evidence_items)} evidence items detected."
            
    aggregate["executive_summary"] = summary_text

    # 11. Risk Score (Adjusted Thresholds)
    score = 0
    # Base score on evidence count
    score += min(len(evidence_items), 4) 
    
    # Weapon lethality (Adjusted for higher sensitivity)
    weapons = aggregate["weapons"]
    if weapons:
        w_conf = weapons[0].get("confidence", 0)
        if weapons[0]["weapon"] == "firearm": score += 6
        elif weapons[0]["weapon"] == "bladed_object": score += 4
        else: score += 2
    
    # Injury presence
    injuries = aggregate["injuries"]
    if injuries and injuries[0]["injury"] != "none_detected":
        score += 3
        
    aggregate["risk_score"] = min(score, 10)

    # 12. Save to DB
    case_manager_local = CaseManager()
    case_manager_local.save_session(case_id, {
        "case:aggregate": aggregate,
        "case:risk_score": aggregate["risk_score"],
        "case:summary": aggregate["executive_summary"]
    })
    
    out_json = save_json(aggregate, f"{case_id}.json")
    try:
        pdf_path = markdown_to_pdf(f"Case Report: {case_id}\n\n{aggregate['executive_summary']}", f"{case_id}.pdf")
    except:
        pdf_path = None
        
    return {
        "case_id": case_id,
        "aggregate": aggregate,
        "json_path": out_json,
        "pdf_path": pdf_path
    }

def ask_memory_helper(query, case_id):
    state = case_manager.get_session(case_id)
    if not state: 
        return "Case data not found."
    
    agg = state.get("case:aggregate", {})
    prompt = f"""
    Answer the user query based ONLY on this forensic case data.
    
    Query: {query}
    
    Case Data:
    {json.dumps(agg, default=str)}
    """
    return call_openrouter_text(prompt) or "Analysis failed."

def list_all_cases_df():
    sessions = case_manager.list_sessions()
    data = []
    for s in sessions:
        agg = s["state"].get("case:aggregate", {})
        
        # Safe extraction of weapon
        w_list = agg.get("weapons", [])
        w_main = w_list[0]["weapon"] if w_list else "Unknown"
        
        # safely get location
        loc = agg.get("gis_location", {})
        
        data.append({
            "case_id": s["session_id"],
            "risk_score": s["state"].get("case:risk_score", 0),
            "mem_primary_weapon": w_main,
            "num_evidence": len(agg.get("evidence_items", [])),
            "updated_at": s["updated_at"],
            "lat": loc.get("lat", None),
            "lon": loc.get("lon", None)
        })
    return pd.DataFrame(data)
