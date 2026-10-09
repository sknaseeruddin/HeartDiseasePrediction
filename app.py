
import hashlib
import hmac
import json
import pickle
import secrets
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st


# ==================================================
# 1. CONFIGURATION AND DESIGN
# ==================================================

st.set_page_config(
    page_title="HeartCare | Health Dashboard",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "heartcare.db"
MODEL_PATH = BASE_DIR / "heart_model.pkl"

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef5ff 0%, #f6f1ff 100%);
    color: #24324a;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1250px;
}

h1, h2, h3 {
    color: #203864 !important;
}

p, label {
    color: #34445d;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #172554 0%, #3730a3 100%);
}

[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #dce6f5;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 5px 18px rgba(31, 56, 100, 0.06);
}

[data-testid="stMetricLabel"] {
    color: #64748b !important;
}

[data-testid="stMetricValue"] {
    color: #203864 !important;
}

div.stButton > button,
div.stFormSubmitButton > button {
    background: linear-gradient(90deg, #2563eb, #6366f1);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.65rem 1rem;
    font-weight: 700;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background: linear-gradient(90deg, #1d4ed8, #4f46e5);
    color: white;
    border: none;
}

div[data-baseweb="input"] input {
    background-color: white;
    color: #24324a;
    border-radius: 8px;
}

div[data-baseweb="select"] > div {
    background-color: white;
    border-radius: 8px;
}

div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #dce6f5;
    border-radius: 16px;
    padding: 20px;
}

.stAlert {
    border-radius: 12px;
}

hr {
    border-color: #dce6f5;
}

[data-testid="stDataFrame"] {
    border: 1px solid #dce6f5;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# 2. DATABASE
# ==================================================

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                check_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                inputs TEXT NOT NULL,
                prediction INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


initialize_database()


# ==================================================
# 3. REGISTRATION AND LOGIN
# ==================================================

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200000
    ).hex()


def register_user(username, password):
    username = username.strip().lower()

    if not 3 <= len(username) <= 30:
        return False, "Username must contain 3–30 characters."

    if not all(c.isalnum() or c in "_-" for c in username):
        return False, "Use only letters, numbers, underscores or hyphens."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    salt = secrets.token_bytes(16).hex()
    password_hash = hash_password(password, salt)

    try:
        with connect_db() as conn:
            conn.execute("""
                INSERT INTO users
                (username, salt, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                salt,
                password_hash,
                datetime.now().isoformat(timespec="seconds")
            ))

        return True, "Account created successfully! Please log in."

    except sqlite3.IntegrityError:
        return False, "This username already exists. Choose another."


def authenticate_user(username, password):
    with connect_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username.strip().lower(),)
        ).fetchone()

    if user is None:
        return None

    entered_hash = hash_password(password, user["salt"])

    if hmac.compare_digest(entered_hash, user["password_hash"]):
        return {
            "id": user["id"],
            "username": user["username"]
        }

    return None


# ==================================================
# 4. LOAD TRAINED MODEL
# ==================================================

@st.cache_resource
def load_model():
    with open(MODEL_PATH, "rb") as file:
        return pickle.load(file)


try:
    model = load_model()
except FileNotFoundError:
    st.error(
        "Model file not found. Make sure heart_model.pkl "
        "is in your project folder."
    )
    st.stop()
except Exception as exc:
    st.error(f"Could not load the model: {exc}")
    st.stop()


# ==================================================
# 5. SESSION STATE
# ==================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None


# ==================================================
# 6. REGISTRATION AND LOGIN PAGE
# ==================================================

def show_auth_page():
    st.markdown("# ❤️ HeartCare")
    st.markdown("### Your Personal Health Tracking Dashboard")
    st.write(
        "Create your account to manage your saved project "
        "check-ins and review your entry history."
    )

    st.info(
        "Educational project only. This model cannot diagnose "
        "heart disease. Use fictional data for demonstrations."
    )

    # Registration is deliberately the first tab.
    tab_register, tab_login = st.tabs([
        "📝 Create Account",
        "🔐 Login"
    ])

    with tab_register:
        st.subheader("Create your account")
        st.write("Register once, then use the same credentials to log in.")

        with st.form("register_form"):
            new_username = st.text_input(
                "Choose a username",
                placeholder="e.g. heartcare_user"
            )

            new_password = st.text_input(
                "Create password",
                type="password",
                help="Use at least 8 characters."
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            register_clicked = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

        if register_clicked:
            if not new_username or not new_password or not confirm_password:
                st.error("Please complete all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = register_user(
                    new_username, new_password
                )

                if success:
                    st.success(message)
                    st.info("Now open the Login tab.")
                else:
                    st.error(message)

    with tab_login:
        st.subheader("Welcome back")
        st.write("Enter the credentials you used during registration.")

        with st.form("login_form"):
            login_username = st.text_input(
                "Username",
                key="login_username",
                placeholder="Your username"
            )

            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            login_clicked = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if login_clicked:
            if not login_username or not login_password:
                st.error("Enter your username and password.")
            else:
                user = authenticate_user(
                    login_username, login_password
                )

                if user:
                    st.session_state.user = user
                    st.session_state.last_prediction = None
                    st.rerun()
                else:
                    st.error(
                        "Invalid username or password. "
                        "Register first or check your credentials."
                    )


# ==================================================
# 7. GET AND SAVE USER RECORDS
# ==================================================

def get_user_records(user_id):
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT id, check_date, created_at, inputs, prediction
            FROM records
            WHERE user_id = ?
            ORDER BY check_date DESC, id DESC
        """, (user_id,)).fetchall()

    return [dict(row) for row in rows]


def save_record(user_id, check_date, input_values, prediction):
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO records
            (user_id, check_date, created_at, inputs, prediction)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            check_date.isoformat(),
            datetime.now().isoformat(timespec="seconds"),
            json.dumps(input_values),
            prediction
        ))


