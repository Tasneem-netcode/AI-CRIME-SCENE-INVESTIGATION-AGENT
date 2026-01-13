
import streamlit as st
import pandas as pd
import csi_backend as csi
import os
import time

# (Triggers Reload)
# --- Page Config ---
st.set_page_config(
    page_title="AI Crime Scene Investigator",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State (Must be initialized before Sidebar usage) ---
if "current_case" not in st.session_state:
    st.session_state.current_case = None

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

    /* Tabs Styling - Increased Gap */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 10px 20px;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-family: 'Exo 2', sans-serif;
        font-weight: 600;
        border: none;
        padding: 0 20px;
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
    
    /* Gemini Input Style */
    .stTextArea textarea {
        background: rgba(15, 23, 42, 0.5) !important;
        border-color: rgba(255,255,255,0.1) !important;
        font-size: 1.1em;
        padding: 15px;
    }

</style>
""", unsafe_allow_html=True)

# --- Configuration Sidebar (Rewritten for ChatGPT Style) ---
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/fingerprint.png", width=80) 
    st.title("Case History")
    
# 1. Dynamic History List
    df_cases = csi.list_all_cases_df()
    if not df_cases.empty:
        st.markdown("<div style='font-size: 0.8em; color: #94a3b8; margin-top: 20px; margin-bottom: 10px;'>RECENT CASES</div>", unsafe_allow_html=True)
        # Iterate desc (newest first)
        for idx, row in df_cases.iterrows():
            # Create a label (concise)
            c_label = f"{row['case_id'][:8]}.. | {row['mem_primary_weapon'][:8]}"
            
            # Style differently if active
            btn_type = "primary" if st.session_state.current_case and st.session_state.current_case.get("case_id") == row['case_id'] else "secondary"
            
            # Compact buttons
            if st.button(c_label, key=f"sidebar_case_{row['case_id']}", use_container_width=True, type=btn_type):
                full_state = csi.case_manager.get_session(row['case_id'])
                if full_state and "case:aggregate" in full_state:
                    res = {
                        "case_id": row['case_id'],
                        "aggregate": full_state["case:aggregate"],
                        "json_path": csi.OUT_DIR / f"{row['case_id']}.json",
                        "pdf_path": csi.OUT_DIR / f"{row['case_id']}.pdf"
                    }
                    st.session_state.current_case = res
                    st.rerun()

    st.markdown("---")
    st.info("**System Status:** Online\n\n**Version:** 2.2.0 (Ultra)\n\n**Secure Connection:** Active")

# --- UI Components ---
def render_metric_card(label, value, color="blue", subtext=None):
    st.markdown(f"""
    <div class="css-card">
        <h3 style="margin:0; font-size: 1rem; color: #94a3b8;">{label}</h3>
        <h2 style="margin:5px 0; font-size: 2.2rem; background: linear-gradient(to right, {color}, white); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{value}</h2>
        {f'<p style="margin:0; font-size: 0.8rem; color: #64748b;">{subtext}</p>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)

def display_case(result, show_input=False):
    agg = result.get("aggregate", {})
    case_id = result.get("case_id")
    
    # Extract description text safely
    desc_obj = agg.get("description", "No description available.")
    if isinstance(desc_obj, dict):
        scene_text = desc_obj.get("description", "No description available.")
    else:
        scene_text = str(desc_obj)
    
    # --- ROW 1: Input (Left) + Risk & Summary (Right) ---
    r1c1, r1c2 = st.columns([1, 2])
    
    with r1c1:
        # User Input / Description Card
        st.markdown(f"""
        <div class="css-card" style="height: 100%; overflow-y: auto; max-height: 400px; margin-bottom: 10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3>📝 Case Input</h3>
                <span style="font-size:0.7em; background:#3b82f6; padding:2px 6px; border-radius:4px;">Gemini 2.0 Flash</span>
            </div>
            <div style="font-size: 0.9em; color: #cbd5e1; white-space: pre-wrap; margin-top: 10px;">{scene_text[:500] + ("..." if len(scene_text)>500 else "")}</div>
            <br>
            <div style="font-size: 0.75em; color: #64748b;">ID: {case_id}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # New Visual Analysis Card
        vis_analysis = agg.get("visual_analysis", "")
        if vis_analysis:
            st.markdown(f"""
            <div class="css-card" style="height: 100%; overflow-y: auto; max-height: 300px; border: 1px solid rgba(56, 189, 248, 0.3);">
                <h3>👁️ Visual Forensics</h3>
                <div style="font-size: 0.85em; color: #7dd3fc; white-space: pre-wrap; margin-top: 5px;">{vis_analysis}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Update / Append Button (ChatGPT Style - Add to Context)
        if st.toggle("✏️ Update / Add Evidence"):
            with st.form(f"update_form_{case_id}"):
                new_notes = st.text_area("Additional Notes / Changes", placeholder="Update scenario details...")
                new_files = st.file_uploader("Add New Media", accept_multiple_files=True)
                
                if st.form_submit_button("🔄 Update Case Analysis"):
                    # MERGE LOGIC: Combine old text + new text.
                    # Ideally, backend handles context window, but for now we append.
                    combined_text = scene_text + "\n\n[UPDATED LOG]: " + new_notes if new_notes else scene_text
                    
                    with st.spinner("Updating case files..."):
                         img_paths = []
                         if new_files:
                             uploads_dir = Path("uploads")
                             uploads_dir.mkdir(exist_ok=True)
                             for uf in new_files:
                                 path = uploads_dir / uf.name
                                 with open(path, "wb") as f:
                                     f.write(uf.getbuffer())
                                 img_paths.append(str(path))
                         
                         # CALL BACKEND WITH EXISTING ID
                         upd_result = csi.run_full_investigation(combined_text, img_paths, case_id=case_id)
                         st.session_state.current_case = upd_result
                         st.toast(f"Case {case_id} updated!", icon="🔄")
                         time.sleep(1)
                         st.rerun()

    with r1c2:
        # Risk & Executive Summary Split
        sub_c1, sub_c2 = st.columns([1, 2])
        with sub_c1:
            risk = agg.get("risk_score", 0)
            risk_color = "#ef4444" if risk > 7 else "#f59e0b" if risk > 4 else "#22c55e"
            st.markdown(f"""
            <div class="css-card" style="border-left: 5px solid {risk_color}; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <h3 style="color:{risk_color}; margin: 0;">Risk Level</h3>
                <div style="font-size: 3.5em; font-weight: bold; color: {risk_color}; line-height: 1.2;">{risk}<span style="font-size: 0.4em; color: #64748b">/10</span></div>
                <p style="margin: 0; opacity: 0.8;">{'CRITICAL' if risk > 7 else 'HIGH' if risk > 4 else 'LOW'} PRIORITY</p>
            </div>
            """, unsafe_allow_html=True)
            
        with sub_c2:
            summary = agg.get("executive_summary")
            summary_content = summary if summary else "Summary unavailable."
            st.markdown(f"""
            <div class="css-card" style="height: 100%; overflow-y:auto; max-height: 250px;">
                <h3>📑 Executive Summary</h3>
                <div style="margin-top: 10px; line-height: 1.6; color: #e2e8f0; font-size: 0.95em;">{summary_content}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- ROW 1.5: Victim Profile (NEW) ---
    vp = agg.get("victim_profile", {})
    if vp and vp.get("risk_level") != "Unknown":
        st.markdown(f"""
        <div class="css-card" style="margin-top: 10px; margin-bottom: 10px; border: 1px solid rgba(168, 85, 247, 0.3);">
            <h3 style="color: #c084fc;">🩸 Victimology Profile</h3>
            <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px;">
                <div><strong>Inferred Demographics:</strong> {vp.get('demographics_inferred', 'N/A')}</div>
                <div><strong>Suspect Relation:</strong> {vp.get('relation_to_suspect_hypothesis', 'N/A')}</div>
                <div><strong>Victim Risk:</strong> {vp.get('risk_level', 'N/A')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- ROW 2: Evidence & Weapons ---
    r2c1, r2c2 = st.columns([1.5, 1])
    
    with r2c1:
        # Evidence Table
        st.markdown('<div class="css-card"><h3>🔎 Detected Evidence</h3>', unsafe_allow_html=True)
        evidence = agg.get("evidence_items", [])
        if evidence:
            df_ev = pd.DataFrame(evidence)
            st.dataframe(
                df_ev[["type", "description", "confidence"]], 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "type": st.column_config.TextColumn("Type", width="small"),
                    "description": "Description",
                    "confidence": st.column_config.ProgressColumn("Confidence", format="%.2f", min_value=0, max_value=1)
                }
            )
        else:
            st.info("No evidence items processed.")
        st.markdown('</div>', unsafe_allow_html=True)
            
    with r2c2:
        # Weapon Analysis (Pure HTML)
        weapons = agg.get("weapons", [])
        injuries = agg.get("injuries", [])
        
        w_html = ""
        if weapons:
            w = weapons[0]
            w_html = f"""
            <div style="margin-bottom: 15px;">
                <div style="color: #38bdf8; font-weight: bold; font-size: 1.1em;">PRIMARY WEAPON</div>
                <div style="font-size: 1.4em; color: white;">{w['weapon'].upper()}</div>
                <div style="font-size: 0.8em; color: #94a3b8;">{w['reason']} ({int(w['confidence']*100)}% Conf)</div>
            </div>
            """
        
        i_html = ""
        if injuries:
            i = injuries[0]
            i_html = f"""
            <div>
                <div style="color: #f87171; font-weight: bold; font-size: 1.1em;">INJURY PATTERN</div>
                <div style="font-size: 1.4em; color: white;">{i['injury'].upper()}</div>
                <div style="font-size: 0.8em; color: #94a3b8;">{i['reason']}</div>
            </div>
            """
            
        # Strip indentation to prevent code block rendering
        import textwrap
        content = textwrap.dedent(f"""
            <h3>🔫 Forensic Analysis</h3>
            {w_html}
            <hr style="border-color: rgba(255,255,255,0.1);">
            {i_html}
        """)
        
        st.markdown(f'<div class="css-card" style="height: 100%;">{content}</div>', unsafe_allow_html=True)

    # --- ROW 3: Timeline & Profiles ---
    import textwrap

    r3c1, r3c2 = st.columns(2)
    
    with r3c1:
        timeline = agg.get("timeline", [])
        t_items = ""
        for t in timeline:
            # Construct each item without extra internal indentation
            t_items += f"""
            <div style="border-left: 2px solid #3b82f6; padding-left: 15px; margin-bottom: 20px; position: relative;">
                <div style="position: absolute; left: -6px; top: 0; width: 10px; height: 10px; background: #3b82f6; border-radius: 50%;"></div>
                <strong style="color: #38bdf8">Step {t['step']}</strong>
                <div style="margin-top: 4px; font-weight: 500;">{t['event']}</div>
                <div style="font-size: 0.85em; color: #64748b; margin-top: 2px;">{t['reason']}</div>
            </div>"""
            
        # Clean up the timeline Items string
        t_items = textwrap.dedent(t_items)
        
        content_timeline = textwrap.dedent(f"""
            <h3>🕰️ Reconstruction</h3>
            <div style="margin-top: 15px;">
                {t_items}
            </div>
        """)
        
        st.markdown(f'<div class="css-card">{content_timeline}</div>', unsafe_allow_html=True)
        
    with r3c2:
        suspects = agg.get("suspect_hypotheses", [])
        s_html = ""
        if suspects:
            for idx, s in enumerate(suspects):
                s_html += f"""
                <div style="background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="color: #a78bfa; font-weight: bold;">HYPOTHESIS {idx+1}</div>
                    <div style="margin: 5px 0;"><strong>Age/Build:</strong> {s.get('age_range')}, {s.get('build')}</div>
                    <div style="font-size: 0.9em; color: #94a3b8; font-style: italic;">"{s.get('reason')}"</div>
                </div>"""
        else:
            s_html = "<div>Insufficient data for profiling.</div>"

        # Clean up the suspect items string
        s_html = textwrap.dedent(s_html)

        content_suspects = textwrap.dedent(f"""
            <h3>👤 Suspect Profiling</h3>
            {s_html}
        """)

        st.markdown(f'<div class="css-card">{content_suspects}</div>', unsafe_allow_html=True)

    # DOWNLOADS (Footer)
    col1, col2, _ = st.columns([1,1,3])
    with col1:
        with open(result.get("json_path"), "rb") as f:
            st.download_button("💾 Export JSON", f, file_name=f"{case_id}.json", mime="application/json", use_container_width=True)
    with col2:
        try:
             with open(result.get("pdf_path"), "rb") as f:
                st.download_button("📄 Export PDF", f, file_name=f"{case_id}.pdf", mime="application/pdf", use_container_width=True)
        except:
            pass
            
    # Delete Option in View
    if st.button("🗑️ Delete This Case", key=f"del_main_{case_id}", type="secondary"):
        csi.case_manager.delete_session(case_id)
        st.session_state.current_case = None
        st.toast("Case deleted.")
        time.sleep(0.5)
        st.rerun()

# --- Top Navigation ---
st.title("AI CRIME SCENE INVESTIGATOR")
tabs = st.tabs(["📊 Dashboard", "🕵️ Investigation", "🧠 Neural Query"])

# --- TAB 1: DASHBOARD ---
with tabs[0]:
    st.markdown("<br>", unsafe_allow_html=True)
    df = csi.list_all_cases_df()
    
    # KPI Row
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        render_metric_card("Total Cases Solved", len(df), "#3b82f6", "Updated in real-time")
    with kpi2:
        # Cloud Agent Status Sim
        st.markdown("""
        <div class="css-card" style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h3 style="margin:0; font-size: 1rem; color: #94a3b8;">Cloud Agents</h3>
                <h2 style="margin:5px 0; font-size: 1.8rem; background: linear-gradient(to right, #a855f7, white); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">ACTIVE</h2>
            </div>
            <div style="text-align: right;">
                <div style="color: #22c55e; font-size: 0.8em;">● Gemini 2.0 Flash</div>
                <div style="color: #22c55e; font-size: 0.8em;">● Vision-Pro-1</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        evidence_count = df['num_evidence'].sum() if not df.empty else 0
        render_metric_card("Evidence Items", evidence_count, "#22c55e", "Processed by vision systems")

    # GIS Crime Map
    st.markdown("### 🗺️ Geospatial Crime Mapping")
    if not df.empty and 'lat' in df.columns:
        # Filter for valid coordinates
        map_df = df.dropna(subset=['lat', 'lon'])
        if not map_df.empty:
            st.map(map_df, latitude='lat', longitude='lon', size=20, color='#ef4444')
        else:
            st.info("No geospatial data available yet.")
    else:
        st.info("Awaiting GIS synchronization...")

    if not df.empty:
        st.markdown("""
        <div class="css-card">
            <h3>📡 Recent System Activity</h3>
        """, unsafe_allow_html=True)
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

# --- TAB 2: INVESTIGATION (Dynamic) ---
with tabs[1]:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Logic: If case exists, show RESULTS MODE. Else, show INPUT MODE.
    if st.session_state.current_case:
        display_case(st.session_state.current_case, show_input=True)
        
    else:
        # --- INPUT MODE ---
        col1, col2 = st.columns([1.2, 0.8])
        
        with col1:
            st.markdown("### 📝 Analysis Input")
            with st.form("investigation_form"):
                scene_text = st.text_area(
                    "Observation Log", 
                    height=300, 
                    placeholder="Enter detailed crime scene observations here..."
                )
                
                c_up1, c_up2 = st.columns([3,1])
                with c_up1:
                     uploaded_files = st.file_uploader("Evidence Media", accept_multiple_files=True, label_visibility="collapsed")
                with c_up2:
                    st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("🚀 RUN DIAGNOSTICS", use_container_width=True)
                
                if submitted and scene_text:
                    with st.spinner("Initializing neural forensics..."):
                        img_paths = []
                        if uploaded_files:
                            uploads_dir = Path("uploads")
                            uploads_dir.mkdir(exist_ok=True)
                            for uf in uploaded_files:
                                path = uploads_dir / uf.name
                                with open(path, "wb") as f:
                                    f.write(uf.getbuffer())
                                img_paths.append(str(path))
                        
                        # New Case -> No ID passed, backend generates one
                        result = csi.run_full_investigation(scene_text, img_paths)
                        st.session_state.current_case = result
                        st.rerun()

        with col2:
             st.markdown("""
            <div style="text-align: center; color: #64748b; padding-top: 100px; opacity: 0.6;">
                <img src="https://img.icons8.com/nolan/96/artificial-intelligence.png" width="100" style="margin-bottom: 20px;">
                <h2 style="color: #94a3b8; font-family: 'Exo 2';">System Idle</h2>
                <div style="margin-top:20px; font-size: 0.8em; color: #475569;">Awaiting Data Input</div>
            </div>
            """, unsafe_allow_html=True)

# --- TAB 3: MEMORY ---
with tabs[2]:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1,2])
    
    df = csi.list_all_cases_df()
    
    if not df.empty:
        with c1:
            # Combined Header Card
            st.markdown("""
            <div class="css-card" style="margin-bottom: 0px; border-bottom-left-radius: 0; border-bottom-right-radius: 0; border-bottom: none;">
                <h3>Context</h3>
                <div style="font-size: 0.8em; color: #94a3b8;">Select active case memory for interrogation.</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Widget (Appears "inside" or attached to the card due to styling)
            case_id = st.selectbox("Active Case Context", df["case_id"].tolist(), label_visibility="collapsed")
            
        with c2:
            st.markdown("""
            <div class="css-card" style="margin-bottom: 0px; border-bottom-left-radius: 0; border-bottom-right-radius: 0; border-bottom: none;">
                <h3>Neural Query Interface</h3>
                <div style="font-size: 0.8em; color: #94a3b8;">Natural language search across case files.</div>
            </div>
            """, unsafe_allow_html=True)
            
            query = st.text_input("Interrogate Data Information", placeholder="e.g. 'What weapon was determined?'", label_visibility="collapsed")
            
            if query:
                st.markdown("""
                <div class="css-card" style="margin-top: 10px; border-top-left-radius: 0; border-top-right-radius: 0;">
                """, unsafe_allow_html=True)
                
                with st.chat_message("assistant"):
                    with st.spinner("Searching neural pathways..."):
                        answer = csi.ask_memory_helper(query, case_id)
                        time.sleep(0.5) # UI effect
                        st.markdown(f"**Analysis Result:**\n\n{answer}")
                
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No memory banks established.")
