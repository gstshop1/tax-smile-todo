import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# 1. പേജ് സെറ്റിംഗുകൾ
st.set_page_config(page_title="Tax Smile ToDo", page_icon="📝", layout="wide")

# 2. സൂപ്പർബേസ് കണക്ഷൻ
SUPABASE_URL = "https://bpthxlzljselcdqvmwjc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwdGh4bHpsanNlbGNkcXZtd2pjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4MzA3MzEsImV4cCI6MjA5MDQwNjczMX0.jSpfNfyNwtwMJhQ-lxyBBkQx24iI9JpnU5V75e7iq-I"
FREEZE_PASSWORD = "sajan123"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- Functions ---
def fetch_staff():
    try:
        res = supabase.table("staff").select("staff_name").order("staff_name").execute()
        return [item['staff_name'] for item in res.data]
    except: return []

def fetch_tasks():
    try:
        response = supabase.table("tasks").select("*").order("deadline", desc=False).execute()
        return response.data
    except: return []

# 3. ടൈറ്റിൽ
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📝 Tax Smile ToDo Planner</h1>", unsafe_allow_html=True)

# --- SIDEBAR (പഴയതുപോലെ തന്നെ) ---
with st.sidebar:
    st.header("📋 Assign New Task")
    client_name = st.text_input("1. Client Name")
    work_type = st.selectbox("2. Work Type", ["GST Filing", "Income Tax", "Audit", "Consultation", "Other"])
    staff_list = fetch_staff()
    selected_staff = st.selectbox("3. Assigned to Staff", ["-- Select Staff --"] + staff_list)
    deadline_date = st.date_input("4. Deadline")
    priority = st.selectbox("5. Priority", ["1 Hour", "Before Noon", "Today", "Calendar"])

    if st.button("🚀 Assign Task"):
        if client_name and selected_staff != "-- Select Staff --":
            task_data = {"client_name": client_name, "work_type": work_type, "deadline": str(deadline_date), "priority": priority, "assigned_to": selected_staff, "status": "Pending", "is_frozen": False}
            supabase.table("tasks").insert(task_data).execute()
            st.success("Task Assigned!"); st.rerun()

# --- MAIN PAGE ---
tasks_data = fetch_tasks()

if not tasks_data:
    st.info("No tasks found.")
else:
    # സെർച്ച്/ഫിൽട്ടർ ലോജിക് ഇവിടെ വേണമെങ്കിൽ ചേർക്കാം
    df = pd.DataFrame(tasks_data)
    df['deadline'] = pd.to_datetime(df['deadline']).dt.strftime('%d/%m/%y')
    df.insert(0, 'Sl No', range(1, len(df) + 1))
    
    df_display = df[['Sl No', 'assigned_to', 'client_name', 'work_type', 'deadline', 'priority', 'status']]
    df_display.columns = ['No', 'Staff', 'Client Name', 'Work Detail', 'Target Date', 'Priority', 'Status']

    # --- COLUMN HEADER STYLING ONLY ---
    # ഇവിടെയാണ് നമ്മൾ ഹെഡറിന് മാത്രം ലൈറ്റ് ബ്ലൂ നിറം നൽകുന്നത്
    def style_header_only(styler):
        styler.set_table_styles([
            {
                'selector': 'th', # 'th' എന്നാൽ Table Header എന്നാണ്
                'props': [
                    ('background-color', 'Red'), # Light Blue Header
                    ('color', '#2c3e50'),           # Dark Blue Text
                    ('font-weight', 'bold'),
                    ('text-align', 'center'),
                    ('border', '1px solid #dee2e6')
                ]
            }
        ])
        return styler

    styled_df = df_display.style.pipe(style_header_only)

    # ടേബിൾ ഡിസ്‌പ്ലേ (Arrow Key Selection സജീവമാണ്)
    selection = st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    selected_rows = selection.selection.rows
    
    # --- FREEZE SECTION ---
    if selected_rows:
        selected_task = tasks_data[selected_rows[0]]
        st.divider()
        st.subheader(f"🔒 Freeze Task: {selected_task['client_name']}")
        col1, col2, col3 = st.columns([2, 1, 1])
        reason = col1.text_input("Reason", key="frz_reason")
        pwd = col2.text_input("Password", type="password", key="frz_pwd")
        if col3.button("Confirm Freeze"):
            if pwd == FREEZE_PASSWORD:
                supabase.table("tasks").update({"is_frozen": True, "freeze_reason": reason, "status": "Inactive"}).eq("id", selected_task['id']).execute()
                st.success("Task Frozen Successfully!"); st.rerun()
            else: st.error("Wrong Password!")

st.divider()
st.caption(f"Tax Smile ToDo | Header Styled | {datetime.now().strftime('%d/%m/%Y %H:%M')}")