# ==================================================
# 8. DAILY CHECK-IN
# ==================================================

def show_health_check():
    st.title("🩺 Daily Check-in")
    st.write(
        "Enter sample measurements for your project. "
        "A new entry will be saved to your account."
    )

    with st.form("health_form"):
        check_date = st.date_input(
            "Check-in date",
            value=date.today()
        )

        st.subheader("Personal Information")
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input(
                "Age",
                min_value=1,
                max_value=120,
                value=45
            )

        with col2:
            sex = st.selectbox(
                "Sex (dataset coding)",
                [1, 0],
                format_func=lambda x:
                    "Male (1)" if x == 1 else "Female (0)"
            )

        st.subheader("Health Measurements")
        col1, col2, col3 = st.columns(3)

        with col1:
            cp = st.selectbox("Chest pain type (cp)", [0, 1, 2, 3])
            trestbps = st.number_input(
                "Resting blood pressure",
                min_value=50,
                max_value=250,
                value=120
            )
            chol = st.number_input(
                "Cholesterol",
                min_value=50,
                max_value=600,
                value=200
            )
            fbs = st.selectbox("Fasting blood sugar (fbs)", [0, 1])

        with col2:
            restecg = st.selectbox("Resting ECG (restecg)", [0, 1, 2])
            thalach = st.number_input(
                "Maximum heart rate",
                min_value=50,
                max_value=250,
                value=150
            )
            exang = st.selectbox(
                "Exercise-induced angina (exang)", [0, 1]
            )
            oldpeak = st.number_input(
                "Oldpeak",
                min_value=0.0,
                max_value=10.0,
                value=1.0,
                step=0.1
            )

        with col3:
            slope = st.selectbox("Slope", [0, 1, 2])
            ca = st.selectbox("Major vessels (ca)", [0, 1, 2, 3, 4])
            thal = st.selectbox("Thal", [0, 1, 2, 3])

        submitted = st.form_submit_button(
            "🔍 Predict and Save Check-in",
            use_container_width=True
        )

    if submitted:
        input_values = {
            "age": age,
            "sex": sex,
            "cp": cp,
            "trestbps": trestbps,
            "chol": chol,
            "fbs": fbs,
            "restecg": restecg,
            "thalach": thalach,
            "exang": exang,
            "oldpeak": oldpeak,
            "slope": slope,
            "ca": ca,
            "thal": thal
        }

        try:
            input_data = pd.DataFrame([input_values])
            input_data = input_data[model.feature_names_in_]
            prediction = int(model.predict(input_data)[0])

            save_record(
                st.session_state.user["id"],
                check_date,
                input_values,
                prediction
            )

            st.session_state.last_prediction = prediction
            st.success("Your check-in was saved successfully!")

        except Exception as exc:
            st.error(f"Could not complete the check-in: {exc}")

    prediction = st.session_state.last_prediction

    if prediction is not None:
        st.subheader("Prediction Summary")

        if prediction == 1:
            st.warning(
                "Class 1: labelled as heart disease in this dataset."
            )
        else:
            st.success(
                "Class 0: labelled as no heart disease in this dataset."
            )

        st.caption(
            "This dataset-based result is not a medical diagnosis "
            "and must not be used to make healthcare decisions."
        )


