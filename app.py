import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import urllib.request
from io import StringIO

# ======================================
# 0) USTAWIENIA STRONY
# ======================================
st.set_page_config(page_title="MIASTECZKA", page_icon="🎯", layout="wide")

# ======================================
# 1) AUTORYZACJA DO GOOGLE SHEETS
# ======================================
@st.cache_resource
def get_sheet():
    """Autoryzacja i połączenie z Google Sheets"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)

    # 🔑 Wklej tu swoje ID arkusza (z adresu pomiędzy /d/ a /edit)
    SHEET_ID = "TWÓJ_ID_ARKUSZA_TUTAJ"
    sheet = client.open_by_key(SHEET_ID).sheet1

    # Jeśli arkusz jest pusty, dodaj nagłówki
    existing = sheet.get_all_values()
    if not existing:
        headers = ["user", "miasto", "komentarz", "ocena", "updated_at"]
        sheet.append_row(headers)
    return sheet

sheet = get_sheet()

# ======================================
# 2) FUNKCJE OBSŁUGI DANYCH
# ======================================
def load_data():
    """Pobierz wszystkie dane z arkusza do DataFrame"""
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def save_comment(user, miasto, komentarz, ocena):
    """Zapisz lub nadpisz wpis użytkownika (działa jak UPSERT)"""
    ts = datetime.utcnow().isoformat()
    df = load_data()

    if df.empty:
        new_row = pd.DataFrame([[user, miasto, komentarz, ocena, ts]],
                               columns=["user", "miasto", "komentarz", "ocena", "updated_at"])
        sheet.append_row(new_row.values.tolist()[0])
        return

    mask = (df["user"] == user) & (df["miasto"] == miasto)
    if mask.any():
        df.loc[mask, ["komentarz", "ocena", "updated_at"]] = [komentarz, ocena, ts]
    else:
        new_row = pd.DataFrame([[user, miasto, komentarz, ocena, ts]],
                               columns=["user", "miasto", "komentarz", "ocena", "updated_at"])
        df = pd.concat([df, new_row], ignore_index=True)

    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

def read_city_entries(miasto):
    """Zwróć wpisy dotyczące konkretnego miasta"""
    df = load_data()
    if df.empty:
        return pd.DataFrame(columns=["Użytkownik", "Ocena", "Komentarz"])
    df_city = df[df["miasto"] == miasto]
    return df_city.rename(columns={"user": "Użytkownik", "ocena": "Ocena", "komentarz": "Komentarz"})

def read_all_grades():
    """Zwróć wszystkie oceny"""
    df = load_data()
    if df.empty:
        return pd.DataFrame(columns=["miasto", "ocena"])
    return df[df["ocena"].notna()][["miasto", "ocena"]]

# ======================================
# 3) MAPOWANIE OCEN
# ======================================
OCENY_DOZW = ["F","D","C","B","A","S", "-brak-"]
LIT_TO_NUM_GLOBAL = {
    "F-":0.5,"F":1.0,"F+":1.5,
    "D-":2.25,"D":2.5,"D+":2.75,
    "C-":3.25,"C":3.5,"C+":3.75,
    "B-":4.0,"B":4.25,"B+":4.5,
    "A-":4.75,"A":5.0,"A+":5.25,
    "S-":5.5,"S":6.0
}
def num_to_band(x):
    for k,v in sorted(LIT_TO_NUM_GLOBAL.items(), key=lambda kv: kv[1], reverse=True):
        if x>=v: return k
    return "F-"

# ======================================
# 4) STYL APLIKACJI
# ======================================
st.markdown("""
<style>
.stApp {background-color: #1e1e1e; color: #f8fafc !important;}
h1, h2, h3, label, p {color: #f8fafc !important;}
section[data-testid="stSidebar"] {background-color: #2a2a2a !important; color: #f8fafc !important;}
div[data-testid="stButton"] > button {
    background-color: #3b82f6 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6em 1.2em !important;
    font-size: 15px !important;
    transition: all 0.15s ease-in-out;
}
div[data-testid="stButton"] > button:hover {
    background-color: #2563eb !important;
    transform: scale(1.03);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# ======================================
# 5) DANE: miasta z Wikipedii
# ======================================
@st.cache_data(show_spinner=True)
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

# ======================================
# 6) PANEL BOCZNY
# ======================================
with st.sidebar:
    st.markdown("## 📍 Nawigacja")

    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🏠 Strona główna"):
            st.session_state["go_home"] = True
    with col_nav2:
        if st.button("📚 Tierlista"):
            st.session_state["go_tierlist"] = True

    st.markdown("---")
    st.header("👤 Twoje dane")
    default_user = st.session_state.get("user", "")
    user = st.text_input("Podaj swoją nazwę użytkownika (klucz):", value=default_user)
    st.session_state["user"] = user

if st.session_state.get("go_home", False):
    st.session_state["go_home"] = False
    st.session_state.pop("miasto", None)
    st.session_state.pop("kom", None)
    st.session_state.pop("grade", None)
    st.rerun()

if st.session_state.get("go_tierlist", False):
    st.session_state["go_tierlist"] = False
    st.switch_page("pages/tierlista.py")

# ======================================
# 7) EKRAN STARTOWY
# ======================================
if not user:
    st.markdown("<h3 style='text-align:center; margin-top:20vh;'>👋 Witaj!<br>Wpisz nazwę użytkownika w panelu bocznym, aby rozpocząć.</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align:center;'>🎯 Losuj polskie miasta</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Wybierz typ miasta, które chcesz odkryć</p>", unsafe_allow_html=True)
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🏡 Losuj małe miasto (≤ 50 000)", key="male_btn"):
            male = miasta[miasta["Ludność"].notna() & (miasta["Ludność"] <= 50_000)]
            if not male.empty:
                st.session_state["miasto"] = male.sample(1)["Miasto"].iloc[0]
    with colB:
        if st.button("🌆 Losuj duże miasto (> 50 000)", key="duze_btn"):
            duze = miasta[miasta["Ludność"].notna() & (miasta["Ludność"] > 50_000)]
            if not duze.empty:
                st.session_state["miasto"] = duze.sample(1)["Miasto"].iloc[0]

# ======================================
# 8) PANEL MIASTA
# ======================================
if "miasto" in st.session_state:
    miasto = st.session_state["miasto"]
    st.subheader(f"🎯 Wylosowano: **{miasto}**")
    link = f"https://www.google.com/maps/search/?api=1&query={miasto.replace(' ', '+')}"
    st.markdown(f"[🗺️ Otwórz w Google Maps]({link})")

    st.markdown(f"""
        <iframe 
            src="https://www.google.com/maps?q={miasto.replace(' ', '+')}&output=embed" 
            width="100%" height="400" style="border-radius:12px; border:1px solid #ccc;">
        </iframe>
    """, unsafe_allow_html=True)

    st.write("---")
    st.markdown("### 💬 Dodaj komentarz i ocenę literową")
    komentarz = st.text_area("Komentarz (opcjonalnie):", key="kom")
    ocena = st.selectbox("Ocena (F…S):", OCENY_DOZW, index=0, placeholder="Wybierz ocenę", key="grade")

    if st.button("💾 Zapisz / nadpisz"):
        if komentarz or ocena:
            save_comment(user, miasto, komentarz or None, ocena or None)
            st.success("Zapisano (UPSERT).")
        else:
            st.warning("Podaj komentarz lub ocenę (przynajmniej jedno).")

    st.write("---")
    st.markdown("### 🧾 Zestawienie ocen użytkowników — tylko to miasto")
    df_city = read_city_entries(miasto)
    if not df_city.empty:
        df_city = df_city[df_city["Ocena"].notna() & (df_city["Ocena"] != "-brak-")]
        st.dataframe(df_city, use_container_width=True)
    else:
        st.info("Brak wpisów dla tego miasta.")

# ======================================
# 9) RANKING
# ======================================
st.write("---")
st.header("🏆 Ultimate ranking małych miast 🏆")

df_all = read_all_grades()
if df_all.empty:
    st.info("Brak ocen w bazie – dodaj pierwsze wpisy, aby zobaczyć ranking.")
else:
    df_all = df_all.merge(miasta[["Miasto","Ludność"]], left_on="miasto", right_on="Miasto", how="left")
    df_all = df_all[df_all["Ludność"].notna() & (df_all["Ludność"] <= 50_000)].copy()

    if df_all.empty:
        st.info("Brak ocen dla małych miast.")
    else:
        df_all["ocena_num"] = df_all["ocena"].map(LIT_TO_NUM_GLOBAL)
        df_all = df_all.dropna(subset=["ocena_num"])

        summary = (
            df_all.groupby("miasto")
            .agg(Średnia=("ocena_num","mean"), Liczba_ocen=("ocena_num","count"))
            .reset_index()
        )

        C = summary["Średnia"].mean() if not summary.empty else 0
        m = summary["Liczba_ocen"].quantile(0.5) if not summary.empty else 1
        summary["Ważony_wynik"] = (
            (summary["Liczba_ocen"] / (summary["Liczba_ocen"] + m)) * summary["Średnia"]
            + (m / (summary["Liczba_ocen"] + m)) * C
        )
        summary["Ocena końcowa"] = summary["Średnia"].apply(num_to_band)
        summary = summary.sort_values(["Ważony_wynik", "Liczba_ocen"], ascending=[False, False])

        st.dataframe(
            summary[["miasto","Ocena końcowa","Liczba_ocen"]]
            .rename(columns={"miasto":"Miasto"}),
            use_container_width=True,
        )

# ======================================
# 10) WYSZUKIWARKA
# ======================================
st.write("---")
st.markdown("### 🔍 Wyszukaj konkretne miasto")
search_city = st.text_input("Wpisz nazwę miasta, aby otworzyć jego stronę:", placeholder="np. Zamość", key="search_city")
if st.button("🔎 Przejdź do miasta", use_container_width=True):
    if not search_city:
        st.warning("Wpisz nazwę miasta, aby kontynuować.")
    else:
        search_clean = search_city.strip().lower()
        miasta_lower = miasta["Miasto"].str.lower()
        matches = miasta[miasta_lower == search_clean]
        if not matches.empty:
            st.session_state["miasto"] = matches.iloc[0]["Miasto"]
            st.session_state["go_to_city_trigger"] = True
        else:
            st.error(f"Nie znaleziono miasta o nazwie „{search_city}”. Spróbuj innej pisowni.")

if st.session_state.get("go_to_city_trigger", False):
    st.session_state["go_to_city_trigger"] = False
    st.rerun()
