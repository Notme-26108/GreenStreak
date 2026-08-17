import streamlit as st
import json
import os
import random
import math
import requests
from datetime import date, timedelta

st.set_page_config(page_title="GreenStreak", page_icon="🌱", layout="wide")

DATA_FILE = "greenstreak_data.json"
PHOTO_DIR = "journal_photos"
COMMUNITY_FILE = "community_board.json"
TOTAL_PLOTS = 15

# ---------- SAVE / LOAD ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return None

def save_data():
    data = {
        "name": st.session_state.name,
        "avatar": st.session_state.avatar,
        "streak": st.session_state.streak,
        "best_streak": st.session_state.best_streak,
        "leaves": st.session_state.leaves,
        "total_leaves_earned": st.session_state.total_leaves_earned,
        "completed_today": st.session_state.completed_today,
        "streak_counted_today": st.session_state.streak_counted_today,
        "garden": st.session_state.garden,
        "last_active_date": st.session_state.last_active_date,
        "day_count": st.session_state.day_count,
        "impact": st.session_state.impact,
        "journal": st.session_state.journal,
        "dark_mode": st.session_state.dark_mode,
        "city": st.session_state.city,
        "streak_freezes": st.session_state.streak_freezes,
        "freeze_used_notice": st.session_state.freeze_used_notice,
        "critter": st.session_state.critter,
        "weather_quest": st.session_state.weather_quest,
        "weather_quest_day": st.session_state.weather_quest_day,
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)
    update_community_board()

def update_community_board():
    board = {}
    if os.path.exists(COMMUNITY_FILE):
        try:
            with open(COMMUNITY_FILE, "r") as f:
                board = json.load(f)
        except Exception:
            board = {}
    if st.session_state.name:
        garden_filled = sum(1 for p in st.session_state.garden if p is not None)
        board[st.session_state.name] = {
            "avatar": st.session_state.avatar,
            "streak": st.session_state.streak,
            "best_streak": st.session_state.best_streak,
            "garden_filled": garden_filled,
            "leaves": st.session_state.leaves,
        }
    with open(COMMUNITY_FILE, "w") as f:
        json.dump(board, f)

# ---------- INITIALIZE STATE (load once) ----------
if "loaded" not in st.session_state:
    saved = load_data()
    if saved:
        st.session_state.name = saved["name"]
        st.session_state.avatar = saved["avatar"]
        st.session_state.streak = saved["streak"]
        st.session_state.best_streak = saved.get("best_streak", saved["streak"])
        st.session_state.leaves = saved["leaves"]
        st.session_state.total_leaves_earned = saved.get("total_leaves_earned", saved["leaves"])
        st.session_state.completed_today = saved["completed_today"]
        st.session_state.streak_counted_today = saved["streak_counted_today"]
        garden = saved["garden"]
        if len(garden) < TOTAL_PLOTS:
            garden = garden + [None] * (TOTAL_PLOTS - len(garden))
        st.session_state.garden = garden
        st.session_state.last_active_date = saved["last_active_date"]
        st.session_state.day_count = saved.get("day_count", 0)
        st.session_state.impact = saved.get("impact", {"litter_pieces": 0, "minutes_outside": 0, "nature_spots": 0})
        st.session_state.journal = saved.get("journal", [])
        st.session_state.dark_mode = saved.get("dark_mode", False)
        st.session_state.city = saved.get("city", "Bangalore")
        st.session_state.streak_freezes = saved.get("streak_freezes", 0)
        st.session_state.freeze_used_notice = saved.get("freeze_used_notice", False)
        st.session_state.critter = saved.get("critter")
        st.session_state.weather_quest = saved.get("weather_quest")
        st.session_state.weather_quest_day = saved.get("weather_quest_day", -1)
    else:
        st.session_state.name = ""
        st.session_state.avatar = "🧑‍🌾"
        st.session_state.streak = 0
        st.session_state.best_streak = 0
        st.session_state.leaves = 0
        st.session_state.total_leaves_earned = 0
        st.session_state.completed_today = []
        st.session_state.streak_counted_today = False
        st.session_state.garden = [None] * TOTAL_PLOTS  # each slot: None or {"type": "🌼", "stage": 0}
        st.session_state.last_active_date = date.today().isoformat()
        st.session_state.day_count = 0
        st.session_state.impact = {"litter_pieces": 0, "minutes_outside": 0, "nature_spots": 0}
        st.session_state.journal = []
        st.session_state.dark_mode = False
        st.session_state.city = "Bangalore"
        st.session_state.streak_freezes = 0
        st.session_state.freeze_used_notice = False
        st.session_state.critter = None
        st.session_state.weather_quest = None
        st.session_state.weather_quest_day = -1
    st.session_state.loaded = True

# ---------- CRITTER POOL ----------
CRITTERS = [
    {"emoji": "🦋", "name": "a butterfly", "flavor": "A butterfly is dancing between your flowers.", "reward": 8},
    {"emoji": "🦔", "name": "a hedgehog", "flavor": "A hedgehog is snoozing in your flowerbed.", "reward": 10},
    {"emoji": "🐝", "name": "a bee", "flavor": "A bee is busy visiting your blooms.", "reward": 6},
    {"emoji": "🐦", "name": "a bird", "flavor": "A little bird stopped by to say hello.", "reward": 8},
    {"emoji": "🐿️", "name": "a squirrel", "flavor": "A squirrel is burying something in your garden.", "reward": 9},
    {"emoji": "🐌", "name": "a snail", "flavor": "A snail is slowly exploring your plots.", "reward": 5},
]
CRITTER_CHANCE = 0.4  # 40% chance a critter shows up on any given day
MYSTERY_CHANCE = 0.25  # 25% chance the critter leaves a mystery bloom instead of leaves

