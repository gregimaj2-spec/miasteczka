import streamlit as st
import pandas as pd
import sqlite3
import random
import urllib.request
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="MIASTECZKA", page_icon="🎯", layout="wide")

# === ukryj domyślne menu Streamlit (app / tierlista) ===
st.markdown("""
    <style>
            /* Styl wszystkich guzików w aplikacji */
        div[data-testid="stButton"] > button {
            background-color: #3b82f6 !important;   /* niebieski */
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.6em 1.2em !important;
            font-size: 15px !important;
            transition: all 0.15s ease-in-out;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #2563eb !important;   /* ciemniejszy niebieski */
            transform: scale(1.03);
        }

        .stApp {
            background-color: #1e1e1e;
            color: #f8fafc !important;
        }
        /* 1) Nie malujemy globalnie wszystkich div/span */
        h1, h2, h3, label, p { 
        color: #f8fafc !important;
        }

        /* 2) Wybrana wartość w selectboxie (zamknięty select) */
        div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
        }

        /* Tekst wybranej opcji */
        div[data-baseweb="select"] > div * {
        color: #000000 !important;   /* czarna czcionka */
        font-weight: 700 !important;
        }

        /* (opcjonalnie) placeholder, gdy nic nie wybrano */
        div[data-baseweb="select"] [aria-hidden="true"] {
        color: #6b7280 !important;   /* szary placeholder */
        }
                }
        section[data-testid="stSidebar"] {
            background-color: #2a2a2a !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
            background-color: #374151;
            color: #f1f5f9;
            border: 1px solid #6b7280;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 13px;
            font-weight: 500;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            background-color: #4b5563;
            border-color: #9ca3af;
            transform: scale(1.02);
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
            background-color: #e2e8f0;
            color: #1e3a8a;
            border: 1px solid #94a3b8;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.15s ease-in-out;
        }
        /* === Przywrócenie ciemnego sidebaru === */
        section[data-testid="stSidebar"] {
            background-color: #2a2a2a !important;  /* ciemnoszary, jak wcześniej */
            color: #f8fafc !important;             /* jasny tekst */
        }
            /* Pasek nawigacyjny i puste obszary strony */
        body {
            background-color: #121212 !important;  /* prawie czarny */
        }

        header[data-testid="stHeader"] {
            background-color: #121212 !important;
            color: #f8fafc !important;
        }

        [data-testid="stToolbar"] {
            background-color: #121212 !important;
            color: #f8fafc !important;
        }

        div[data-testid="stDecoration"] {
            background-color: #121212 !important;
        }
        div[data-baseweb="select"] > div {
        color: #000000 !important;           /* bardzo ciemny szary (prawie czarny) */
        background-color: #ffffff !important;
        }

        div[data-baseweb="popover"] {
            background-color: #ffffff !important;
            color: #111827 !important;
        }

        div[data-baseweb="popover"] * {
            color: #111827 !important;
        }
        /* Kolory w selectboxie dla ocen */
        div[data-baseweb="select"] [data-testid="stMarkdownContainer"] {
            color: #00000 !important;
            font-weight: 700;
        }

        /* Po rozwinięciu menu ocen */
        div[data-baseweb="popover"] div[role="option"] {
            font-weight: 700 !important;
        }

        /* Styl poszczególnych opcji po tekście */
        div[role="option"]:has(span:contains("S")) { background-color: #0047AB !important; color: #ffffff !important; }
        div[role="option"]:has(span:contains("A")) { background-color: #007FFF !important; color: #ffffff !important; }
        div[role="option"]:has(span:contains("B")) { background-color: #708238 !important; color: #ffffff !important; }
        div[role="option"]:has(span:contains("C")) { background-color: #FFD700 !important; color: #000000 !important; }
        div[role="option"]:has(span:contains("D")) { background-color: #FF8C00 !important; color: #000000 !important; }
        div[role="option"]:has(span:contains("F")) { background-color: #DC143C !important; color: #ffffff !important; }
        /* === Naprawa białych ikonek w prawym górnym rogu tabeli === */

        /* Kontener z ikonami (Download / Search / Fullscreen) */
        [data-testid="stDataFrame"] button[kind="icon"] {
            background-color: #f9f9f9 !important;     /* jasne tło */
            border: 1px solid #d1d5db !important;     /* delikatna ramka */
            border-radius: 6px !important;
            padding: 4px !important;
        }

        /* Ikonki – ciemne, widoczne */
        [data-testid="stDataFrame"] button[kind="icon"] svg {
            fill: #111 !important;                   /* ciemny grafitowy kolor */
            opacity: 0.9 !important;
        }

        /* Hover – lekkie podświetlenie */
        [data-testid="stDataFrame"] button[kind="icon"]:hover {
            background-color: #e5e7eb !important;
        }

        /* Wyrównanie menu do tła (żeby nie wyglądało jak przyklejone) */
        [data-testid="stDataFrame"] div[role="group"] {
            background-color: transparent !important;
        }
            /* Kolor wybranej opcji w selectboxie (po zamknięciu menu) */
        div[data-baseweb="select"] div[role="button"] {
            color: #000000 !important;      /* czarna czcionka */
            background-color: #ffffff !important;  /* białe tło */
            font-weight: 700 !important;
        
        /* === Naprawa koloru tytułu i podtytułu (po usunięciu globalnego div/span) === */
        .main-title {
            color: #f8fafc !important;   /* jasny tekst */
        }

        .main-subtitle {
            color: #cbd5e1 !important;   /* jaśniejszy szary, czytelny */
        }
    </style>
""", unsafe_allow_html=True)
hide_default_format = """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_default_format, unsafe_allow_html=True)

# =========================
# 1) DANE: miasta z Wikipedii
# =========================
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

# =========================
# 2) BAZA DANYCH
# =========================
def ensure_db():
    with sqlite3.connect("miasta.db") as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS komentarze (
            user TEXT,
            miasto TEXT,
            komentarz TEXT,
            ocena TEXT,
            updated_at TEXT,
            UNIQUE(user, miasto)
        )
        """)
        conn.commit()

