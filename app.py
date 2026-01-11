
import streamlit as st
import pandas as pd
import csi_backend as csi
import os
import time

# --- Page Config ---
st.set_page_config(
    page_title="AI Crime Scene Investigator",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS (CSI/Glass Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
        color: #e2e8f0;
        font-family: 'Exo 2', sans-serif;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #020617; 
    }
    ::-webkit-scrollbar-thumb {
        background: #334155; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569; 
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-family: 'Exo 2', sans-serif;
        font-weight: 600;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255, 255, 255, 0.05);
        color: #cbd5e1;
        transform: translateY(-1px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }

    /* Headings */
    h1, h2, h3 {
        color: #f8fafc;
        font-family: 'Exo 2', sans-serif;
        letter-spacing: 0.5px;
    }
    h1 {
        background: linear-gradient(to right, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(96, 165, 250, 0.2);
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-family: 'Exo 2', sans-serif;
        color: #38bdf8;
        text-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    /* Cards/Containers (Glassmorphism) */
    .css-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .css-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
        border-color: rgba(56, 189, 248, 0.4);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #2563eb, #06b6d4);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7em 1.5em;
        font-family: 'Exo 2', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(37, 99, 235, 0.4);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8, #0891b2);
        box-shadow: 0 0 25px rgba(37, 99, 235, 0.6);
        transform: translateY(-2px);
    }
    
    /* Dataframes */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f1f5f9 !important;
        border-radius: 8px;
        font-family: 'Exo 2', sans-serif;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Toast */
    div[data-baseweb="toast"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: white;
        border-radius: 8px;
    }

</style>
""", unsafe_allow_html=True)

# --- Configuration Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/fingerprint.png", width=80) 
    st.title("Settings")
    
    # Secure handling: Key re-integrated as requested by user
    api_key_default = "AIzaSyB6suR8iFycHZ7VNI5Ybn0apiqf-MrUnb0"
    api_key = st.text_input("Gemini API Key", value=api_key_default, type="password", help="Required for Executive Summary generation")
    
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            st.success("Key active (Env)")
        else:
            st.warning("Analysis Limited (No Key)")
    else:
        st.success("System Authenticated")
        
    st.markdown("---")
    st.info("**System Status:** Online\n\n**Version:** 2.2.0 (Ultra)\n\n**Secure Connection:** Active")

# --- Session State ---
if "current_case" not in st.session_state:
    st.session_state.current_case = None

# --- UI Components ---

def render_metric_card(label, value, color="blue", subtext=None):
    st.markdown(f"""
    <div class="css-card">
        <h3 style="margin:0; font-size: 1rem; color: #94a3b8;">{label}</h3>
        <h2 style="margin:5px 0; font-size: 2.2rem; background: linear-gradient(to right, {color}, white); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{value}</h2>
        {f'<p style="margin:0; font-size: 0.8rem; color: #64748b;">{subtext}</p>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)

def display_case(result):
    agg = result.get("aggregate", {})
    case_id = result.get("case_id")
    
    st.markdown(f"## 📂 Case File: `{case_id}`")
    
    # RISK & SUMMARY
    col1, col2 = st.columns([1, 2])
    with col1:
        risk = agg.get("risk_score", 0)
        risk_color = "#ef4444" if risk > 3 else "#f59e0b" if risk > 1 else "#22c55e"
        
        st.markdown(f"""
        <div class="css-card" style="border-left: 5px solid {risk_color}; height: 100%;">
            <h3 style="color:{risk_color}">Risk Assessment</h3>
            <div style="font-size: 3em; font-weight: bold; color: {risk_color}">{risk}<span style="font-size: 0.4em; color: #64748b">/10</span></div>
            <p>{'CRITICAL LEVEL' if risk > 3 else 'MODERATE LEVEL' if risk > 1 else 'LOW LEVEL'}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="css-card" style="height: 100%;">', unsafe_allow_html=True)
        st.subheader("📑 Executive Summary")
        summary = agg.get("executive_summary")
        if summary and "Gemini API Key missing" not in summary:
            st.write(summary)
        else:
            st.warning(summary or "No summary available.")
        st.markdown('</div>', unsafe_allow_html=True)

    # EVIDENCE & WEAPONS
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🔎 Evidence")
        evidence = agg.get("evidence_items", [])
        if evidence:
            df_ev = pd.DataFrame(evidence)
            st.dataframe(df_ev[["type", "description", "confidence"]], use_container_width=True, hide_index=True)
        else:
            st.info("No evidence items processed.")
        st.markdown('</div>', unsafe_allow_html=True)
            
    with c2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🔫 Analysis")
        weapons = agg.get("weapons", [])
        injuries = agg.get("injuries", [])
        
        if weapons:
            w = weapons[0]
            st.markdown(f"**Primary Weapon:** <span style='color:#38bdf8'>{w['weapon'].upper()}</span>", unsafe_allow_html=True)
            st.caption(f"Confidence: {w['confidence']} | {w['reason']}")
            st.progress(min(w['confidence'], 1.0))
        
        st.divider()
        
        if injuries:
            i = injuries[0]
            st.markdown(f"**Primary Injury:** <span style='color:#f87171'>{i['injury'].upper()}</span>", unsafe_allow_html=True)
            st.caption(f"Type: {i['lethality_probability']} | {i['reason']}")
        st.markdown('</div>', unsafe_allow_html=True)

    # TIMELINE & SUSPECTS
    c_time, c_susp = st.columns([1.5, 1])
    
    with c_time:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🕰️ Event Timeline")
        timeline = agg.get("timeline", [])
        for t in timeline:
             st.markdown(f"""
             <div style="border-left: 2px solid #3b82f6; padding-left: 15px; margin-bottom: 15px;">
                <strong style="color: #38bdf8">Step {t['step']}</strong>: {t['event']}
                <br><span style="font-size: 0.9em; color: #94a3b8">{t['reason']}</span>
             </div>
             """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_susp:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("👤 Profiling")
        suspects = agg.get("suspect_hypotheses", [])
        if suspects:
            for idx, s in enumerate(suspects):
                with st.expander(f"Suspect Hypothesis {idx+1}", expanded=(idx==0)):
                    st.write(f"**Age:** {s.get('age_range')}")
                    st.write(f"**Build:** {s.get('build')}")
                    st.caption(s.get('reason'))
        else:
            st.write("Insufficient data for profiling.")
        st.markdown('</div>', unsafe_allow_html=True)

    # DOWNLOADS
    col1, col2, _ = st.columns([1,1,3])
    with col1:
        with open(result.get("json_path"), "rb") as f:
            st.download_button("💾 Export JSON", f, file_name=f"{case_id}.json", mime="application/json", use_container_width=True)
    with col2:
        try:
             with open(result.get("pdf_path"), "rb") as f:
                st.download_button("📄 Export PDF", f, file_name=f"{case_id}.pdf", mime="application/pdf", use_container_width=True)
        except:
            st.error("PDF Missing")

# --- Top Navigation ---
st.title("AI CRIME SCENE INVESTIGATOR")
tabs = st.tabs(["📊 Dashboard", "🕵️ New Investigation", "🗃️ Archives", "🧠 Neural Query"])

# --- TAB 1: DASHBOARD ---
with tabs[0]:
    st.markdown("<br>", unsafe_allow_html=True)
    df = csi.list_all_cases_df()
    
    # KPI Row
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        render_metric_card("Total Cases Solved", len(df), "#3b82f6", "Updated in real-time")
    with kpi2:
        high_risk = len(df[df['risk_score'] > 3]) if not df.empty else 0
        render_metric_card("High Risk Cases", high_risk, "#ef4444", "Requires immediate attention")
    with kpi3:
        evidence_count = df['num_evidence'].sum() if not df.empty else 0
        render_metric_card("Evidence Items", evidence_count, "#22c55e", "Processed by vision systems")

    st.markdown("### 📡 Recent System Activity")
    if not df.empty:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.dataframe(
            df[["case_id", "mem_primary_weapon", "risk_score", "updated_at"]].sort_values("updated_at", ascending=False).head(5),
            use_container_width=True,
            hide_index=True,
            column_config={
                "case_id": "Case ID",
                "mem_primary_weapon": "Primary Weapon",
                "risk_score": st.column_config.ProgressColumn("Risk Level", min_value=0, max_value=10, format="%d"),
                "updated_at": "Timestamp"
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("System initialized. No case data available.")

# --- TAB 2: NEW INVESTIGATION ---
with tabs[1]:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="css-card">
            <h3>📝 Case Entry</h3>
            <p>Input initial scene observation logs below.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("investigation_form"):
            scene_text = st.text_area("Observation Log", height=250, placeholder="Example: Victim found in the living room. Large pool of blood near the sofa. A muddy footprint leading to the back door. Broken glass on the floor...")
            uploaded_files = st.file_uploader("Upload Evidence Media", accept_multiple_files=True, help="Supports PNG, JPG, JPEG")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 INITIATE ANALYSIS SEQUENCE", use_container_width=True)
            
            if submitted and scene_text:
                with st.spinner("Processing scene data... Running heuristics... Generating profile..."):
                    img_paths = []
                    if uploaded_files:
                        uploads_dir = Path("uploads")
                        uploads_dir.mkdir(exist_ok=True)
                        for uf in uploaded_files:
                            path = uploads_dir / uf.name
                            with open(path, "wb") as f:
                                f.write(uf.getbuffer())
                            img_paths.append(str(path))
                    
                    result = csi.run_full_investigation(scene_text, img_paths, api_key=api_key)
                    st.session_state.current_case = result
                    st.toast("Investigation Complete!", icon="✅")

    with col2:
        if st.session_state.current_case:
            display_case(st.session_state.current_case)
        else:
            st.markdown("""
            <div style="text-align: center; color: #64748b; padding-top: 50px;">
                <h1>waiting for input...</h1>
                <p>Enter case details to begin forensic analysis.</p>
            </div>
            """, unsafe_allow_html=True)

# --- TAB 3: ARCHIVES ---
with tabs[2]:
    st.markdown("<br>", unsafe_allow_html=True)
    df = csi.list_all_cases_df()
    
    if not df.empty:
        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown("### Select Case")
            case_id = st.selectbox("Identifier", df["case_id"].tolist(), label_visibility="collapsed")
            if st.button("Load Archival Data", use_container_width=True):
                full_state = csi.case_manager.get_session(case_id)
                if full_state and "case:aggregate" in full_state:
                    res = {
                        "case_id": case_id,
                        "aggregate": full_state["case:aggregate"],
                        "json_path": csi.OUT_DIR / f"{case_id}.json",
                        "pdf_path": csi.OUT_DIR / f"{case_id}.pdf"
                    }
                    st.session_state.view_case = res
                else:
                    st.error("Data integrity error.")
        
        with c2:
            if "view_case" in st.session_state:
                display_case(st.session_state.view_case)
            else:
                st.info("Select a case from the menu to view details.")
    else:
        st.write("Archive empty.")

# --- TAB 4: MEMORY ---
with tabs[3]:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1,2])
    
    df = csi.list_all_cases_df()
    
    if not df.empty:
        with c1:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.subheader("Context")
            case_id = st.selectbox("Active Case Context", df["case_id"].tolist())
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c2:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.subheader("Neural Query Interface")
            query = st.text_input("Interrogate Data Information", placeholder="e.g. 'What weapon was determined?'")
            
            if query:
                st.markdown("---")
                with st.chat_message("assistant"):
                    with st.spinner("Searching neural pathways..."):
                        answer = csi.ask_memory_helper(query, case_id)
                        time.sleep(0.5) # UI effect
                        st.markdown(f"**Analysis Result:**\n\n{answer}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No memory banks established.")
