# 🌱 GreenStreak

**OregonHacks 2026 submission — Theme: Nature + Tech**
Prompt: *Best technology that helps people reconnect with nature or supports environmental health*

## The Problem

Most people know spending time outdoors and taking small eco-friendly actions is good for
them and the planet, but there's no everyday nudge to actually do it. Environmental apps
tend to be either guilt-driven trackers or one-off educational tools — nothing that builds
a genuine daily habit the way apps like Duolingo do for language learning.

## The Solution

GreenStreak turns real-world nature habits into a daily game. Each day you get 3 randomized
micro-quests (spend time outside, spot a bird, pick up litter, watch the sky, etc.).
Completing them earns in-game currency ("Leaves"), builds a real, date-based streak, and
lets you grow a virtual garden that visually matures over real days — plant a seed, watch it
grow, harvest it, replant. A chibi gardener character reacts live to your garden's state.

Unlike a generic points tracker, GreenStreak converts your actions into a live
**Environmental Impact panel** — real tallies of litter picked up, minutes spent outside,
and nature moments logged — showing the tangible, cumulative effect of small daily habits.

## Key Features

- **Real, persistent streak** — tied to the actual calendar date (not a fake counter), saved
  to disk so progress survives closing the app
- **Randomized daily quests** from a pool of 9, rotating via a day-based system
- **Virtual garden with real growth stages** — seed → growing → bloom, maturing one stage
  per real day, harvestable for bonus currency
- **Reactive chibi gardener** — animates differently depending on garden state (idle, tending,
  celebrating)
- **Environmental Impact panel** — converts quest completions into cumulative real-world stats
- **Custom cottagecore-inspired UI** — built entirely with custom CSS on top of Streamlit

## Tech Stack

- **Python + Streamlit** — UI framework and app logic
- **Custom CSS** injected via `st.markdown` for the visual theme and animations
- **JSON file persistence** for streak/garden/profile data across sessions
- Pure Python standard library (`json`, `random`, `datetime`) — no external APIs required to run

## AI Use Disclosure

This project was built using **Claude (Anthropic)** as a coding assistant and collaborator
throughout the hackathon — including architecture decisions (e.g., using `st.session_state`
and `st.container(key=...)` correctly), debugging Streamlit-specific issues (rerun timing,
container nesting), CSS/animation design, and iterative feature development. All code was
reviewed, tested, and understood by the author before submission, per OregonHacks' AI use
policy.

## Running Locally

```bash
pip install streamlit
streamlit run app.py
```

Then open the local URL Streamlit provides (usually `http://localhost:8501`).

## What's Next

- Photo-proof uploads for quests, building a personal nature scrapbook
- Real weather-API-driven quests (e.g., stargazing quests on clear nights)
- Multiplayer/shared gardens for friends or classrooms
- Expanding garden plots and more plant variety