# ---------- REAL DAILY RESET (based on actual date) ----------
today_str = date.today().isoformat()
if st.session_state.last_active_date != today_str:
    st.session_state.freeze_used_notice = False
    if not st.session_state.streak_counted_today:
        if st.session_state.streak_freezes > 0:
            st.session_state.streak_freezes -= 1
            st.session_state.freeze_used_notice = True
        else:
            st.session_state.streak = 0  # missed a day, no freeze available
    st.session_state.completed_today = []
    st.session_state.streak_counted_today = False
    st.session_state.last_active_date = today_str
    st.session_state.day_count += 1

    # grow every planted, not-yet-bloomed plot by one stage each real day
    for plot in st.session_state.garden:
        if plot is not None and plot["stage"] < 2:
            plot["stage"] += 1

    # roll for a new critter visitor
    critter_rng = random.Random(st.session_state.day_count * 7919 + 13)
    if critter_rng.random() < CRITTER_CHANCE:
        chosen = critter_rng.choice(CRITTERS)
        st.session_state.critter = {**chosen, "visited": False}
    else:
        st.session_state.critter = None

    save_data()

# ---------- SIDEBAR ----------
AVATAR_OPTIONS = {
    "🧑‍🌾 Human Gardener": "🧑‍🌾",
    "🐰 Bunny Gardener": "🐰",
    "🦊 Fox Gardener": "🦊",
    "🦉 Owl Gardener": "🦉",
    "🐼 Panda Gardener": "🐼",
}
AVATAR_LOOKUP = {v: k for k, v in AVATAR_OPTIONS.items()}

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    dark_toggle = st.toggle("🌙 Dark mode", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        save_data()
        st.rerun()

    if st.session_state.name:
        with st.expander("👤 Profile"):
            new_name = st.text_input("Name", value=st.session_state.name, key="profile_name_input")
            current_label = AVATAR_LOOKUP.get(st.session_state.avatar, list(AVATAR_OPTIONS.keys())[0])
            new_avatar_label = st.radio("Gardener", list(AVATAR_OPTIONS.keys()),
                                         index=list(AVATAR_OPTIONS.keys()).index(current_label),
                                         key="profile_avatar_input")
            if st.button("💾 Save profile"):
                if new_name.strip() != "":
                    st.session_state.name = new_name.strip()
                    st.session_state.avatar = AVATAR_OPTIONS[new_avatar_label]
                    save_data()
                    st.rerun()

        with st.expander("📍 Location"):
            new_city = st.text_input("City (for weather quest & nearby nature)", value=st.session_state.city, key="city_input")
            if st.button("💾 Save location"):
                st.session_state.city = new_city.strip() or "Bangalore"
                st.session_state.weather_quest_day = -1  # force refetch
                save_data()
                st.rerun()

# ---------- COLOR PALETTE ----------
if st.session_state.dark_mode:
    P = {
        "bg1": "#1E2420", "bg2": "#161B18",
        "text": "#D8E6D2", "title": "#9FCB96", "subtitle": "#8FB88A",
        "card_bg": "#232C27", "card_border": "#3A473C",
        "metric_val": "#E0B36B",
        "btn_bg": "#4C7A55", "btn_hover": "#5C8F65", "btn_shadow": "#2F4C36",
        "mascot_bg": "#232C27",
        "sky_grad": "#16202E 0%, #16202E 18%, #223321 18%, #1B2A18 100%",
        "fence_color": "#5C4632",
        "deco_after": "🌙",
        "empty_color": "#3A473C",
        "stage_label": "#9FB395",
        "badge_locked": "#2A322C",
    }
else:
    P = {
        "bg1": "#FDF6EC", "bg2": "#F3EFE0",
        "text": "#4A5D46", "title": "#5B7B5A", "subtitle": "#6E8B6A",
        "card_bg": "#FFFDF8", "card_border": "#E6DCC3",
        "metric_val": "#B5793D",
        "btn_bg": "#A8C69F", "btn_hover": "#93B888", "btn_shadow": "#7FA377",
        "mascot_bg": "#F0EAD6",
        "sky_grad": "#BEE3F5 0%, #BEE3F5 18%, #DCEFBE 18%, #A9D68C 100%",
        "fence_color": "#C9A66B",
        "deco_after": "☀️",
        "empty_color": "#EAF4DE",
        "stage_label": "#8A7A55",
        "badge_locked": "#EFE9D6",
    }

# ---------- CSS ----------
css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&display=swap');

html, body, [class*="css"] {{ font-family: 'Quicksand', sans-serif; }}
.stApp {{
    background: linear-gradient(180deg, {P['bg1']} 0%, {P['bg2']} 100%);
    background-image:
        radial-gradient(circle, {P['card_border']}55 1px, transparent 1px),
        linear-gradient(180deg, {P['bg1']} 0%, {P['bg2']} 100%);
    background-size: 22px 22px, 100% 100%;
}}
.stApp, .stApp p, .stApp span, .stApp label, .stApp div, .stApp li {{
    color: {P['text']} !important;
}}
h1 {{ color: {P['title']} !important; font-weight: 700 !important; text-align: center; }}
h3 {{ color: {P['subtitle']} !important; }}

[data-testid="stAppViewContainer"] .main .block-container {{
    max-width: 900px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}}

.stMetric {{
    background-color: {P['card_bg']};
    border-radius: 20px;
    padding: 10px;
    border: 2px solid {P['card_border']};
}}
div[data-testid="stMetricValue"] {{ color: {P['metric_val']} !important; }}

.quest-card, .impact-card, .journal-entry, .today-card {{
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.quest-card:hover, .impact-card:hover, .journal-entry:hover {{
    transform: translateY(-2px);
    box-shadow: 3px 5px 0px {P['card_border']};
}}

.quest-card {{
    background-color: {P['card_bg']};
    border-radius: 18px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border: 2px solid {P['card_border']};
    box-shadow: 2px 2px 0px {P['card_border']};
}}

.today-card {{
    background-color: {P['card_bg']};
    border: 2px dashed {P['card_border']};
    border-radius: 18px;
    padding: 12px 18px;
    margin-bottom: 14px;
    text-align: center;
}}

.stButton>button {{
    background-color: {P['btn_bg']};
    color: white !important;
    border-radius: 30px;
    border: none;
    padding: 6px 18px;
    font-weight: 600;
    box-shadow: 2px 2px 0px {P['btn_shadow']};
}}
.stButton>button:hover {{ background-color: {P['btn_hover']}; color: white !important; }}
.stButton>button:focus-visible, a:focus-visible, input:focus-visible, [role="radio"]:focus-visible {{
    outline: 3px solid {P['metric_val']} !important;
    outline-offset: 2px !important;
}}

.mascot-box {{
    text-align: center;
    background-color: {P['mascot_bg']};
    border-radius: 24px;
    padding: 16px;
    margin-bottom: 18px;
    border: 2px solid {P['card_border']};
}}
.mascot-emoji {{ font-size: 60px; animation: bob 2s ease-in-out infinite; }}
@keyframes bob {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-8px); }} }}
.mascot-speech {{ font-weight: 600; color: {P['subtitle']} !important; margin-top: 4px; }}