ensure_db()

# =========================
# 3) FUNKCJE DB
# =========================
def save_comment(user, miasto, komentarz, ocena):
    ts = datetime.utcnow().isoformat()
    with sqlite3.connect("miasta.db") as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO komentarze (user, miasto, komentarz, ocena, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user, miasto) DO UPDATE SET
            komentarz=excluded.komentarz,
            ocena=excluded.ocena,
            updated_at=excluded.updated_at
        """, (user, miasto, komentarz, ocena, ts))
        conn.commit()

def read_city_entries(miasto):
    with sqlite3.connect("miasta.db") as conn:
        return pd.read_sql_query(
            "SELECT user AS Użytkownik, ocena AS Ocena, komentarz AS Komentarz "
            "FROM komentarze WHERE miasto=? AND (ocena IS NOT NULL OR komentarz IS NOT NULL)",
            conn, params=(miasto,)
        )

def read_user_grades(user):
    with sqlite3.connect("miasta.db") as conn:
        return pd.read_sql_query(
            "SELECT miasto, ocena FROM komentarze WHERE user=? AND ocena IS NOT NULL",
            conn, params=(user,)
        )

def read_all_grades():
    with sqlite3.connect("miasta.db") as conn:
        return pd.read_sql_query("SELECT miasto, ocena FROM komentarze WHERE ocena IS NOT NULL", conn)

# =========================
# 4) MAPOWANIE OCEN
# =========================
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

# =========================
# 5) PANEL BOCZNY
# =========================
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
    # Reset flagi i danych miasta
    st.session_state["go_home"] = False
    st.session_state.pop("miasto", None)   # usuwa zapisane miasto
    st.session_state.pop("kom", None)      # czyści komentarz z text_area
    st.session_state.pop("grade", None)    # czyści ocenę z selectboxa
    st.rerun()  # odświeża stronę bez przełączania (pozostajesz w app.py)

if st.session_state.get("go_tierlist", False):
    st.session_state["go_tierlist"] = False
    st.switch_page("pages/tierlista.py")

# =========================
# 6a) EKRAN STARTOWY — LOSOWANIE
# =========================

if not user:
    st.markdown(
        "<h3 style='text-align:center; margin-top:20vh;'>👋 Witaj!<br>Wpisz nazwę użytkownika w panelu bocznym, aby rozpocząć.</h3>",
        unsafe_allow_html=True
    )
else:
    st.markdown("""
    <style>
        /* Kontener główny */
        .main-container {
            display: flex;
            flex-direction: column;
            justify-content: center;   /* pionowe wyśrodkowanie */
            align-items: center;       /* poziome wyśrodkowanie */
            height: 1vh;              /* wysokość widoku, by nie trzeba było przewijać */
            text-align: center;
        }

        /* Tytuł */
        .main-title {
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 10px;
            color: #00000;  /* ciemnoniebieski szary */
        }

        /* Podtytuł */
        .main-subtitle {
            font-size: 20px;
            color: #00000;
            margin-bottom: 60px;
        }

        /* Rząd przycisków */
        .button-row {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 60px;
        }

        /* Styl przycisków */
        div[data-testid="stButton"] button {
            font-size: 22px;
            font-weight: 600;
            padding: 22px 40px;
            border-radius: 14px;
            background-color: #2563eb;
            color: white;
            border: none;
            transition: all 0.2s ease-in-out;
            box-shadow: 0px 4px 12px rgba(37, 99, 235, 0.2);
        }
        div[data-testid="stButton"] button:hover {
            background-color: #1e40af;
            transform: scale(1.05);
            box-shadow: 0px 6px 16px rgba(30, 64, 175, 0.35);
        }

    </style>
