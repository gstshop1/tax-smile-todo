import streamlit as st
import pandas as pd
import time
from datetime import datetime, date
from supabase import create_client, Client

# 1. Page Config
st.set_page_config(page_title="Tax Smile ToDo", page_icon="📝", layout="wide")

# 2. Supabase Connection
SUPABASE_URL = "https://bpthxlzljselcdqvmwjc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwdGh4bHpsanNlbGNkcXZtd2pjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4MzA3MzEsImV4cCI6MjA5MDQwNjczMX0.jSpfNfyNwtwMJhQ-lxyBBkQx24iI9JpnU5V75e7iq-I"

# Passwords
ADMIN_PASSWORD = "sajan123"
STAFF_PASSWORD = "sajan12"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- MODERN PREMIUM CSS STYLING ---
st.markdown(
    """
    <style>
    /* Global Styles */
    .stApp { background-color: #f4f7f6; }
    
    /* Sidebar Styling - Dark Navy/Gray */
    [data-testid="stSidebar"] { 
        background-color: #1e1e2d !important; 
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #ffffff !important; font-weight: bold !important;
    }

    /* Sidebar Input Boxes & Select Boxes - Text Color to Black */
    [data-testid="stSidebar"] input, 
    [data-testid="stSidebar"] select, 
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #000000 !important;
        font-weight: 500 !important;
    }

    /* Professional Gradient Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white !important;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(37, 117, 252, 0.3);
    }
    
    /* Document View/Download Badges */
    .view-pill { 
        background-color: #d1fae5; color: #065f46 !important; 
        padding: 6px 14px; border-radius: 20px; font-weight: 700; 
        text-decoration: none; font-size: 13px; border: 1px solid #059669;
        display: inline-block; margin-right: 10px;
    }
    .dl-pill { 
        background-color: #fef3c7; color: #92400e !important; 
        padding: 6px 14px; border-radius: 20px; font-weight: 700; 
        text-decoration: none; font-size: 13px; border: 1px solid #d97706;
        display: inline-block;
    }
    
    /* Header Typography */
    .main-header {
        color: #1e1e2d;
        font-weight: 800;
        text-align: center;
        font-size: 42px;
        margin-bottom: 25px;
    }
    
    /* Card Container for Details */
    .report-card {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Functions ---
def fetch_staff():
    try:
        res = supabase.table("staff").select("staff_name").order("staff_name").execute()
        db_names = [item['staff_name'] for item in res.data]
        if "Sajan" not in db_names: db_names.insert(0, "Sajan")
        return db_names
    except: return ["Sajan"]

def fetch_clients():
    try:
        res = supabase.table("tasks").select("client_name").execute()
        return sorted(list(set([item['client_name'] for item in res.data if item['client_name']])))
    except: return []

def fetch_tasks_all():
    try:
        res = supabase.table("tasks").select("*").order("deadline", desc=False).execute()
        return res.data
    except: return []

def upload_multiple_to_storage(files, folder, client):
    links = []
    progress_bar = st.progress(0, text="Uploading documents...")
    for i, file in enumerate(files):
        try:
            clean_name = "".join(x for x in client if x.isalnum())
            file_ext = file.name.split('.')[-1]
            file_path = f"{folder}/{clean_name}_{int(time.time())}_{i}.{file_ext}"
            supabase.storage.from_("media").upload(path=file_path, file=file.getvalue())
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/media/{file_path}"
            links.append({"name": file.name, "url": public_url})
            progress_bar.progress((i + 1) / len(files))
        except: st.error(f"Failed to upload: {file.name}")
    time.sleep(0.5)
    progress_bar.empty()
    return links

def update_task_status(task_id, new_status, staff_comment, admin_query):
    try:
        supabase.table("tasks").update({"status": new_status, "staff_comment": staff_comment, "admin_query": admin_query}).eq("id", task_id).execute()
        return True
    except: return False

# --- Session Management ---
if "selected_task" not in st.session_state: st.session_state.selected_task = None
if "last_user" not in st.session_state: st.session_state.last_user = None
if "filter_overdue" not in st.session_state: st.session_state.filter_overdue = False

# --- SIDEBAR ---
st.sidebar.markdown("# 🏛️ TAX SMILE")
st.sidebar.markdown("---")
st.sidebar.header("👤 User Account")
staff_list = fetch_staff()
current_user = st.sidebar.selectbox("Log in as:", ["-- Select User --"] + staff_list)

if st.session_state.last_user != current_user:
    st.session_state.last_user = current_user
    st.session_state.selected_task = None
    st.session_state.filter_overdue = False
    st.rerun()

authenticated, is_admin = False, False
if current_user != "-- Select User --":
    pwd_input = st.sidebar.text_input("Access Password", type="password")
    if current_user == "Sajan" and pwd_input == ADMIN_PASSWORD:
        authenticated, is_admin = True, True
    elif pwd_input == STAFF_PASSWORD:
        authenticated = True

if authenticated and is_admin and st.session_state.selected_task is None:
    st.sidebar.divider()
    st.sidebar.header("🆕 Assign New Work")
    clients = fetch_clients()
    with st.sidebar.form("assign_form", clear_on_submit=True):
        c_sel = st.selectbox("Existing Client", ["-- New Entry --"] + clients)
        c_new = st.text_input("New Client Name")
        work = st.selectbox("Service", ["GST Filing", "Income Tax", "Audit Support", "Consultancy", "Other"])
        stf = st.selectbox("Staff Member", staff_list)
        due = st.date_input("Deadline")
        up_files = st.file_uploader("Documents", accept_multiple_files=True)
        up_audio = st.audio_input("Voice Record")
        if st.form_submit_button("Assign Task"):
            final_c = c_new if c_new else (c_sel if c_sel != "-- New Entry --" else "")
            if final_c:
                with st.spinner("Processing..."):
                    f_links = upload_multiple_to_storage(up_files, "docs", final_c) if up_files else []
                    a_url = ""
                    if up_audio:
                        a_path = f"audio/{int(time.time())}.wav"
                        supabase.storage.from_("media").upload(a_path, up_audio.getvalue())
                        a_url = f"{SUPABASE_URL}/storage/v1/object/public/media/{a_path}"
                    supabase.table("tasks").insert({"client_name": final_c, "work_type": work, "assigned_to": stf, "deadline": str(due), "status": "Pending", "file_links": f_links, "audio_url": a_url}).execute()
                st.sidebar.success("✅ Work Assigned!"); time.sleep(1); st.rerun()

# --- MAIN DASHBOARD ---
st.markdown("<div class='main-header'>Tax Smile Dashboard</div>", unsafe_allow_html=True)

if authenticated:
    tasks_data = fetch_tasks_all()
    df = pd.DataFrame(tasks_data)

    if st.session_state.selected_task is not None:
        task = st.session_state.selected_task
        st.markdown(f"### 📂 Client: {task['client_name']}")
        with st.container():
            st.markdown("<div class='report-card'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.metric("Service", task['work_type'])
            col2.metric("Due Date", task['deadline'])
            col3.metric("Staff", task['assigned_to'])
            st.divider()
            med_1, med_2 = st.columns(2)
            with med_1:
                st.markdown("#### 🎧 Voice Instruction")
                if task.get('audio_url'): st.audio(task['audio_url'])
                else: st.info("No audio.")
            with med_2:
                st.markdown("#### 📄 Documents")
                links = task.get('file_links', [])
                if links:
                    for item in links:
                        st.markdown(f"**{item['name']}**<br><a href='{item['url']}' target='_blank' class='view-pill'>👁️ View</a> <a href='{item['url']}' download class='dl-pill'>📥 Download</a>", unsafe_allow_html=True)
                        st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
                else: st.info("No files.")
            st.divider()
            status_list = ["Pending", "In Progress", "Query Sent", "Query From Admin", "Completed"]
            curr_status = st.selectbox("Status", status_list, index=status_list.index(task['status']) if task['status'] in status_list else 0)
            adm_q = st.text_area("Admin Query", value=task.get('admin_query', '') or "") if is_admin else task.get('admin_query', '')
            stf_n = st.text_area("Staff Note", value=task.get('staff_comment', '') or "")
            b1, b2 = st.columns(2)
            if b1.button("💾 Save Update", use_container_width=True):
                update_task_status(task['id'], curr_status, stf_n, adm_q if is_admin else task.get('admin_query'))
                st.session_state.selected_task = None; st.rerun()
            if b2.button("⬅️ Return", use_container_width=True):
                st.session_state.selected_task = None; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        if is_admin:
            with st.expander("🤖 AI Insights", expanded=True):
                overdue = df[(pd.to_datetime(df['deadline']).dt.date < date.today()) & (df['status'] != 'Completed')]
                if not overdue.empty:
                    st.error(f"⚠️ {len(overdue)} tasks past deadline!")
                    c_b1, c_b2 = st.columns(2)
                    if c_b1.button("🔍 View Overdue", use_container_width=True): st.session_state.filter_overdue = True; st.rerun()
                    if c_b2.button("📋 Show All", use_container_width=True): st.session_state.filter_overdue = False; st.rerun()
                else: st.success("All tasks on track!")

        f_df = df.copy()
        if not is_admin: f_df = f_df[(f_df['assigned_to'] == current_user) & (f_df['status'] != 'Completed')]
        if st.session_state.filter_overdue: f_df = f_df[(pd.to_datetime(f_df['deadline']).dt.date < date.today()) & (f_df['status'] != 'Completed')]
        
        f_df['client_name'] = f_df.apply(lambda x: f"🔴 {x['client_name']}" if x['status'] == 'Query From Admin' else (f"✅ {x['client_name']}" if x['status'] == 'Completed' else x['client_name']), axis=1)
        
        st.subheader("📌 Task Repository")
        grid = st.dataframe(f_df[['client_name', 'work_type', 'deadline', 'assigned_to', 'status']] if is_admin else f_df[['client_name', 'work_type', 'deadline', 'status']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        
        if grid.selection.rows:
            st.session_state.selected_task = f_df.iloc[grid.selection.rows[0]].to_dict()
            st.rerun()
else:
    st.info("👋 Login from sidebar.")

st.divider()
st.caption(f"Tax Smile Management Suite | {datetime.now().strftime('%B %Y')}")
    
