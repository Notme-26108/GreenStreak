import streamlit as st
import json
import os
import random
from datetime import date, timedelta

st.set_page_config(page_title="GreenStreak", page_icon="🌱", layout="centered")

DATA_FILE = "greenstreak_data.json"

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
        "leaves": st.session_state.leaves,
        "total_leaves_earned": st.session_state.total_leaves_earned,
        "completed_today": st.session_state.completed_today,
        "streak_counted_today": st.session_state.streak_counted_today,
        "garden": st.session_state.garden,
        "last_active_date": st.session_state.last_active_date,
        "day_count": st.session_state.day_count,
        "impact": st.session_state.impact,
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ---------- INITIALIZE STATE (load once) ----------
if "loaded" not in st.session_state:
    saved = load_data()
    if saved:
        st.session_state.name = saved["name"]
        st.session_state.avatar = saved["avatar"]
        st.session_state.streak = saved["streak"]
        st.session_state.leaves = saved["leaves"]
        st.session_state.total_leaves_earned = saved.get("total_leaves_earned", saved["leaves"])
        st.session_state.completed_today = saved["completed_today"]
        st.session_state.streak_counted_today = saved["streak_counted_today"]
        st.session_state.garden = saved["garden"]
        st.session_state.last_active_date = saved["last_active_date"]
        st.session_state.day_count = saved.get("day_count", 0)
        st.session_state.impact = saved.get("impact", {"litter_pieces": 0, "minutes_outside": 0, "nature_spots": 0})
    else:
        st.session_state.name = ""
        st.session_state.avatar = "🧑‍🌾"
        st.session_state.streak = 0
        st.session_state.leaves = 0
        st.session_state.total_leaves_earned = 0
        st.session_state.completed_today = []
        st.session_state.streak_counted_today = False
        st.session_state.garden = [None] * 9  # each slot: None or {"type": "🌼", "stage": 0}
        st.session_state.last_active_date = date.today().isoformat()
        st.session_state.day_count = 0
        st.session_state.impact = {"litter_pieces": 0, "minutes_outside": 0, "nature_spots": 0}
    st.session_state.loaded = True

# ---------- REAL DAILY RESET (based on actual date) ----------
today_str = date.today().isoformat()
if st.session_state.last_active_date != today_str:
    if not st.session_state.streak_counted_today:
        st.session_state.streak = 0  # missed a day
    st.session_state.completed_today = []
    st.session_state.streak_counted_today = False
    st.session_state.last_active_date = today_str
    st.session_state.day_count += 1

    # grow every planted, not-yet-bloomed plot by one stage each real day
    for plot in st.session_state.garden:
        if plot is not None and plot["stage"] < 2:
            plot["stage"] += 1

    save_data()