.header-deco {{
    text-align: center;
    font-size: 22px;
    letter-spacing: 10px;
    margin: -6px 0 14px 0;
    animation: bob 3s ease-in-out infinite;
    opacity: 0.85;
}}

.side-leaf {{
    position: fixed;
    top: 40%;
    font-size: 34px;
    opacity: 0.35;
    animation: bob 4s ease-in-out infinite;
    z-index: 0;
    display: none;
}}
.side-leaf-left {{ left: 2%; }}
.side-leaf-right {{ right: 2%; }}
@media (min-width: 1100px) {{
    .side-leaf {{ display: block; }}
}}

.st-key-garden_scene {{
    position: relative;
    background: linear-gradient(180deg, {P['sky_grad']}) !important;
    border-radius: 24px !important;
    padding: 30px 16px 22px 16px !important;
    border: 5px solid #A9764F !important;
    overflow: hidden;
}}
.st-key-garden_scene::before {{
    content: "🌳";
    position: absolute;
    top: 2px;
    left: 6px;
    font-size: 32px;
}}
.st-key-garden_scene::after {{
    content: "{P['deco_after']}";
    position: absolute;
    top: 4px;
    right: 10px;
    font-size: 26px;
}}
.garden-fence {{
    width: 100%;
    height: 12px;
    margin-top: 4px;
    background-image: repeating-linear-gradient(90deg, {P['fence_color']} 0px, {P['fence_color']} 5px, transparent 5px, transparent 13px);
}}
.garden-butterfly {{
    position: absolute;
    top: 14px;
    font-size: 18px;
    animation: flutter 9s linear infinite;
}}
@keyframes flutter {{
    0% {{ left: -5%; transform: translateY(0px); }}
    25% {{ transform: translateY(-6px); }}
    50% {{ transform: translateY(0px); }}
    75% {{ transform: translateY(-6px); }}
    100% {{ left: 100%; transform: translateY(0px); }}
}}
.garden-plot {{
    text-align: center;
    font-size: 36px;
    background: transparent;
    border: none;
    margin: 2px 2px 0px 2px;
    padding: 0;
    filter: drop-shadow(1px 3px 1px rgba(60,45,20,0.25));
    animation: grow-in 0.6s ease;
}}
.empty-plot {{
    text-align: center;
    font-size: 18px;
    color: {P['empty_color']} !important;
    opacity: 0.9;
    margin: 10px 2px 0px 2px;
}}
.locked-plot {{
    text-align: center;
    font-size: 20px;
    opacity: 0.5;
    margin: 10px 2px 0px 2px;
}}
.plot-stage-label {{
    text-align: center;
    font-size: 10px;
    color: {P['stage_label']} !important;
    margin: 0px 2px 8px 2px;
}}
@keyframes grow-in {{ 0% {{ transform: scale(0.7); opacity: 0.5; }} 100% {{ transform: scale(1); opacity: 1; }} }}

@keyframes sparkle {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.4; }}
}}
.bloom-ready {{ animation: grow-in 0.6s ease, sparkle 1.5s ease-in-out infinite; }}

@keyframes dig {{
    0%, 100% {{ transform: rotate(0deg) translateY(0px); }}
    25% {{ transform: rotate(-18deg) translateY(2px); }}
    50% {{ transform: rotate(0deg) translateY(5px); }}
    75% {{ transform: rotate(18deg) translateY(2px); }}
}}
.gardener-dig {{ animation: dig 0.9s ease-in-out infinite; }}

@keyframes celebrate-bounce {{
    0%, 100% {{ transform: translateY(0) scale(1); }}
    30% {{ transform: translateY(-12px) scale(1.15); }}
    60% {{ transform: translateY(0) scale(1); }}
}}
.gardener-celebrate {{ animation: celebrate-bounce 0.7s ease-in-out infinite; }}

.critter-card {{
    background-color: {P['card_bg']};
    border-radius: 18px;
    padding: 14px 18px;
    margin: 4px 0 14px 0;
    border: 2px dashed {P['metric_val']};
    text-align: center;
}}
.critter-emoji {{ font-size: 44px; animation: bob 2.2s ease-in-out infinite; }}

.impact-card {{
    background-color: {P['card_bg']};
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 10px;
    border: 2px solid {P['card_border']};
    text-align: center;
}}
.impact-number {{
    font-size: 30px;
    font-weight: 700;
    color: {P['metric_val']} !important;
}}
.impact-label {{
    font-size: 13px;
    color: {P['subtitle']} !important;
}}
.journal-entry {{
    background-color: {P['card_bg']};
    border-radius: 16px;
    padding: 12px 16px;
    margin-bottom: 10px;
    border: 2px solid {P['card_border']};
}}
.journal-date {{
    font-size: 11px;
    color: {P['subtitle']} !important;
}}