# ==================================================
# 9. PERSONAL DASHBOARD
# ==================================================

def show_dashboard():
    user = st.session_state.user
    records = get_user_records(user["id"])

    st.title(f"Welcome, {user['username']}! 👋")
    st.write("Your personal project tracking overview.")

    today_records = [
        record for record in records
        if record["check_date"] == date.today().isoformat()
    ]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Check-ins", len(records))

    with col2:
        st.metric("Today's Entries", len(today_records))

    with col3:
        st.metric(
            "Days with Entries",
            len(set(record["check_date"] for record in records))
        )

    st.divider()
    st.subheader("Recent Activity")

    if not records:
        st.info(
            "No entries yet. Open Daily Check-in to save your "
            "first sample record."
        )
    else:
        recent = pd.DataFrame([
            {
                "Date": record["check_date"],
                "Model Class": record["prediction"],
                "Saved At": record["created_at"]
            }
            for record in records[:10]
        ])

        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True
        )

    st.info(
        "This dashboard counts saved records. A model prediction "
        "is not a reliable measure of changes in your health."
    )


# ==================================================
# 10. HISTORY PAGE
# ==================================================

def show_history():
    st.title("📅 Check-in History")

    records = get_user_records(st.session_state.user["id"])

    if not records:
        st.info("No saved entries yet. Create a daily check-in first.")
        return

    history = pd.DataFrame([
        {
            "Date": record["check_date"],
            "Saved At": record["created_at"],
            "Model Class": record["prediction"]
        }
        for record in records
    ])

    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("View Record Details")

    selected_index = st.selectbox(
        "Choose a saved record",
        options=list(range(len(records))),
        format_func=lambda i: (
            f"{records[i]['check_date']} — "
            f"Record {records[i]['id']}"
        )
    )

    selected = records[selected_index]

    st.json(json.loads(selected["inputs"]))

    st.caption(
        "Saved entries are for project demonstration and "
        "record review, not medical interpretation."
    )


# ==================================================
# 11. MAIN APPLICATION
# ==================================================

if st.session_state.user is None:
    show_auth_page()

else:
    with st.sidebar:
        st.title("❤️ HeartCare")
        st.caption("Personal Tracking Dashboard")
        st.divider()

        st.write(f"Logged in as **{st.session_state.user['username']}**")

        page = st.radio(
            "Navigation",
            ["Dashboard", "Daily Check-in", "History"]
        )

        st.divider()

        st.caption("Educational ML project")

        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.last_prediction = None
            st.rerun()

    if page == "Dashboard":
        show_dashboard()
    elif page == "Daily Check-in":
        show_health_check()
    elif page == "History":
        show_history()
