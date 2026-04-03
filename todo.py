import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# 1. Page Config
st.set_page_config(page_title="Tax Smile ToDo", page_icon="📝", layout="wide")

# 2. Supabase Connection
SUPABASE_URL = "https://bpthxlzljselcdqvmwjc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwdGh4bHpsanNlbGNkcXZtd2pjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4MzA3MzEsImV4cCI6MjA5MDQwNjczMX0.jSpfNfyNwtwMJhQ-lxyBBkQx24iI9JpnU5V75e7iq-I"
ADMIN_PASSWORD = "sajan123"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- CSS: Improved UI, Colors & Progress Bar Visibility ---
st.markdown(
    """
    <style>
    /* Sidebar Background */
    [data-testid="stSidebar"] { background-color: #001f3f !important; }
    
    /* Sidebar Headings */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p {
        color: white !important; font-weight: bold !important;
    }

    /* Selection List & Input Text Colors - Fixing Visibility */
    div[data-baseweb="select"] > div, input, select, textarea {
        background-color: white !important;
        color: black !important;
        -webkit-text-fill-color: black !important;
    }
    
    /* Dropdown Items Visibility */
    div[role="listbox"] ul li {
        background-color: white !important;
        color: black !important;
    }

    /* Readable Alert/Message Box */
    .stAlert {
        background-color: #ffffff !important;
        color: black !important;
        border: 1px solid #2c3e50;
    }

    .detail-box { 
        background-color: #ffffff; padding: 25px; border-radius: 12px; 
        border: 1px solid #ddd; color: black; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    }
    
    .stButton>button { background-color: #2c3e50; color: white !important; width: 100%; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Functions ---
def fetch_staff():
    try:
        res = supabase.table("staff").select("staff_name").order("staff_name").execute()
        return [item['staff_name'] for item in res.data] if res.data else ["Sajan"]
    except: return ["Sajan"]

def fetch_clients():
    try:
        res = supabase.table("tasks").select("client_name").execute()
        return sorted(list(set([item['client_name'] for item in res.data if item['client_name']])))
    except: return []

def fetch_tasks():
    try:
        res = supabase.table("tasks").select("*").in_("status", ["Pending", "Inactive"]).order("deadline", desc=False).execute()
        return res.data
    except: return []

# --- Session State ---
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

# --- SIDEBAR: LOGIN ---
st.sidebar.header("🔐 User Login")
staff_list = fetch_staff()
current_user = st.sidebar.selectbox("Select Name", ["-- Select --"] + staff_list)

is_admin = False
if current_user != "-- Select --":
    pwd = st.sidebar.text_input("Password", type="password")
    if pwd == ADMIN_PASSWORD:
        is_admin = True

# --- ADMIN Actions (SIDEBAR) ---
if is_admin and st.session_state.selected_task is None:
    with st.sidebar.expander("📤 Rare: Bulk Import"):
        up_excel = st.file_uploader("Upload Excel", type=["xlsx"])
        if up_excel and st.button("Save Now"):
            df = pd.read_excel(up_excel)
            for n in df['client_name']:
                supabase.table("tasks").insert({"client_name": str(n).strip(), "status": "System"}).execute()
            st.success("Clients Saved!"); st.rerun()

    st.sidebar.header("🚀 Assign Task")
    clients = fetch_clients()
    
    # Form clear_on_submit allows resetting fields after task creation
    with st.sidebar.form("task_form", clear_on_submit=True):
        c_sel = st.selectbox("Client", ["-- New --"] + clients)
        c_new = st.text_input("OR New Name")
        work = st.selectbox("Work", ["GST", "IT", "Audit", "Consultation", "Other"])
        stf = st.selectbox("Staff", staff_list)
        due = st.date_input("Deadline")
        
        st.write("📁 Media Section")
        files = st.file_uploader("Attach Files", accept_multiple_files=True)
        audio = st.audio_input("Voice Instruction")
        
        if st.form_submit_button("🚀 Assign Task"):
            final_c = c_new if c_new else (c_sel if c_sel != "-- New --" else "")
            
            if final_c:
                # 1. Multiple Task Avoidance Check
                existing_tasks = fetch_tasks()
                is_duplicate = any(t['client_name'] == final_c and t['work_type'] == work and t['status'] == 'Pending' for t in existing_tasks)
                
                if is_duplicate:
                    st.error(f"❌ '{work}' for '{final_c}' is already pending!")
                else:
                    # 2. Progress Bar Visibility
                    prog_bar = st.sidebar.progress(0, text="Saving Task...")
                    for i in range(1, 101):
                        time.sleep(0.01)
                        prog_bar.progress(i)
                    
                    supabase.table("tasks").insert({
                        "client_name": final_c, "work_type": work, 
                        "assigned_to": stf, "deadline": str(due), "status": "Pending"
                    }).execute()
                    
                    st.sidebar.success(f"✅ Success! Task for {final_client if 'final_client' in locals() else final_c} assigned.")
                    st.balloons()
                    st.rerun()
            else:
                st.error("Please provide a client name")

# --- MAIN PAGE ---
if st.session_state.selected_task is not None:
    task = st.session_state.selected_task
    st.markdown(f"""
    <div class="detail-box">
        <h1 style='color: #2c3e50;'>👤 {task['client_name']}</h1>
        <hr>
        <p><b>📌 Work:</b> {task['work_type']} | <b>📅 Due:</b> {task['deadline']} | <b>👨‍💼 Staff:</b> {task['assigned_to']}</p>
        <br>
        <h3>📂 Saved Documents</h3>
        <p style='color: grey;'>Media files will be listed here.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.selected_task = None
        st.rerun()

else:
    st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📝 Tax Smile Dashboard</h1>", unsafe_allow_html=True)
    if current_user != "-- Select --":
        tasks = fetch_tasks()
        if tasks:
            df = pd.DataFrame(tasks)
            view_df = df if is_admin else df[df['assigned_to'] == current_user]
            
            if not view_df.empty:
                st.subheader(f"📌 Task Table: {current_user}")
                sel = st.dataframe(
                    view_df[['client_name', 'work_type', 'deadline', 'assigned_to', 'status']],
                    use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row"
                )
                if sel.selection.rows:
                    st.session_state.selected_task = view_df.iloc[sel.selection.rows[0]]
                    st.rerun()

st.divider()
st.caption(f"Tax Smile ToDo | {datetime.now().strftime('%d/%m/%Y')}")