.badge-row {{ display: flex; gap: 14px; justify-content: center; margin: 10px 0 4px 0; flex-wrap: wrap; }}
.badge {{
    text-align: center;
    background-color: {P['card_bg']};
    border: 2px solid {P['card_border']};
    border-radius: 16px;
    padding: 10px 14px;
    min-width: 74px;
}}
.badge-locked {{ opacity: 0.4; background-color: {P['badge_locked']}; }}
.badge-emoji {{ font-size: 26px; }}
.badge-label {{ font-size: 11px; color: {P['subtitle']} !important; }}

.footer-note {{
    text-align: center;
    font-size: 12px;
    color: {P['subtitle']} !important;
    margin-top: 30px;
    opacity: 0.8;
}}

.leaderboard-row {{
    display: flex;
    justify-content: space-between;
    background-color: {P['card_bg']};
    border: 2px solid {P['card_border']};
    border-radius: 14px;
    padding: 10px 16px;
    margin-bottom: 8px;
}}

.explore-row {{
    background-color: {P['card_bg']};
    border: 2px solid {P['card_border']};
    border-radius: 14px;
    padding: 10px 16px;
    margin-bottom: 8px;
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)
st.markdown("<div class='side-leaf side-leaf-left'>🌿</div><div class='side-leaf side-leaf-right'>🍃</div>", unsafe_allow_html=True)

st.title("🌱 GreenStreak")
st.markdown("<p style='text-align:center;'>a cozy little garden that grows with you 🍃</p>", unsafe_allow_html=True)
st.markdown("<div class='header-deco'>🍃 🌸 🦋 🍃 🌼</div>", unsafe_allow_html=True)

# ---------- PROFILE (first-time setup) ----------
if st.session_state.name == "":
    st.subheader("👋 Welcome! Let's set up your garden")
    name_input = st.text_input("What should we call you?")
    avatar_label = st.radio("Pick your gardener", list(AVATAR_OPTIONS.keys()), horizontal=True)
    if st.button("Start my garden 🌱"):
        if name_input.strip() != "":
            st.session_state.name = name_input.strip()
            st.session_state.avatar = AVATAR_OPTIONS[avatar_label]
            save_data()
            st.rerun()
        else:
            st.warning("Please enter a name first!")
    st.stop()

# ---------- QUEST POOL (randomized daily via day_count) ----------
all_quests = [
    {"id": "outside", "text": "Step outside and just breathe for 10 minutes", "emoji": "🌤️", "reward": 5, "impact": ("minutes_outside", 10)},
    {"id": "spot", "text": "Be a detective — spot a bird, bug, or plant you've never noticed", "emoji": "🐦", "reward": 7, "impact": ("nature_spots", 1)},
    {"id": "declutter", "text": "Litter bandit mission: collect 3 pieces of trash on your walk", "emoji": "🧹", "reward": 10, "impact": ("litter_pieces", 3)},
    {"id": "water", "text": "Sip water outside like the fresh-air royalty you are", "emoji": "💧", "reward": 5, "impact": None},
    {"id": "sketch", "text": "Leaf hunter: sketch or photograph the most interesting leaf you find", "emoji": "🍂", "reward": 7, "impact": ("nature_spots", 1)},
    {"id": "walk", "text": "Take the scenic route — a short walk through any green space", "emoji": "🚶", "reward": 7, "impact": ("minutes_outside", 10)},
    {"id": "sky", "text": "Cloud-gaze for 5 minutes, phone nowhere in sight", "emoji": "☁️", "reward": 5, "impact": ("minutes_outside", 5)},
    {"id": "plantcare", "text": "Give a plant some love — water it like it's your best friend", "emoji": "🪴", "reward": 7, "impact": None},
    {"id": "sound", "text": "Nature ASMR: sit still and count how many natural sounds you hear", "emoji": "👂", "reward": 10, "impact": None},
    {"id": "goldenhour", "text": "Catch the sunrise or sunset for a few quiet minutes", "emoji": "🌅", "reward": 8, "impact": ("minutes_outside", 5)},
    {"id": "forage", "text": "Plant ID challenge: identify one plant you walk past every day", "emoji": "🌿", "reward": 8, "impact": ("nature_spots", 1)},
    {"id": "breeze", "text": "Stand still outside and really notice the wind for a minute", "emoji": "🍃", "reward": 5, "impact": None},
]

quest_rng = random.Random(st.session_state.day_count)
quests = quest_rng.sample(all_quests, 3)

# ---------- WEATHER BONUS QUEST (Open-Meteo, free, no key) ----------
def fetch_weather_quest(city):
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=6,
        ).json()
        if not geo.get("results"):
            return None
        loc = geo["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code,cloud_cover"},
            timeout=6,
        ).json()
        current = wx.get("current", {})
        code = current.get("weather_code", 0)
        cloud = current.get("cloud_cover", 50)
        temp = current.get("temperature_2m")

        if code in (0, 1) and cloud < 30:
            return {"text": f"Clear skies in {city} tonight — spend 5 minutes stargazing", "emoji": "🌌", "reward": 10}
        elif code in (2, 3):
            return {"text": f"Cloudy in {city} — find shapes in the clouds for a few minutes", "emoji": "☁️", "reward": 8}
        elif code in range(51, 68) or code in range(80, 100):
            return {"text": f"It's rainy in {city} — watch or listen to the rain from somewhere dry", "emoji": "🌧️", "reward": 8}
        elif temp is not None and temp >= 30:
            return {"text": f"It's warm in {city} — find some shade under a real tree", "emoji": "🌳", "reward": 8}
        else:
            return {"text": f"Step out and notice today's weather in {city}", "emoji": "🌦️", "reward": 7}
    except Exception:
        return None

