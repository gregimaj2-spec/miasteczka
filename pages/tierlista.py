import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Tierlista", page_icon="📚", layout="wide")

hide_default_format = """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_default_format, unsafe_allow_html=True)

# === STYL GLOBALNY ===
st.markdown("""
    <style>
        /* Globalne tło i kolor tekstu */
        .stApp {
            background-color: #1e1e1e;
            color: #f8fafc !important;
        }

        h1, h2, h3, label, p, div, span {
            color: #f8fafc !important;
        }

        /* Styl tabel */
        div[data-testid="stDataFrame"] {
            background-color: transparent !important;
            color: #f8fafc !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #2a2a2a !important;
            color: #f8fafc !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
            background-color: #374151;
            color: #f1f5f9;
            border: 1px solid #6b7280;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.15s ease-in-out;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            background-color: #4b5563;
            border-color: #9ca3af;
            transform: scale(1.02);
        }

        /* Kolory tierów */
        .tier-S { background-color: rgba(234,179,8,0.25) !important; }
        .tier-A { background-color: rgba(59,130,246,0.25) !important; }
        .tier-B { background-color: rgba(34,197,94,0.25) !important; }
        .tier-C { background-color: rgba(168,85,247,0.25) !important; }
        .tier-D { background-color: rgba(249,115,22,0.25) !important; }
        .tier-F { background-color: rgba(239,68,68,0.25) !important; }
            
            /* Guziki akcji (np. Otwórz miasto) */
        div[data-testid="stButton"] > button {
            background-color: #3b82f6 !important;  /* niebieski */
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5em 1em !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #2563eb !important;  /* ciemniejszy niebieski */
            transform: scale(1.03);
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
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
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
    # Czyścimy dane z sesji
    for key in ["miasto", "kom", "grade"]:
        st.session_state.pop(key, None)
    st.switch_page("app.py")  # wróć do strony głównej

if not user:
    st.warning("👉 Wpisz swoją nazwę użytkownika, aby zobaczyć tierlistę.")
    st.stop()

# --- FUNKCJE DB ---
def read_user_grades(user):
    with sqlite3.connect("miasta.db") as conn:
        return pd.read_sql_query(
            "SELECT miasto, ocena FROM komentarze WHERE user=? AND ocena IS NOT NULL",
            conn, params=(user,)
        )

# --- TIERLISTA ---
st.title(f"📚 Tierlista użytkownika **{user}**")

df_user = read_user_grades(user)

# --- FILTR: tylko małe miasta ---
# wczytaj dane z Wikipedii (te same, co w app.py)
import urllib.request
from io import StringIO

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

show_small_only = st.toggle("Pokaż tylko małe miasta (≤ 50 000 mieszkańców)", value=True)

if show_small_only:
    miasta = load_miasta()
    df_user = df_user.merge(miasta, left_on="miasto", right_on="Miasto", how="left")
    df_user = df_user[df_user["Ludność"].notna() & (df_user["Ludność"] <= 50_000)]

if df_user.empty:
    st.info("Nie masz jeszcze żadnych ocen. Wróć do strony głównej i oceń kilka miast.")
else:
    # grupowanie wg ocen
    tiers = ["S", "A", "B", "C", "D", "F"]
    grouped = (
        df_user.groupby("ocena")["miasto"]
        .apply(lambda s: ", ".join(sorted(s)))
        .reindex(tiers)
        .reset_index()
        .rename(columns={"ocena": "Ocena", "miasto": "Miasta"})
    ).fillna("")

    # podsumowanie
    summary = df_user["ocena"].value_counts().reindex(tiers).fillna(0).astype(int)
    total = summary.sum()

    st.markdown("---")
    st.markdown("### 🧮 Podsumowanie Twoich ocen")

    cols = st.columns(len(tiers))
    colors = {
        "S":"#eab308", "A":"#3b82f6", "B":"#22c55e",
        "C":"#a855f7", "D":"#f97316", "F":"#ef4444"
    }
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

    # tabela z kolorowym tłem
    st.markdown("---")
    st.markdown("### 🎯 Twoja tierlista")
    styled = grouped.style.map(
        lambda val: (
        "background-color: #0047AB; color: #fff; font-weight: 800;" if val == "S" else    # kobaltowy
        "background-color: #007FFF; color: #fff; font-weight: 800;" if val == "A" else    # lazurowy
        "background-color: #708238; color: #fff; font-weight: 800;" if val == "B" else    # oliwkowy
        "background-color: #FFD700; color: #000; font-weight: 800;" if val == "C" else    # złoty
        "background-color: #FF8C00; color: #000; font-weight: 800;" if val == "D" else    # pomarańczowy
        "background-color: #DC143C; color: #fff; font-weight: 800;" if val == "F" else ""
        ),
        subset=["Ocena"]
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # wyszukiwarka
    st.markdown("---")
    st.markdown("### 🔍 Przejdź do miasta z listy")
    selected_city = st.text_input("Wpisz nazwę miasta z Twojej listy:")

    if st.button("➡️ Otwórz to miasto"):
        if selected_city.strip() == "":
            st.warning("Podaj nazwę miasta, aby przejść dalej.")
        else:
            st.session_state["miasto"] = selected_city.strip()
            st.switch_page("app.py")