""", unsafe_allow_html=True)

    # Kontener z centralnym wyrównaniem
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown('<div class="main-title">🎯 Losuj polskie miasta</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Wybierz typ miasta, które chcesz odkryć</div>', unsafe_allow_html=True)

    st.markdown('<div class="button-row">', unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🏡 Losuj małe miasto (≤ 50 000)", key="male_btn"):
            male = miasta[miasta["Ludność"].notna() & (miasta["Ludność"] <= 50_000)]
            if not male.empty:
                st.session_state["miasto"] = male.sample(1)["Miasto"].iloc[0]
            else:
                st.error("Brak danych o małych miastach.")

    with colB:
        if st.button("🌆 Losuj duże miasto (> 50 000)", key="duze_btn"):
            duze = miasta[miasta["Ludność"].notna() & (miasta["Ludność"] > 50_000)]
            if not duze.empty:
                st.session_state["miasto"] = duze.sample(1)["Miasto"].iloc[0]
            else:
                st.error("Brak danych o dużych miastach.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    # =========================
    # 6b) PANEL MIASTA
    # =========================
if "miasto" in st.session_state:
    miasto = st.session_state["miasto"]
    st.subheader(f"🎯 Wylosowano: **{miasto}**")
    link = f"https://www.google.com/maps/search/?api=1&query={miasto.replace(' ', '+')}"
    st.markdown(f"[🗺️ Otwórz w Google Maps]({link})")

    # 🗺️ Osadzona mapa
    st.markdown(
        f"""
        <iframe 
            src="https://www.google.com/maps?q={miasto.replace(' ', '+')}&output=embed" 
            width="100%" height="400" style="border-radius:12px; border:1px solid #ccc;">
        </iframe>
        """,
        unsafe_allow_html=True,
    )

    st.write("---")
    st.markdown("### 💬 Dodaj komentarz i ocenę literową")
    komentarz = st.text_area("Komentarz (opcjonalnie):", key="kom")
    ocena = st.selectbox("Ocena (F…S):", OCENY_DOZW, index=0, placeholder="Wybierz ocenę", key="grade")

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("💾 Zapisz / nadpisz"):
            if komentarz or ocena:
                save_comment(user, miasto, komentarz or None, ocena or None)
                st.success("Zapisano (UPSERT).")
            else:
                st.warning("Podaj komentarz lub ocenę (przynajmniej jedno).")
            if ocena == "— brak —":
                ocena = None

    st.write("---")
    st.markdown("### 🧾 Zestawienie ocen użytkowników — tylko to miasto")
    df_city = read_city_entries(miasto)
    if not df_city.empty:
        df_city = df_city[df_city["Ocena"].notna() & (df_city["Ocena"] != "-brak-")]
    if df_city.empty:
        st.info("Brak wpisów dla tego miasta.")
    else:
        st.dataframe(df_city, use_container_width=True)

# =========================
# 🏆 RANKING MAŁYCH MIAST
# =========================
st.write("---")
st.header("🏆 Ultimate ranking małych miast 🏆")

df_all = read_all_grades()
if df_all.empty:
    st.info("Brak ocen w bazie – dodaj pierwsze wpisy, aby zobaczyć ranking.")
else:
    # filtruj tylko małe miasta
    df_all = df_all.merge(miasta[["Miasto","Ludność"]], left_on="miasto", right_on="Miasto", how="left")
    df_all = df_all[df_all["Ludność"].notna() & (df_all["Ludność"] <= 50_000)].copy()

    if df_all.empty:
        st.info("Brak ocen dla małych miast.")
    else:
        # przelicz na numery
        df_all["ocena_num"] = df_all["ocena"].map(LIT_TO_NUM_GLOBAL)
        df_all = df_all.dropna(subset=["ocena_num"])

        # agregacja
        summary = (
            df_all.groupby("miasto")
            .agg(Średnia=("ocena_num","mean"), Liczba_ocen=("ocena_num","count"))
            .reset_index()
        )

        # parametry bayesowskie
        C = summary["Średnia"].mean() if not summary.empty else 0
        m = summary["Liczba_ocen"].quantile(0.5) if not summary.empty else 1

        # ważony wynik
        summary["Ważony_wynik"] = (
            (summary["Liczba_ocen"] / (summary["Liczba_ocen"] + m)) * summary["Średnia"]
            + (m / (summary["Liczba_ocen"] + m)) * C
        )

        # literowe pasma
        summary["Ocena końcowa"] = summary["Ważony_wynik"].apply(num_to_band)

        # sortuj
        summary = summary.sort_values(["Ważony_wynik","Liczba_ocen"], ascending=[False, False])

        st.dataframe(
            summary[["miasto","Ocena końcowa","Liczba_ocen"]]
            .rename(columns={"miasto":"Miasto"}),
            use_container_width=True,
        )
# =========================
# 🔍 WYSZUKIWARKA MIASTA
# =========================
st.write("---")
st.markdown("### 🔍 Wyszukaj konkretne miasto")

search_city = st.text_input(
    "Wpisz nazwę miasta, aby otworzyć jego stronę:",
    placeholder="np. Zamość",
    key="search_city"
)

go_to_city = st.button("🔎 Przejdź do miasta", use_container_width=True)

# logika po naciśnięciu przycisku
if go_to_city:
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

# rerun poza callbackiem
if st.session_state.get("go_to_city_trigger", False):
    st.session_state["go_to_city_trigger"] = False
    st.rerun()