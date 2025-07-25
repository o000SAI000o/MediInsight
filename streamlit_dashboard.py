import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for Flask apps
import matplotlib.pyplot as plt
import sqlite3
import bcrypt
import random
from email.message import EmailMessage
from fpdf import FPDF
import smtplib

# --- Setup ---
st.set_page_config(page_title="MediInsight", page_icon=":hospital:", layout="wide")
st.title("\U0001F4CA MediInsight Prediction Dashboard")

# --- Theme Toggle ---
with st.sidebar:
    theme = st.radio("🎨 Theme Mode", ["Light", "Dark"], key="theme_mode")

if theme == "Dark":
    dark_css = """
    <style>
    body {
        background-color: #121212;
        color: white;
    }
    .stApp {
        background-color: #121212;
        color: white;
    }
    div[data-testid="stDataFrame"] table {
        color: white;
    }
    </style>
    """
    st.markdown(dark_css, unsafe_allow_html=True)

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'forgot_password' not in st.session_state:
    st.session_state.forgot_password = False

# --- OTP Store (in-memory for demo) ---
OTP_STORE = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg.set_content(f"Your OTP to reset MediInsight password is: {otp}")
    msg['Subject'] = 'MediInsight Password Reset'
    msg['From'] = 'your_email@example.com'
    msg['To'] = to_email

    try:
        with smtplib.SMTP('localhost', 1025) as server:
            server.send_message(msg)
    except Exception as e:
        st.error(f"Email send failed: {e}")

# --- Password Reset ---
if st.session_state.forgot_password:
    st.header("\U0001F501 Reset Password")
    email = st.text_input("Enter your registered email")

    if st.button("Send OTP"):
        otp = generate_otp()
        OTP_STORE[email] = otp
        send_otp_email(email, otp)
        st.success("OTP sent to your email.")

    entered_otp = st.text_input("Enter OTP")
    new_password = st.text_input("New Password", type="password")

    if st.button("Reset Password"):
        if OTP_STORE.get(email) == entered_otp:
            hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            conn = sqlite3.connect("instance/users.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE user SET password = ? WHERE email = ?", (hashed_pw, email))
            conn.commit()
            conn.close()
            st.success("Password updated successfully.")
            st.session_state.forgot_password = False
        else:
            st.error("Invalid OTP")
    st.stop()

# --- Login Panel ---
if not st.session_state.logged_in:
    with st.sidebar.form("login_form"):
        st.subheader("\U0001F510 Secure Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        submitted = st.form_submit_button("Login")

        if submitted:
            try:
                conn = sqlite3.connect('instance/users.db')
                cursor = conn.cursor()
                cursor.execute("SELECT password, is_admin FROM user WHERE username = ?", (username,))
                row = cursor.fetchone()
                conn.close()

                if not row:
                    st.error("\u274C Username not found")
                elif bcrypt.checkpw(password.encode(), row[0].encode()):
                    st.session_state.logged_in = True
                    st.session_state.user = username
                    st.session_state.is_admin = bool(row[1])
                    st.experimental_rerun()
                else:
                    st.error("\u274C Incorrect password")
            except Exception as e:
                st.error("\u26A0\uFE0F Login failed. Contact admin.")
                st.stop()

    if st.sidebar.button("Forgot Password?"):
        st.session_state.forgot_password = True
    st.stop()

# --- Logout ---
with st.sidebar:
    st.success(f"\U0001F464 Logged in as: {st.session_state.user}")
    if st.button("Logout"):
        for key in st.session_state.keys():
            st.session_state[key] = False if isinstance(st.session_state[key], bool) else ""
        st.experimental_rerun()

# --- Load Data ---
conn = sqlite3.connect("instance/users.db")
df = pd.read_sql_query("SELECT * FROM report", conn)
conn.close()

user_df = df if st.session_state.is_admin else df[df['user'] == st.session_state.user]

# --- Filters ---
st.sidebar.title("\U0001F4CB Filter Reports")
model_types = user_df['model_type'].unique().tolist()
selected_model = st.sidebar.selectbox("Select Model Type", options=["All"] + sorted(model_types))
results = user_df['result'].unique().tolist()
selected_result = st.sidebar.selectbox("Select Result", options=["All"] + sorted(results))

filtered_df = user_df.copy()
if selected_model != "All":
    filtered_df = filtered_df[filtered_df['model_type'] == selected_model]
if selected_result != "All":
    filtered_df = filtered_df[filtered_df['result'] == selected_result]

# --- Display Table ---
st.subheader(f"\U0001F4C1 Reports for: {st.session_state.user}")
st.dataframe(filtered_df, use_container_width=True)

# --- Chart ---
st.subheader("\U0001F4C8 Prediction Chart")
if not filtered_df.empty:
    fig, ax = plt.subplots()
    sns.countplot(data=filtered_df, x='model_type', hue='result', ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.warning("No data to show chart.")

# --- Export ---
st.subheader("\U0001F4E5 Export Report")
col1, col2 = st.columns(2)

with col1:
    st.download_button("\U0001F4C3 Export CSV", filtered_df.to_csv(index=False), "report.csv", "text/csv")

with col2:
    if st.button("\U0001F4C4 Export PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for i, row in filtered_df.iterrows():
            pdf.cell(200, 10, txt=f"{row['timestamp']} | {row['model_type']} | {row['result']}", ln=True)
        pdf_path = f"{st.session_state.user}_report.pdf"
        pdf.output(pdf_path)
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_path, mime="application/pdf")

# --- Re-run Demo ---
st.subheader("\U0001F501 Re-run Prediction (Demo)")
if not filtered_df.empty:
    selected_row = st.selectbox("Select a report to re-run", filtered_df.index)
    selected_report = filtered_df.loc[selected_row]

    st.json({
        "Model Type": selected_report["model_type"],
        "Input Data": selected_report["input_data"],
        "Previous Result": selected_report["result"]
    })

    if st.button("Re-run prediction"):
        st.success(f"\u2705 Re-ran model: {selected_report['model_type']}")
        st.info("\U0001F501 (Simulated — integrate ML models here)")
else:
    st.info("No reports available for re-running.")