# ---------- CSS ----------
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Quicksand', sans-serif; }
.stApp { background: linear-gradient(180deg, #FDF6EC 0%, #F3EFE0 100%); }
.stApp, .stApp p, .stApp span, .stApp label, .stApp div, .stApp li {
    color: #4A5D46 !important;
}
h1 { color: #5B7B5A !important; font-weight: 700 !important; text-align: center; }
h3 { color: #6E8B6A !important; }

.stMetric {
    background-color: #FFFDF8;
    border-radius: 20px;
    padding: 10px;
    border: 2px solid #E6DCC3;
}
div[data-testid="stMetricValue"] { color: #B5793D !important; }

.quest-card {
    background-color: #FFFDF8;
    border-radius: 18px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border: 2px solid #E6DCC3;
    box-shadow: 2px 2px 0px #E6DCC3;
}

.stButton>button {
    background-color: #A8C69F;
    color: white !important;
    border-radius: 30px;
    border: none;
    padding: 6px 18px;
    font-weight: 600;
    box-shadow: 2px 2px 0px #7FA377;
}
.stButton>button:hover { background-color: #93B888; color: white !important; }

.mascot-box {
    text-align: center;
    background-color: #F0EAD6;
    border-radius: 24px;
    padding: 16px;
    margin-bottom: 18px;
    border: 2px solid #E6DCC3;
}
.mascot-emoji { font-size: 60px; animation: bob 2s ease-in-out infinite; }
@keyframes bob { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-8px); } }
.mascot-speech { font-weight: 600; color: #6E8B6A !important; margin-top: 4px; }

.st-key-garden_scene {
    position: relative;
    background: linear-gradient(180deg, #BEE3F5 0%, #BEE3F5 18%, #DCEFBE 18%, #A9D68C 100%) !important;
    border-radius: 24px !important;
    padding: 30px 16px 22px 16px !important;
    border: 5px solid #A9764F !important;
    overflow: hidden;
}
.st-key-garden_scene::before {
    content: "🌳";
    position: absolute;
    top: 2px;
    left: 6px;
    font-size: 32px;
}
.st-key-garden_scene::after {
    content: "☀️";
    position: absolute;
    top: 4px;
    right: 10px;
    font-size: 26px;
}
.garden-fence {
    width: 100%;
    height: 12px;
    margin-top: 4px;
    background-image: repeating-linear-gradient(90deg, #C9A66B 0px, #C9A66B 5px, transparent 5px, transparent 13px);
}
.garden-butterfly {
    position: absolute;
    top: 14px;
    font-size: 18px;
    animation: flutter 9s linear infinite;
}
@keyframes flutter {
    0% { left: -5%; transform: translateY(0px); }
    25% { transform: translateY(-6px); }
    50% { transform: translateY(0px); }
    75% { transform: translateY(-6px); }
    100% { left: 100%; transform: translateY(0px); }
}
.garden-plot {
    text-align: center;
    font-size: 38px;
    background: transparent;
    border: none;
    margin: 2px 2px 0px 2px;
    padding: 0;
    filter: drop-shadow(1px 3px 1px rgba(60,45,20,0.25));
    animation: grow-in 0.6s ease;
}
.empty-plot {
    text-align: center;
    font-size: 20px;
    color: #EAF4DE !important;
    opacity: 0.9;
    margin: 10px 2px 0px 2px;
}
.plot-stage-label {
    text-align: center;
    font-size: 11px;
    color: #8A7A55 !important;
    margin: 0px 4px 8px 4px;
}
@keyframes grow-in { 0% { transform: scale(0.7); opacity: 0.5; } 100% { transform: scale(1); opacity: 1; } }

@keyframes sparkle {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.bloom-ready { animation: grow-in 0.6s ease, sparkle 1.5s ease-in-out infinite; }

@keyframes dig {
    0%, 100% { transform: rotate(0deg) translateY(0px); }
    25% { transform: rotate(-18deg) translateY(2px); }
    50% { transform: rotate(0deg) translateY(5px); }
    75% { transform: rotate(18deg) translateY(2px); }
}
.gardener-dig { animation: dig 0.9s ease-in-out infinite; }

@keyframes celebrate-bounce {
    0%, 100% { transform: translateY(0) scale(1); }
    30% { transform: translateY(-12px) scale(1.15); }
    60% { transform: translateY(0) scale(1); }
}
.gardener-celebrate { animation: celebrate-bounce 0.7s ease-in-out infinite; }

.impact-card {
    background-color: #FFFDF8;
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 10px;
    border: 2px solid #E6DCC3;
    text-align: center;
}
.impact-number {
    font-size: 30px;
    font-weight: 700;
    color: #B5793D !important;
}
.impact-label {
    font-size: 13px;
    color: #6E8B6A !important;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

st.title("🌱 GreenStreak")
st.markdown("<p style='text-align:center;'>a cozy little garden that grows with you 🍃</p>", unsafe_allow_html=True)

# ---------- PROFILE (first-time setup) ----------
AVATAR_OPTIONS = {
    "🧑‍🌾 Human Gardener": "🧑‍🌾",
    "🐰 Bunny Gardener": "🐰",
    "🦊 Fox Gardener": "🦊",
}

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

# ---------- QUEST POOL (randomized daily via day_count, not tied to real calendar date) ----------
# Each quest can optionally map to an "impact" stat: (impact_key, amount added per completion)
all_quests = [
    {"id": "outside", "text": "Spend 10 minutes outside", "emoji": "🌤️", "reward": 5, "impact": ("minutes_outside", 10)},
    {"id": "spot", "text": "Spot one bird or plant", "emoji": "🐦", "reward": 7, "impact": ("nature_spots", 1)},
    {"id": "declutter", "text": "Pick up 3 pieces of litter", "emoji": "🧹", "reward": 10, "impact": ("litter_pieces", 3)},
    {"id": "water", "text": "Drink water while sitting outside", "emoji": "💧", "reward": 5, "impact": None},
    {"id": "sketch", "text": "Sketch or photograph a leaf", "emoji": "🍂", "reward": 7, "impact": ("nature_spots", 1)},
    {"id": "walk", "text": "Take a short walk in a green space", "emoji": "🚶", "reward": 7, "impact": ("minutes_outside", 10)},
    {"id": "sky", "text": "Watch the sky for 5 minutes, no phone", "emoji": "☁️", "reward": 5, "impact": ("minutes_outside", 5)},
    {"id": "plantcare", "text": "Water a houseplant or garden plant", "emoji": "🪴", "reward": 7, "impact": None},
    {"id": "sound", "text": "Sit quietly and count natural sounds you hear", "emoji": "👂", "reward": 10, "impact": None},
]

random.seed(st.session_state.day_count)
quests = random.sample(all_quests, 3)

# ---------- MASCOT ----------
all_done_check = len(st.session_state.completed_today) == 3

if all_done_check:
    mascot_text = f"Yay {st.session_state.name}! You did it today! So proud of you!"
elif len(st.session_state.completed_today) > 0:
    mascot_text = f"You're doing great, {st.session_state.name}! Keep going!"
else:
    mascot_text = f"Hi {st.session_state.name}! Let's start today's quests together!"

# ---------- TABS ----------
tab_home, tab_garden, tab_stats = st.tabs(["🏠 Home", "🌻 Garden", "📊 Stats"])

# ================= HOME TAB =================
with tab_home:
    st.markdown(f"""
    <div class="mascot-box">
        <div class="mascot-emoji">{st.session_state.avatar}</div>
        <div class="mascot-speech">{mascot_text}</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🌿 Today's Quests")

    for quest in quests:
        already_done = quest["id"] in st.session_state.completed_today
        st.markdown("<div class='quest-card'>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"{quest['emoji']} {quest['text']}")
        with c2:
            if already_done:
                st.write("✅ Done")
            else:
                if st.button(f"+{quest['reward']} 🍃", key=quest["id"]):
                    st.session_state.completed_today.append(quest["id"])
                    st.session_state.leaves += quest["reward"]
                    st.session_state.total_leaves_earned += quest["reward"]
                    if quest["impact"] is not None:
                        key, amount = quest["impact"]
                        st.session_state.impact[key] += amount
                    save_data()
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    all_done = len(st.session_state.completed_today) == len(quests)
    if all_done and not st.session_state.streak_counted_today:
        st.session_state.streak += 1
        st.session_state.streak_counted_today = True
        save_data()
        st.balloons()
        st.rerun()

    if all_done:
        st.success("🎉 All quests complete today! Streak is safe.")

    st.divider()

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
        "🌼 Flower": 10,
        "🌷 Tulip": 20,
        "🌳 Tree": 40,
    }
    harvest_rewards = {
        "🌼": 15,
        "🌷": 30,
        "🌳": 60,
    }

    STAGE_EMOJI = {0: "🌱", 1: "🌿"}  # stage 2 uses the plant's own final emoji

    with st.container(key="garden_scene"):
        st.markdown("<div class='garden-butterfly'>🦋</div>", unsafe_allow_html=True)
        for row in range(3):
            cols = st.columns(3)
            for i in range(3):
                idx = row * 3 + i
                with cols[i]:
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
                            reward = harvest_rewards[plot["type"]]
                            if st.button(f"Harvest +{reward}🍃", key=f"harvest_{idx}"):
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
    empty_plots = [i for i, p in enumerate(st.session_state.garden) if p is None]

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
        st.success("Your garden is full! 🎉 Harvest a bloomed plant to make room.")

# ================= STATS TAB =================
with tab_stats:
    st.subheader(f"📊 {st.session_state.name}'s Stats")

    col1, col2 = st.columns(2)
    col1.metric("🔥 Streak", st.session_state.streak)
    col2.metric("🍃 Leaves", st.session_state.leaves)

    st.caption(f"🍃 {st.session_state.total_leaves_earned} leaves earned in total")

    st.divider()
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