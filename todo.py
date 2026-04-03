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

# --- CSS Styling ---
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { background-color: #001f3f !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p {
        color: white !important; font-weight: bold !important;
    }
    div[data-baseweb="select"] > div { background-color: white !important; color: black !important; }
    .detail-box { 
        background-color: #f8f9fa; padding: 25px; border-radius: 12px; 
        border: 1px solid #dee2e6; color: black; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    }
    .stButton>button { background-color: #3498db; color: white !important; width: 100%; font-weight: bold; border-radius: 8px; }
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

def fetch_tasks():
    try:
        res = supabase.table("tasks").select("*").in_("status", ["Pending", "Inactive"]).order("deadline", desc=False).execute()
        return res.data
    except: return []

def upload_to_storage(file, folder, client):
    """ഫയൽ അപ്‌ലോഡ് ചെയ്ത് പബ്ലിക് ലിങ്ക് നൽകുന്നു"""
    try:
        # ക്ലയന്റ് പേര് ക്ലീൻ ചെയ്യുന്നു (സ്പേസ് ഒഴിവാക്കാൻ)
        clean_name = "".join(x for x in client if x.isalnum())
        file_ext = file.name.split('.')[-1]
        file_path = f"{folder}/{clean_name}_{int(time.time())}.{file_ext}"
        
        # അപ്‌ലോഡ് ചെയ്യുന്നു
        supabase.storage.from_("media").upload(
            path=file_path,
            file=file.getvalue(),
            file_options={"content-type": file.type}
        )
        # പബ്ലിക് ലിങ്ക് റിട്ടേൺ ചെയ്യുന്നു
        return f"{SUPABASE_URL}/storage/v1/object/public/media/{file_path}"
    except Exception as e:
        st.error(f"❌ Upload Error ({folder}): {e}")
        return None

# --- Session State ---
if "selected_task" not in st.session_state: st.session_state.selected_task = None
if "last_user" not in st.session_state: st.session_state.last_user = None

# --- SIDEBAR: LOGIN ---
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
    elif pwd_input != "":
        st.sidebar.error("❌ Invalid Password")

# --- MAIN CONTENT ---
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📝 Tax Smile Dashboard</h1>", unsafe_allow_html=True)

if authenticated:
    # --- ADMIN Actions ---
    if is_admin and st.session_state.selected_task is None:
        st.sidebar.header("🚀 Assign Task")
        clients = fetch_clients()
        with st.sidebar.form("task_form", clear_on_submit=True):
            c_sel = st.selectbox("Search Client", ["-- New --"] + clients)
            c_new = st.text_input("New Name")
            work = st.selectbox("Work Type", ["GST", "IT", "Audit", "Consultation", "Other"])
            stf = st.selectbox("Assign To", staff_list)
            due = st.date_input("Deadline")
            
            # Media Upload Section
            up_file = st.file_uploader("Attach Document (PDF/JPG)", type=["pdf", "jpg", "xlsx"])
            up_audio = st.audio_input("Record Voice Instruction")
            
            if st.form_submit_button("🚀 Assign Task Now"):
                final_c = c_new if c_new else (c_sel if c_sel != "-- New --" else "")
                if final_c:
                    # ഫയലുകൾ അപ്‌ലോഡ് ചെയ്യുന്നു
                    f_url = upload_to_storage(up_file, "docs", final_c) if up_file else None
                    a_url = upload_to_storage(up_audio, "audio", final_c) if up_audio else None
                    
                    try:
                        supabase.table("tasks").insert({
                            "client_name": final_c, "work_type": work, 
                            "assigned_to": stf, "deadline": str(due), "status": "Pending",
                            "file_url": f_url, "audio_url": a_url
                        }).execute()
                        st.sidebar.success("✅ Saved Successfully!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Database error: {e}")

    # --- DETAIL VIEW ---
    if st.session_state.selected_task is not None:
        task = st.session_state.selected_task
        try:
            f_date = datetime.strptime(task['deadline'], '%Y-%m-%d').strftime('%d-%m-%Y')
        except:
            f_date = task['deadline']

        st.markdown(f"""
        <div class="detail-box">
            <h2 style='color: #2c3e50;'>👤 {task['client_name']}</h2>
            <hr>
            <p style='font-size: 18px;'><b>📌 Work:</b> {task['work_type']} | <b>📅 Deadline:</b> {f_date}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if task.get('file_url'):
                st.subheader("📄 Document")
                st.link_button("👁️ View / Download File", task['file_url'])
            else:
                st.info("No documents attached.")
        
        with col2:
            if task.get('audio_url'):
                st.subheader("🎧 Voice Instruction")
                st.audio(task['audio_url'])
            else:
                st.info("No audio instruction.")

        if st.button("⬅️ Back to Dashboard"):
            st.session_state.selected_task = None
            st.rerun()
            
    else:
        # --- DASHBOARD TABLE ---
        tasks_data = fetch_tasks()
        if tasks_data:
            df = pd.DataFrame(tasks_data)
            view_df = df if is_admin else df[df['assigned_to'] == current_user]
            
            if not view_df.empty:
                disp_df = view_df.copy()
                disp_df['deadline'] = pd.to_datetime(disp_df['deadline']).dt.strftime('%d-%m-%Y')
                
                st.subheader(f"📌 Task Table: {current_user}")
                sel = st.dataframe(
                    disp_df[['client_name', 'work_type', 'deadline', 'assigned_to', 'status']],
                    use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row"
                )
                if sel.selection.rows:
                    st.session_state.selected_task = view_df.iloc[sel.selection.rows[0]].to_dict()
                    st.rerun()
            else:
                st.info(f"Hello {current_user}, no pending tasks.")
else:
    # ലോഗിൻ ഇൻസ്ട്രക്ഷൻ
    if current_user == "-- Select Name --":
        st.warning("👈 Please select your name and login from the sidebar.")
    else:
        st.info("👈 Please enter your password to access the Tax Smile Dashboard.")

st.divider()
st.caption(f"Tax Smile ToDo | {datetime.now().strftime('%d/%m/%Y')}")
