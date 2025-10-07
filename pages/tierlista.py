import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import urllib.request
from io import StringIO

# ===============================
# 🧭 KONFIGURACJA STRONY
# ===============================
st.set_page_config(page_title="Tierlista", page_icon="📚", layout="wide")

# ukryj boczne menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# ===============================
# 🎨 STYL GLOBALNY
# ===============================
st.markdown("""
    <style>
        .stApp {
            background-color: #1e1e1e;
            color: #f8fafc !important;
        }
        h1, h2, h3, label, p, div, span {
            color: #f8fafc !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #2a2a2a !important;
            color: #f8fafc !important;
        }
        div[data-testid="stButton"] > button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5em 1em !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #2563eb !important;
            transform: scale(1.03);
        }
        [data-testid="stDataFrame"] button[kind="icon"] {
            background-color: #f9f9f9 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 6px !important;
            padding: 4px !important;
        }
        [data-testid="stDataFrame"] button[kind="icon"] svg {
            fill: #111 !important;
            opacity: 0.9 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ===============================
# 🧭 SIDEBAR
# ===============================
with st.sidebar:
    st.markdown("## 📍 Nawigacja")

    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🏠 Strona główna"):
            st.session_state["go_home"] = True
    with col_nav2:
        st.button("📚 Tierlista", disabled=True)

    st.markdown("---")
    st.header("👤 Twoje dane")
    default_user = st.session_state.get("user", "")
    user = st.text_input("Podaj swoją nazwę użytkownika (klucz):", value=default_user)
    st.session_state["user"] = user

if st.session_state.get("go_home", False):
    st.session_state["go_home"] = False
    for key in ["miasto", "kom", "grade"]:
        st.session_state.pop(key, None)
    st.switch_page("app.py")

if not user:
    st.warning("👉 Wpisz swoją nazwę użytkownika, aby zobaczyć tierlistę.")
    st.stop()

# ===============================
# 🔗 GOOGLE SHEETS BACKEND
# ===============================
@st.cache_resource
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    SHEET_ID = "1lCVAdbq3g7Mmg1XQ3fg4kssBqlJc3xzD3XIOQbIXpbI"  # <-- ten sam co w app.py
    sheet = client.open_by_key(SHEET_ID).sheet1

    existing = sheet.get_all_values()
    if not existing:
        headers = ["user", "miasto", "komentarz", "ocena", "updated_at"]
        sheet.append_row(headers)
    return sheet

sheet = get_sheet()

def load_data():
    df = pd.DataFrame(sheet.get_all_records())
    return df

def read_user_grades(user):
    df = load_data()
    if df.empty:
        return pd.DataFrame(columns=["miasto", "ocena"])
    return df[(df["user"] == user) & df["ocena"].notna()][["miasto", "ocena"]]

# ===============================
# 🏙️ DANE O MIASTACH (Wikipedia)
# ===============================
@st.cache_data(show_spinner=False)
def load_miasta():
    url = "https://pl.wikipedia.org/wiki/Dane_statystyczne_o_miastach_w_Polsce"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req).read().decode("utf-8")
    tables = pd.read_html(StringIO(html))
    df = tables[0].copy()
    df.columns = [c.strip().replace("\xa0", " ") for c in df.columns]
    lud_cols = [c for c in df.columns if "ludno" in c.lower()]
    df.rename(columns={lud_cols[0]: "Ludność"}, inplace=True)
    df["Ludność"] = (
        df["Ludność"].astype(str)
        .str.replace(r"[^0-9]", "", regex=True)
        .replace("", pd.NA)
        .astype("Int64")
    )
    return df[["Miasto", "Ludność"]]

miasta = load_miasta()

# ===============================
# 📚 TIERLISTA UŻYTKOWNIKA
# ===============================
st.title(f"📚 Tierlista użytkownika **{user}**")

df_user = read_user_grades(user)

show_small_only = st.toggle("Pokaż tylko małe miasta (≤ 50 000 mieszkańców)", value=True)
if show_small_only and not df_user.empty:
    df_user = df_user.merge(miasta, left_on="miasto", right_on="Miasto", how="left")
    df_user = df_user[df_user["Ludność"].notna() & (df_user["Ludność"] <= 50_000)]

if df_user.empty:
    st.info("Nie masz jeszcze żadnych ocen. Wróć do strony głównej i oceń kilka miast.")
    st.stop()

# ===============================
# 🧮 PODSUMOWANIE
# ===============================
tiers = ["S", "A", "B", "C", "D", "F"]
grouped = (
    df_user.groupby("ocena")["miasto"]
    .apply(lambda s: ", ".join(sorted(s)))
    .reindex(tiers)
    .reset_index()
    .rename(columns={"ocena": "Ocena", "miasto": "Miasta"})
).fillna("")

summary = df_user["ocena"].value_counts().reindex(tiers).fillna(0).astype(int)
total = summary.sum()

st.markdown("---")
st.markdown("### 🧮 Podsumowanie Twoich ocen")

cols = st.columns(len(tiers))
colors = {"S":"#eab308","A":"#3b82f6","B":"#22c55e","C":"#a855f7","D":"#f97316","F":"#ef4444"}

for i, tier in enumerate(tiers):
    with cols[i]:
        st.markdown(
            f"<div style='text-align:center; font-size:22px; font-weight:700; color:{colors[tier]};'>{tier}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='text-align:center; font-size:16px; color:#f8fafc;'>{summary[tier]} / {total}</div>",
            unsafe_allow_html=True
        )

# ===============================
# 🗂️ TABELA TIERLISTY
# ===============================
st.markdown("---")
st.markdown("### 🎯 Twoja tierlista")
st.dataframe(grouped, use_container_width=True, hide_index=True)

# ===============================
# 🔍 WYSZUKIWARKA
# ===============================
st.markdown("---")
st.markdown("### 🔍 Przejdź do miasta z listy")
selected_city = st.text_input("Wpisz nazwę miasta z Twojej listy:")

if st.button("➡️ Otwórz to miasto"):
    if selected_city.strip() == "":
        st.warning("Podaj nazwę miasta, aby przejść dalej.")
    else:
        st.session_state["miasto"] = selected_city.strip()
        st.switch_page("app.py")
