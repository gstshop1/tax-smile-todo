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

# Passwords
ADMIN_PASSWORD = "sajan123"
STAFF_PASSWORD = "sajan12"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- CSS Styling (Corrected Sidebar Text to Black) ---
st.markdown(
    """
    <style>
    /* Sidebar styling with black text */
    [data-testid="stSidebar"] { 
        background-color: #f0f2f6 !important; 
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p {
        color: #000000 !important; 
        font-weight: bold !important;
    }
    .stButton>button { 
        background-color: #3498db; 
        color: white !important; 
        width: 100%; 
        font-weight: bold; 
        border-radius: 8px; 
    }
    .filter-container { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        border: 1px solid #d1d3d4; 
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

def upload_to_storage(file, folder, client):
    try:
        clean_name = "".join(x for x in client if x.isalnum())
        file_ext = file.name.split('.')[-1]
        file_path = f"{folder}/{clean_name}_{int(time.time())}.{file_ext}"
        supabase.storage.from_("media").upload(path=file_path, file=file.getvalue(), file_options={"content-type": file.type})
        return f"{SUPABASE_URL}/storage/v1/object/public/media/{file_path}"
    except: return None

def update_task_status(task_id, new_status, staff_comment, admin_query):
    try:
        supabase.table("tasks").update({
            "status": new_status, 
            "staff_comment": staff_comment,
            "admin_query": admin_query
        }).eq("id", task_id).execute()
        return True
    except: return False

# --- Session State ---
if "selected_task" not in st.session_state: st.session_state.selected_task = None
if "last_user" not in st.session_state: st.session_state.last_user = None

# --- SIDEBAR: LOGIN & ASSIGN TASK ---
st.sidebar.header("🔐 User Login")
staff_list = fetch_staff()
current_user = st.sidebar.selectbox("Select Your Name", ["-- Select Name --"] + staff_list)

if st.session_state.last_user != current_user:
    st.session_state.last_user = current_user
    st.session_state.selected_task = None
    st.rerun()

authenticated = False
is_admin = False

if current_user != "-- Select Name --":
    pwd_input = st.sidebar.text_input("Enter Password", type="password", key=f"pwd_{current_user}")
    if current_user == "Sajan" and pwd_input == ADMIN_PASSWORD:
        authenticated, is_admin = True, True
    elif pwd_input == STAFF_PASSWORD:
        authenticated = True

# --- ADMIN ONLY: ASSIGN WORK SECTION ---
if authenticated and is_admin and st.session_state.selected_task is None:
    st.sidebar.divider()
    st.sidebar.header("🚀 Assign New Work")
    clients = fetch_clients()
    with st.sidebar.form("assign_form", clear_on_submit=True):
        c_sel = st.selectbox("Search Client", ["-- New --"] + clients)
        c_new = st.text_input("OR New Client Name")
        work = st.selectbox("Work Type", ["GST", "IT", "Audit", "Consultation", "Other"])
        stf = st.selectbox("Assign To", staff_list)
        due = st.date_input("Deadline")
        up_file = st.file_uploader("Attach Document", type=["pdf", "jpg", "xlsx"])
        up_audio = st.audio_input("Record Instruction")
        
        if st.form_submit_button("Assign Task Now"):
            final_c = c_new if c_new else (c_sel if c_sel != "-- New --" else "")
            if final_c:
                f_url = upload_to_storage(up_file, "docs", final_c) if up_file else None
                a_url = upload_to_storage(up_audio, "audio", final_c) if up_audio else None
                supabase.table("tasks").insert({
                    "client_name": final_c, "work_type": work, "assigned_to": stf, 
                    "deadline": str(due), "status": "Pending", "file_url": f_url, "audio_url": a_url
                }).execute()
                st.sidebar.success("✅ Work Assigned!"); time.sleep(1); st.rerun()

# --- MAIN CONTENT ---
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📝 Tax Smile Dashboard</h1>", unsafe_allow_html=True)

if authenticated:
    if st.session_state.selected_task is not None:
        # --- REPORT BOX WINDOW (FULL SCREEN VIEW) ---
        task = st.session_state.selected_task
        st.markdown(f"## 📋 Work Report: {task['client_name']}")
        
        with st.container(border=True):
            i1, i2, i3 = st.columns(3)
            with i1: st.write(f"**📌 Work:** {task['work_type']}")
            with i2: st.write(f"**📅 Deadline:** {task['deadline']}")
            with i3: st.write(f"**👨‍💼 Staff:** {task['assigned_to']}")

            st.divider()
            m1, m2 = st.columns(2)
            with m1:
                if task.get('audio_url'): st.audio(task['audio_url'])
            with m2:
                if task.get('file_url'): st.link_button("📄 Open Document", task['file_url'], use_container_width=True)

            st.divider()
            q1, q2 = st.columns(2)
            with q1:
                if task.get('admin_query'): st.error(f"⚠️ **Admin Query:**\n{task['admin_query']}")
            with q2:
                if task.get('staff_comment'): st.info(f"💬 **Staff Note:**\n{task['staff_comment']}")

            st.divider()
            st.subheader("⚙️ Update Progress")
            status_options = ["Pending", "In Progress", "Query Sent", "Query From Admin", "Completed"]
            try: curr_idx = status_options.index(task['status'])
            except: curr_idx = 0
            new_status = st.selectbox("Current Status", status_options, index=curr_idx)
            
            if is_admin:
                a_query = st.text_area("Admin Query", value=task.get('admin_query', '') or "")
                s_note = task.get('staff_comment', '') 
            else:
                s_note = st.text_area("Staff Note / Query", value=task.get('staff_comment', '') or "")
                a_query = task.get('admin_query', '')

            b1, b2 = st.columns(2)
            with b1:
                if st.button("💾 Save & Submit", use_container_width=True):
                    final_status = "Query From Admin" if is_admin and a_query != (task.get('admin_query') or "") else new_status
                    if update_task_status(task['id'], final_status, s_note, a_query):
                        st.success("✅ Updated!"); st.session_state.selected_task = None; time.sleep(1); st.rerun()
            with b2:
                if st.button("⬅️ Back to List", use_container_width=True):
                    st.session_state.selected_task = None; st.rerun()

    else:
        # --- MAIN LIST VIEW WITH FILTERS ---
        tasks_data = fetch_tasks_all()
        if tasks_data:
            df = pd.DataFrame(tasks_data)
            if not is_admin:
                df = df[(df['assigned_to'] == current_user) & (df['status'] != 'Completed')]
            
            if not df.empty:
                # Filter UI
                st.markdown("<div class='filter-container'>🔍 <b>Quick Filter</b></div>", unsafe_allow_html=True)
                f1, f2, f3 = st.columns(3)
                with f1: sel_work = st.selectbox("By Work", ["All"] + sorted(df['work_type'].unique().tolist()))
                with f2: sel_staff = st.selectbox("By Staff", ["All"] + sorted(df['assigned_to'].unique().tolist())) if is_admin else "All"
                with f3: sel_stat = st.selectbox("By Status", ["All"] + sorted(df['status'].unique().tolist()))

                # Apply Filtering
                f_df = df.copy()
                if sel_work != "All": f_df = f_df[f_df['work_type'] == sel_work]
                if sel_staff != "All": f_df = f_df[f_df['assigned_to'] == sel_staff]
                if sel_stat != "All": f_df = f_df[f_df['status'] == sel_stat]

                # Markers
                f_df['client_name'] = f_df.apply(lambda x: f"🔴 {x['client_name']} (Query)" if x['status'] == 'Query From Admin' else (f"✅ {x['client_name']} (Done)" if x['status'] == 'Completed' else x['client_name']), axis=1)
                f_df['deadline'] = pd.to_datetime(f_df['deadline']).dt.strftime('%d-%m-%Y')

                st.subheader(f"📌 Tasks Found: {len(f_df)}")
                cols = ['client_name', 'work_type', 'deadline', 'assigned_to', 'status'] if is_admin else ['client_name', 'work_type', 'deadline', 'status']
                
                sel = st.dataframe(f_df[cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
                
                if sel.selection.rows:
                    idx = sel.selection.rows[0]
                    st.session_state.selected_task = f_df.iloc[idx].to_dict()
                    st.rerun()
else:
    st.info("👈 Please login from the sidebar.")

st.divider()
st.caption(f"Tax Smile ToDo | {datetime.now().strftime('%d/%m/%Y')}")
    