if st.session_state.weather_quest_day != st.session_state.day_count:
    fetched = fetch_weather_quest(st.session_state.city)
    st.session_state.weather_quest = fetched
    st.session_state.weather_quest_day = st.session_state.day_count
    save_data()

# ---------- MASCOT ----------
all_done_check = len(st.session_state.completed_today) == 3

if all_done_check:
    mascot_text = f"Yay {st.session_state.name}! You did it today! So proud of you!"
elif len(st.session_state.completed_today) > 0:
    mascot_text = f"You're doing great, {st.session_state.name}! Keep going!"
else:
    mascot_text = f"Hi {st.session_state.name}! Let's start today's quests together!"

# ---------- TABS ----------
tab_home, tab_garden, tab_journal, tab_stats, tab_community, tab_explore = st.tabs(
    ["🏠 Home", "🌻 Garden", "📔 Journal", "📊 Stats", "👥 Community", "🧭 Explore Nearby"]
)

# ================= HOME TAB =================
with tab_home:
    st.markdown(f"""
    <div class="today-card">
        🗓️ <b>Day {st.session_state.day_count + 1}</b> of your GreenStreak journey — current streak 🔥 {st.session_state.streak}
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.freeze_used_notice:
        st.info("❄️ You missed yesterday, but a Streak Freeze protected your streak! It's been used up.")

    st.markdown(f"""
    <div class="mascot-box">
        <div class="mascot-emoji">{st.session_state.avatar}</div>
        <div class="mascot-speech">{mascot_text}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("❓ How to play"):
        st.markdown("""
        - Every day you get **3 nature quests** — complete them to earn 🍃 Leaves and build your streak
        - There's sometimes a **bonus weather quest** based on real conditions where you live
        - Spend Leaves in the **Garden** tab to plant flowers, trees, and more
        - Plants grow over **2 real days**: 🌱 seed → 🌿 growing → full bloom — then harvest for a bigger payout
        - Miss a day and your streak resets — unless you have a **❄️ Streak Freeze** saved up (buy one in Stats)
        - Occasionally a **critter visitor** shows up in your garden with a surprise reward
        """)

    st.subheader("🌿 Today's Quests")

    for quest in quests:
        already_done = quest["id"] in st.session_state.completed_today
        photo_key = f"photo_{quest['id']}_{st.session_state.day_count}"

        st.markdown("<div class='quest-card'>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"{quest['emoji']} {quest['text']}")
        with c2:
            if already_done:
                st.write("✅ Done")
            else:
                if st.button(f"+{quest['reward']} 🍃", key=quest["id"]):
                    photo_file = st.session_state.get(photo_key)
                    photo_path = None
                    if photo_file is not None:
                        os.makedirs(PHOTO_DIR, exist_ok=True)
                        ext = os.path.splitext(photo_file.name)[1] or ".png"
                        photo_path = f"{PHOTO_DIR}/{st.session_state.day_count}_{quest['id']}{ext}"
                        with open(photo_path, "wb") as f:
                            f.write(photo_file.getbuffer())

                    st.session_state.completed_today.append(quest["id"])
                    st.session_state.leaves += quest["reward"]
                    st.session_state.total_leaves_earned += quest["reward"]
                    if quest["impact"] is not None:
                        key, amount = quest["impact"]
                        st.session_state.impact[key] += amount

                    st.session_state.journal.append({
                        "date": today_str,
                        "quest": quest["text"],
                        "emoji": quest["emoji"],
                        "photo": photo_path,
                    })

                    save_data()
                    st.rerun()
        if not already_done:
            with st.expander("📷 Add a photo (optional)"):
                st.file_uploader("Proof photo", type=["png", "jpg", "jpeg"], key=photo_key, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    # Weather bonus quest card
    if st.session_state.weather_quest:
        wq = st.session_state.weather_quest
        wq_done = "weather" in st.session_state.completed_today
        st.markdown("<div class='quest-card' style='border-style:dashed;'>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"{wq['emoji']} **Bonus:** {wq['text']}")
        with c2:
            if wq_done:
                st.write("✅ Done")
            else:
                if st.button(f"+{wq['reward']} 🍃", key="weather_quest_btn"):
                    st.session_state.completed_today.append("weather")
                    st.session_state.leaves += wq["reward"]
                    st.session_state.total_leaves_earned += wq["reward"]
                    save_data()
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Critter visitor card
    if st.session_state.critter and not st.session_state.critter.get("visited"):
        crit = st.session_state.critter
        st.markdown(f"""
        <div class="critter-card">
            <div class="critter-emoji">{crit['emoji']}</div>
            <div>{crit['flavor']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👋 Say hello", key="critter_btn"):
            mystery_rng = random.Random(st.session_state.day_count * 31 + 7)
            if mystery_rng.random() < MYSTERY_CHANCE:
                empty_unlocked = [i for i in range(TOTAL_PLOTS) if st.session_state.garden[i] is None]
                if empty_unlocked:
                    idx = mystery_rng.choice(empty_unlocked)
                    st.session_state.garden[idx] = {"type": "🌺", "stage": 2}
                    st.success(f"{crit['name'].capitalize()} left behind a rare Mystery Bloom in your garden! 🌺")
                else:
                    st.session_state.leaves += crit["reward"] * 2
                    st.session_state.total_leaves_earned += crit["reward"] * 2
                    st.success(f"Your garden's full, so {crit['name']} left {crit['reward']*2} 🍃 instead!")
            else:
                st.session_state.leaves += crit["reward"]
                st.session_state.total_leaves_earned += crit["reward"]
                st.success(f"{crit['name'].capitalize()} was happy to see you! +{crit['reward']} 🍃")
            st.session_state.critter["visited"] = True
            save_data()
            st.balloons()
            st.rerun()

    all_done = len(st.session_state.completed_today) >= 3
    if all_done and not st.session_state.streak_counted_today:
        st.session_state.streak += 1
        if st.session_state.streak > st.session_state.best_streak:
            st.session_state.best_streak = st.session_state.streak
        st.session_state.streak_counted_today = True
        save_data()
        st.balloons()
        st.rerun()

    if all_done:
        st.success("🎉 All quests complete today! Streak is safe.")

    st.markdown("<div style='text-align:center; margin:16px 0;'>🌿 · · · · · 🌿</div>", unsafe_allow_html=True)

    st.caption("For demo purposes: fast-forward to tomorrow (simulates a real day passing, grows your garden)")
    if st.button("🌅 Fast-forward to tomorrow"):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        st.session_state.last_active_date = yesterday
        save_data()
        st.rerun()

# ================= GARDEN TAB =================
with tab_garden:
    st.subheader("🌻 Your Garden")
    st.caption("Plants grow one stage each real day: 🌱 seed → 🌿 growing → full bloom, ready to harvest!")

    plant_options = {
        "🍄 Mushroom": 6,
        "🌼 Flower": 10,
        "🌷 Tulip": 20,
        "🌳 Tree": 40,
        "🌻 Sunflower": 60,
    }
    harvest_rewards = {
        "🍄": 10,
        "🌼": 15,
        "🌷": 30,
        "🌳": 60,
        "🌻": 90,
        "🌺": 20,  # rare mystery bloom from critters
    }

    STAGE_EMOJI = {0: "🌱", 1: "🌿"}  # stage 2 uses the plant's own final emoji

    unlocked_count = 9
    if st.session_state.best_streak >= 7:
        unlocked_count += 3
    if st.session_state.best_streak >= 14:
        unlocked_count += 3

    if unlocked_count < TOTAL_PLOTS:
        next_threshold = 7 if unlocked_count == 9 else 14
        st.caption(f"🔓 {unlocked_count}/{TOTAL_PLOTS} plots unlocked — reach a {next_threshold}-day streak to unlock more")

    with st.container(key="garden_scene"):
        st.markdown("<div class='garden-butterfly'>🦋</div>", unsafe_allow_html=True)
        for row in range(5):
            cols = st.columns(3)
            for i in range(3):
                idx = row * 3 + i
                with cols[i]:
                    if idx >= unlocked_count:
                        needed = 7 if idx < 12 else 14
                        st.markdown("<div class='locked-plot'>🔒</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='plot-stage-label'>streak {needed}+</div>", unsafe_allow_html=True)
                        continue
                    plot = st.session_state.garden[idx]
                    if plot is None:
                        st.markdown("<div class='empty-plot'>• • •</div>", unsafe_allow_html=True)
                    else:
                        stage = plot["stage"]
                        if stage < 2:
                            display = STAGE_EMOJI[stage]
                            st.markdown(f"<div class='garden-plot'>{display}</div>", unsafe_allow_html=True)
                            label = "seed" if stage == 0 else "growing"
                            st.markdown(f"<div class='plot-stage-label'>{label}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='garden-plot bloom-ready'>{plot['type']}</div>", unsafe_allow_html=True)
                            reward = harvest_rewards.get(plot["type"], 15)
                            if st.button(f"+{reward}🍃", key=f"harvest_{idx}"):
                                st.session_state.leaves += reward
                                st.session_state.total_leaves_earned += reward
                                st.session_state.garden[idx] = None
                                save_data()
                                st.balloons()
                                st.rerun()
        st.markdown("<div class='garden-fence'></div>", unsafe_allow_html=True)

        ready_to_harvest = any(p is not None and p["stage"] == 2 for p in st.session_state.garden)
        still_growing = any(p is not None and p["stage"] < 2 for p in st.session_state.garden)

        if ready_to_harvest:
            gardener_status = "Something's ready to harvest!"
            gardener_class = "gardener-celebrate"
        elif still_growing:
            gardener_status = "Tending the garden..."
            gardener_class = "gardener-dig"
        else:
            gardener_status = "Waiting for you to plant something!"
            gardener_class = ""

        st.markdown(f"""
        <div style='text-align:center; margin-top:6px;'>
            <div class='mascot-emoji {gardener_class}' style='font-size:38px;'>{st.session_state.avatar}</div>
            <div class='plot-stage-label' style='font-size:13px; font-weight:600;'>{gardener_status}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write(f"**Plant something:**  (you have {st.session_state.leaves} 🍃)")
    empty_plots = [i for i in range(unlocked_count) if st.session_state.garden[i] is None]

    if empty_plots:
        plant_choice = st.selectbox("Choose a plant", list(plant_options.keys()))
        cost = plant_options[plant_choice]
        st.write(f"Cost: {cost} 🍃  (takes 2 real days to fully bloom)")
        if st.button("🌱 Plant it"):
            if st.session_state.leaves >= cost:
                plot_index = empty_plots[0]
                plant_emoji = plant_choice.split(" ")[0]
                st.session_state.garden[plot_index] = {"type": plant_emoji, "stage": 0}
                st.session_state.leaves -= cost
                save_data()
                st.rerun()
            else:
                st.error("Not enough leaves! Complete more quests 🌿")
    else:
        st.success("All your unlocked plots are full! 🎉 Harvest one or grow your streak to unlock more.")

# ================= JOURNAL TAB =================
with tab_journal:
    st.subheader("📔 Your Nature Journal")
    st.caption("A running log of everything you've completed, with photos when you added them")

    if len(st.session_state.journal) == 0:
        st.info("Your journal is empty — complete a quest to start logging your nature journey!")
    else:
        for entry in reversed(st.session_state.journal[-30:]):
            st.markdown("<div class='journal-entry'>", unsafe_allow_html=True)
            st.markdown(f"<div class='journal-date'>{entry['date']}</div>", unsafe_allow_html=True)
            st.write(f"{entry['emoji']} {entry['quest']}")
            if entry.get("photo") and os.path.exists(entry["photo"]):
                st.image(entry["photo"], width=200)
            st.markdown("</div>", unsafe_allow_html=True)

# ================= STATS TAB =================
with tab_stats:
    st.subheader(f"📊 {st.session_state.name}'s Stats")

    col1, col2 = st.columns(2)
    col1.metric("🔥 Streak", st.session_state.streak)
    col2.metric("🍃 Leaves", st.session_state.leaves)

    st.caption(f"🏆 Best streak: {st.session_state.best_streak} days · 🍃 {st.session_state.total_leaves_earned} leaves earned in total · ❄️ {st.session_state.streak_freezes} freeze(s) saved")

    st.markdown("<div style='text-align:center; margin:16px 0;'>🌿 · · · · · 🌿</div>", unsafe_allow_html=True)

    st.subheader("🏅 Streak Milestones")
    milestones = [(3, "🥉", "3 days"), (7, "🥈", "7 days"), (14, "🥇", "14 days"), (30, "🏆", "30 days")]
    badge_html = "<div class='badge-row'>"
    for threshold, emoji, label in milestones:
        locked = st.session_state.best_streak < threshold
        cls = "badge badge-locked" if locked else "badge"
        display_emoji = "🔒" if locked else emoji
        badge_html += f"<div class='{cls}'><div class='badge-emoji'>{display_emoji}</div><div class='badge-label'>{label}</div></div>"
    badge_html += "</div>"
    st.markdown(badge_html, unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; margin:16px 0;'>🌿 · · · · · 🌿</div>", unsafe_allow_html=True)

    st.subheader("❄️ Streak Freeze")
    st.caption("Protects your streak once if you ever miss a day — buy a spare for peace of mind.")
    if st.button("Buy a Streak Freeze (25 🍃)"):
        if st.session_state.leaves >= 25:
            st.session_state.leaves -= 25
            st.session_state.streak_freezes += 1
            save_data()
            st.rerun()
        else:
            st.error("Not enough leaves!")

    st.markdown("<div style='text-align:center; margin:16px 0;'>🌿 · · · · · 🌿</div>", unsafe_allow_html=True)

    st.subheader("🌍 Your Environmental Impact")
    st.caption("Real actions logged through your quests")

    impact = st.session_state.impact
    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        st.markdown(f"""
        <div class="impact-card">
            <div class="impact-number">{impact['litter_pieces']}</div>
            <div class="impact-label">🧹 pieces of litter picked up</div>
        </div>
        """, unsafe_allow_html=True)
    with ic2:
        st.markdown(f"""
        <div class="impact-card">
            <div class="impact-number">{impact['minutes_outside']}</div>
            <div class="impact-label">⏱️ minutes spent outside</div>
        </div>
        """, unsafe_allow_html=True)
    with ic3:
        st.markdown(f"""
        <div class="impact-card">
            <div class="impact-number">{impact['nature_spots']}</div>
            <div class="impact-label">🐦 nature moments logged</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; margin:16px 0;'>🌿 · · · · · 🌿</div>", unsafe_allow_html=True)
    with st.expander("⚙️ Reset (for a clean demo recording)"):
        st.caption("This wipes your streak, leaves, garden, journal, and impact stats back to zero.")
        if st.button("🗑️ Reset everything"):
            st.session_state.name = ""
            st.session_state.avatar = "🧑‍🌾"
            st.session_state.streak = 0
            st.session_state.best_streak = 0
            st.session_state.leaves = 0
            st.session_state.total_leaves_earned = 0
            st.session_state.completed_today = []
            st.session_state.streak_counted_today = False
            st.session_state.garden = [None] * TOTAL_PLOTS
            st.session_state.last_active_date = date.today().isoformat()
            st.session_state.day_count = 0
            st.session_state.impact = {"litter_pieces": 0, "minutes_outside": 0, "nature_spots": 0}
            st.session_state.journal = []
            st.session_state.streak_freezes = 0
            st.session_state.freeze_used_notice = False
            st.session_state.critter = None
            save_data()
            st.rerun()

# ================= COMMUNITY TAB =================
with tab_community:
    st.subheader("👥 Community Leaderboard")
    st.caption("Everyone who's used GreenStreak on this device, ranked by best streak. Great for classrooms or friend groups sharing a computer.")

    board = {}
    if os.path.exists(COMMUNITY_FILE):
        try:
            with open(COMMUNITY_FILE, "r") as f:
                board = json.load(f)
        except Exception:
            board = {}

    if not board:
        st.info("No community data yet — it fills in as people use the app.")
    else:
        ranked = sorted(board.items(), key=lambda kv: kv[1].get("best_streak", 0), reverse=True)
        for i, (pname, pdata) in enumerate(ranked, start=1):
            st.markdown(f"""
            <div class="leaderboard-row">
                <span>#{i} {pdata.get('avatar','🌱')} <b>{pname}</b></span>
                <span>🔥 {pdata.get('best_streak',0)} best · 🌻 {pdata.get('garden_filled',0)} plants · 🍃 {pdata.get('leaves',0)}</span>
            </div>
            """, unsafe_allow_html=True)

# ================= EXPLORE NEARBY TAB =================
with tab_explore:
    st.subheader("🧭 Explore Nearby Nature")
    st.caption(
        f"Find real parks, trails, and nature spots near "
        f"{st.session_state.city} using OpenStreetMap."
    )

    if st.button("🔎 Find nearby nature spots", key="find_nature_btn"):
        try:
            # 1. Geocode the selected city
            geo_response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": st.session_state.city,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
                timeout=10,
            )
            geo_response.raise_for_status()
            geo = geo_response.json()

            if not geo.get("results"):
                st.error(
                    "Couldn't find that city — check the spelling in "
                    "Settings → Location."
                )
            else:
                loc = geo["results"][0]
                lat = float(loc["latitude"])
                lon = float(loc["longitude"])

                # 2. Search OpenStreetMap for nodes, ways and relations.
                #    This is important because parks are often stored as ways.
                query = f"""
[out:json][timeout:30];
(
  nwr["leisure"="park"](around:10000,{lat},{lon});
  nwr["leisure"="nature_reserve"](around:10000,{lat},{lon});
  nwr["leisure"="garden"](around:10000,{lat},{lon});
  nwr["natural"="wood"](around:10000,{lat},{lon});
  nwr["natural"="heath"](around:10000,{lat},{lon});
  nwr["tourism"="viewpoint"](around:10000,{lat},{lon});
  nwr["route"="hiking"](around:10000,{lat},{lon});
);
out center tags;
"""

                # 3. Use fallback Overpass servers in case one is busy.
                overpass_servers = [
                    "https://overpass-api.de/api/interpreter",
                    "https://overpass.kumi.systems/api/interpreter",
                    "https://overpass.private.coffee/api/interpreter",
                ]

                osm_data = None
                last_error = None

                for server in overpass_servers:
                    try:
                        osm_response = requests.post(
                            server,
                            data={"data": query},
                            timeout=35,
                            headers={"User-Agent": "GreenStreak/1.0"},
                        )
                        osm_response.raise_for_status()
                        osm_data = osm_response.json()
                        break
                    except Exception as exc:
                        last_error = exc

                if osm_data is None:
                    st.error(
                        "Couldn't reach OpenStreetMap right now. "
                        "The map service may be temporarily busy."
                    )
                    if last_error:
                        st.caption(f"Technical detail: {last_error}")
                else:
                    elements = osm_data.get("elements", [])

                    category_emoji = {
                        "park": "🏞️",
                        "nature_reserve": "🌲",
                        "garden": "🌷",
                        "wood": "🌳",
                        "heath": "🌿",
                        "viewpoint": "🔭",
                        "hiking": "🥾",
                    }

                    results = []
                    seen_names = set()

                    for element in elements:
                        tags = element.get("tags", {})
                        name = tags.get("name")

                        if not name:
                            continue

                        name_key = name.strip().lower()
                        if name_key in seen_names:
                            continue
                        seen_names.add(name_key)

                        # Nodes have lat/lon.
                        # Ways/relations have center.lat/center.lon.
                        if "lat" in element and "lon" in element:
                            element_lat = element["lat"]
                            element_lon = element["lon"]
                        elif "center" in element:
                            center = element["center"]
                            element_lat = center.get("lat")
                            element_lon = center.get("lon")
                        else:
                            continue

                        if element_lat is None or element_lon is None:
                            continue

                        element_lat = float(element_lat)
                        element_lon = float(element_lon)

                        # Haversine distance in kilometres.
                        distance = (
                            2
                            * 6371
                            * math.asin(
                                math.sqrt(
                                    math.sin(
                                        math.radians(element_lat - lat) / 2
                                    ) ** 2
                                    + math.cos(math.radians(lat))
                                    * math.cos(math.radians(element_lat))
                                    * math.sin(
                                        math.radians(element_lon - lon) / 2
                                    ) ** 2
                                )
                            )
                        )

                        if tags.get("leisure") == "park":
                            category = "park"
                        elif tags.get("leisure") == "nature_reserve":
                            category = "nature_reserve"
                        elif tags.get("leisure") == "garden":
                            category = "garden"
                        elif tags.get("natural") == "wood":
                            category = "wood"
                        elif tags.get("natural") == "heath":
                            category = "heath"
                        elif tags.get("tourism") == "viewpoint":
                            category = "viewpoint"
                        elif tags.get("route") == "hiking":
                            category = "hiking"
                        else:
                            category = "nature spot"

                        results.append(
                            {
                                "name": name,
                                "category": category,
                                "distance": distance,
                                "lat": element_lat,
                                "lon": element_lon,
                            }
                        )

                    results.sort(key=lambda item: item["distance"])

                    if not results:
                        st.warning(
                            f"No named nature spots were found within 10 km "
                            f"of {st.session_state.city}."
                        )
                        st.info(
                            "Try another nearby city or check your location "
                            "spelling."
                        )
                    else:
                        st.success(
                            f"Found {len(results)} nature spots near "
                            f"{st.session_state.city}! 🌿"
                        )

                        for spot in results[:15]:
                            emoji = category_emoji.get(
                                spot["category"], "📍"
                            )

                            map_url = (
                                "https://www.openstreetmap.org/"
                                f"?mlat={spot['lat']}&mlon={spot['lon']}"
                                f"#map=17/{spot['lat']}/{spot['lon']}"
                            )

                            st.markdown(
                                f"""
                                <div class="explore-row">
                                    {emoji} <b>{spot['name']}</b><br>
                                    <span style="font-size:12px;">
                                        {spot['category'].replace('_', ' ').title()}
                                        · {spot['distance']:.1f} km away
                                    </span><br>
                                    <a href="{map_url}" target="_blank"
                                       style="font-size:12px;">
                                        🗺️ View on OpenStreetMap
                                    </a>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

        except requests.exceptions.Timeout:
            st.error(
                "The nature service took too long to respond. "
                "Please try again."
            )
        except requests.exceptions.RequestException as exc:
            st.error("Couldn't connect to the nature-spot service.")
            st.caption(f"Connection error: {exc}")
        except Exception as exc:
            st.error(
                "Something went wrong while finding nature spots."
            )
            st.caption(f"Technical detail: {exc}")

st.markdown("<div class='footer-note'>🌱 Made with Claude for OregonHacks · GreenStreak</div>", unsafe_allow_html=True)