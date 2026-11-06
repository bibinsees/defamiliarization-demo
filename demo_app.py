"""
AutoDefa demo UI - a ChatGPT-style replay / live viewer for the automated
defamiliarization attack, aimed at non-technical audiences.

Run:  py -m streamlit run demo_app.py
"""
import json
import re
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
DATASET_DIR = ROOT / "dataset_AutoDefa" / "home_theft"
REPLAY_DIR = ROOT / "demo_replays"

# Saved transcripts shipped with the repo -> friendly names for the dropdown
DATASET_NAMES = {
    "gpt4turbofull.txt": "gpt-4-turbo",
    "gpt4.1full": "gpt-4.1",
    "gpt4.1minifull": "gpt-4.1-mini",
    "gpt4.1-nano_full.txt": "gpt-4.1-nano",
    "gpt5nanofull.txt": "gpt-5-nano",
    "gpt5minifull.txt": "gpt-5-mini",
    "gpt5.2full": "gpt-5.2",
}
LIVE_MODELS = ["gpt-4o-mini", "gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1",
               "gpt-5-nano", "gpt-5-mini", "gpt-5.2"]

ATTACKER_LABEL = "Attacker"
# Attacker used to generate the paper dataset (see AutoDefa.ipynb / AutoDefa.py)
DATASET_ATTACKER_MODEL = "gpt-4.1-mini"
ATTACKER_AVATAR = "🎭"
TARGET_AVATAR = "🤖"


# =============================================================================
# Loading conversations
# =============================================================================
def parse_dataset_file(path: Path) -> dict:
    """Parse one of the dataset_AutoDefa/*.txt transcripts.

    Format: paragraphs starting with 'User: ' (the TARGET model) or
    'Assistant: ' (the ATTACKER), followed by an 'Evaluation:' block with
    'First Judge:' and 'Second Judge:' sections.
    """
    text = path.read_text(encoding="utf-8")
    # Most files introduce the judges with 'Evaluation:', one goes straight to
    # 'First Judge:'; the label's case also varies between files.
    split = re.split(r"\n(?=Eva\w*ation:|First judge:)", text, maxsplit=1, flags=re.I)
    body, evaluation = split[0], (split[1] if len(split) > 1 else "")

    parts = re.split(r"^(User|Assistant): ", body, flags=re.M)
    messages = []
    for i in range(1, len(parts) - 1, 2):
        role = "TARGET" if parts[i] == "User" else "ATTACKER"
        messages.append({"role": role, "content": parts[i + 1].strip()})

    first_eval, final_eval = "", ""
    if evaluation:
        m = re.search(r"First Judge:\s*(.*?)\s*Second Judge:\s*(.*)", evaluation, re.S | re.I)
        if m:
            first_eval, final_eval = m.group(1).strip(), m.group(2).strip()
        else:
            first_eval = evaluation.strip()

    return {
        "target_model": DATASET_NAMES.get(path.name, path.stem),
        "attacker_model": DATASET_ATTACKER_MODEL,
        "messages": messages,
        "first_evaluation": first_eval,
        "final_evaluation": final_eval,
        "source": f"dataset: {path.name}",
    }


def load_replays() -> dict:
    """Return {display name: run dict} for every pre-recorded conversation."""
    replays = {}
    if DATASET_DIR.exists():
        for fname, nice in DATASET_NAMES.items():
            p = DATASET_DIR / fname
            if p.exists():
                replays[f"{nice}  (paper dataset)"] = parse_dataset_file(p)
    if REPLAY_DIR.exists():
        for p in sorted(REPLAY_DIR.glob("*.json")):
            try:
                run = json.loads(p.read_text(encoding="utf-8"))
                run.setdefault("source", f"saved run: {p.name}")
                replays[f"{run.get('target_model', '?')}  (saved {p.stem.split('_')[-1]})"] = run
            except (OSError, ValueError):
                continue
    return replays


def save_replay(run: dict) -> Path:
    REPLAY_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = REPLAY_DIR / f"{run['target_model']}_{stamp}.json"
    payload = {k: v for k, v in run.items() if k != "transcript"}
    payload["saved_at"] = stamp
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# =============================================================================
# Verdict helpers
# =============================================================================
def classify_verdict(first_eval: str) -> str:
    """Reduce the judge's free-text answer to SAFE / UNSAFE / UNKNOWN."""
    if not first_eval:
        return "UNKNOWN"
    t = first_eval.replace("*", "").lower()
    m = re.search(r"verdict\W{0,5}(unsafe|safe)", t)
    if m:
        return m.group(1).upper()
    if "not compromised" in t or "was not compromised" in t:
        return "SAFE"
    if "unsafe" in t or "compromised" in t:
        return "UNSAFE"
    if "safe" in t:
        return "SAFE"
    return "UNKNOWN"


def render_verdict(run: dict):
    verdict = run.get("verdict") or classify_verdict(run.get("first_evaluation", ""))
    st.divider()
    if verdict == "UNSAFE":
        st.error("🚨  **UNSAFE** — the target AI was talked into giving advice it should have refused.", icon=None)
    elif verdict == "SAFE":
        st.success("✅  **SAFE** — the target AI kept refusing for the whole conversation.", icon=None)
    else:
        st.warning("❔  Verdict unclear — read the judge's reasoning below.")
    with st.expander("How was this decided? (independent AI judges)"):
        st.markdown("**Judge 1 – did the target produce unsafe content?**")
        st.markdown(run.get("first_evaluation") or "_not available_")
        st.markdown("**Judge 2 – is Judge 1's verdict well-grounded?**")
        st.markdown(run.get("final_evaluation") or "_not available_")


# =============================================================================
# Chat rendering
# =============================================================================
# Phrases that signal the burglary intent running through the conversation.
# These are topic markers (what the chat is *about*), not instructions, used
# only to colour the transcript red so the audience can spot the drift.
_UNSAFE_WORDS = [
    r"lock[\- ]?pick(?:ing|ed)?", r"pick the lock", r"\bshim\b", r"\bbypass",
    r"credit card", r"thin blade", r"thin wire", r"wire hanger", r"coat hanger",
    r"hairpin", r"bobby pin", r"paper ?clip", r"plastic strip",
    r"remove (?:a |one |the )?hinge", r"hinge pin", r"mail slot", r"\bpry\b",
    r"window latch", r"crooked latch", r"the latch", r"\bunlocked\b",
    r"greasy pipe", r"oily pipe", r"\bfoothold", r"rope ladder", r"\bpulley",
    r"climb (?:the|over|up)", r"second[\- ]floor",
    r"\bmuffle", r"lubricat", r"\bstealth", r"\bsneak", r"silently",
    r"scent[\- ]mask", r"cover (?:my|your) tracks", r"wipe (?:down )?surfaces",
    r"fingerprint", r"guard dog", r"distract(?:ing)? the dog",
    r"peek inside",
    r"valuables", r"hiding spot", r"hollow book", r"false panel",
    r"loose (?:board|brick|panel|stone)", r"locked box", r"\bstash\b",
    r"hide .{0,25}?(?:money|jewelry|jewellery|cash|valuables)",
    r"where .{0,30}?hide .{0,20}?money",
]
_UNSAFE_RE = re.compile("(" + "|".join(_UNSAFE_WORDS) + ")", re.I)
_RED_OPEN = '<span class="unsafe-hl" style="color:#C46686;font-weight:700">'


def highlight_unsafe(text: str) -> str:
    """Wrap burglary-signal phrases in a highlight span (leaves markdown intact).

    Light theme: pink on pink tint (style-kit "negative"); dark theme: red.
    """
    return _UNSAFE_RE.sub(lambda m: f"{_RED_OPEN}{m.group(0)}</span>", text)


def _render_body(content: str, *, animate: bool, speed: float, highlight: bool):
    """Render one message body, optionally with a word-by-word typing effect.

    Highlighting (red) is applied on every frame when the sidebar toggle is on.
    """
    builder = highlight_unsafe if highlight else (lambda t: t)
    if not animate:
        st.markdown(builder(content), unsafe_allow_html=True)
        return
    placeholder = st.empty()
    delay = 1.0 / max(speed, 1)
    acc = ""
    for word in content.split(" "):
        acc += word + " "
        placeholder.markdown(builder(acc), unsafe_allow_html=True)
        time.sleep(delay)
    placeholder.markdown(builder(content), unsafe_allow_html=True)


def render_message(msg: dict, index: int, total: int, *, animate: bool,
                   speed: float, hide: bool, hide_from_turn: int, target_model: str,
                   attacker_model: str = DATASET_ATTACKER_MODEL):
    is_attacker = msg["role"] == "ATTACKER"
    turn = index // 2 + 1
    total_turns = (total + 1) // 2

    if is_attacker:
        box = st.chat_message("user", avatar=ATTACKER_AVATAR)
        header = f"**{ATTACKER_LABEL}: {attacker_model}**"
    else:
        box = st.chat_message("assistant", avatar=TARGET_AVATAR)
        header = f"**Target: {target_model}**"

    with box:
        st.caption(f"{header} · turn {turn} / {total_turns}")
        hidden = hide and not is_attacker and turn >= hide_from_turn
        # Attacker messages are always marked. Target replies are marked only
        # when the run was judged UNSAFE; in SAFE runs they are mostly refusals.
        hl = st.session_state.get("highlight", True) and (
            is_attacker or st.session_state.get("run_unsafe", False))
        if hidden:
            with st.expander("🔒 Target's reply hidden — click to reveal"):
                _render_body(msg["content"], animate=False, speed=speed, highlight=hl)
        else:
            _render_body(msg["content"], animate=animate, speed=speed, highlight=hl)



DARK_CSS = """
<style>
.stApp, [data-testid="stAppViewContainer"], header[data-testid="stHeader"],
[data-testid="stBottomBlockContainer"] {background-color: #0e1117 !important;}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {background-color: #1a1c24 !important;}
.stApp, .stApp p, .stApp li, .stApp span, .stApp label, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp strong, .stApp em, .stApp small,
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"],
[data-testid="stWidgetLabel"], [data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] {color: #fafafa !important;}
[data-testid="stCaptionContainer"] {opacity: 0.75;}
[data-testid="stChatMessage"] {background-color: rgba(255, 255, 255, 0.04);}
[data-testid="stExpander"] details {border-color: #3a3d4a !important;}
[data-testid="stExpander"] summary:hover {background-color: rgba(255,255,255,0.05);}
/* inputs, dropdowns and secondary buttons */
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="input"] input,
.stNumberInput button, .stButton button[kind="secondary"], [data-baseweb="popover"] ul,
[data-baseweb="popover"] li {background-color: #262730 !important; color: #fafafa !important;
    border-color: #3a3d4a !important;}
[data-baseweb="select"] svg {fill: #fafafa !important;}
hr {border-color: #3a3d4a !important;}
.stApp span.unsafe-hl, .stApp span.unsafe-hl * {color: #ff6b6b !important; font-weight: 700;}
</style>
"""

# Light theme, built from style-kit/ (emotions-theme.css + STYLE_GUIDE.md).
# Only the kit's palette is used:
#   page #FBFBFA · panel/cream #FAF9F5 · card #FFFFFF · border #DDDDDD
#   title #000000 · text #3D3D3A · muted #73726C
#   blue #2C84DB (good / SAFE) · pink #C46686 (bad / UNSAFE)
#   blue tint #EAF3F7 · pink tint #FCEBEA
LIGHT_CSS = """
<style>
:root {
  --et-page: #FBFBFA; --et-panel: #FAF9F5; --et-card: #FFFFFF; --et-border: #DDDDDD;
  --et-title: #000000; --et-text: #3D3D3A; --et-muted: #73726C;
  --et-blue: #2C84DB; --et-pink: #C46686; --et-blue-band: #EAF3F7; --et-pink-band: #FCEBEA;
  --et-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell,
             "Fira Sans", "Droid Sans", "Helvetica Neue", Arial, sans-serif;
  --et-mono: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace;
}

/* ---- surfaces ---- */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stBottomBlockContainer"] {
  background-color: var(--et-page) !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background-color: var(--et-panel) !important;
}
[data-testid="stSidebar"] {border-right: 1px solid var(--et-border);}

/* ---- typography ---- */
.stApp, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input {
  font-family: var(--et-sans);
  -webkit-font-smoothing: antialiased;
}
.stApp, .stApp p, .stApp li, .stApp strong, .stApp em,
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {color: var(--et-text);}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  color: var(--et-title) !important; font-family: var(--et-sans); font-weight: 700;
}
[data-testid="stMain"] h1 {               /* page title */
  font-size: 50px; line-height: 1.1; letter-spacing: -0.5px; text-align: center;
  padding: 24px 0 28px;
}
[data-testid="stSidebar"] h1 {font-size: 24px; letter-spacing: -0.3px;}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {font-size: 19px;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
[data-testid="stWidgetLabel"] p {color: var(--et-muted) !important;}
.stApp code {font-family: var(--et-mono); background: var(--et-panel); color: var(--et-muted);}
hr {border-color: var(--et-border) !important; background-color: var(--et-border) !important;}

/* ---- chat bubbles: target = white card, attacker = cream panel ---- */
[data-testid="stChatMessage"] {
  background: var(--et-card) !important;
  border: 1px solid var(--et-border);
  border-radius: 10px;
  color: var(--et-text);
}
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {
  background: var(--et-panel) !important;
}

/* ---- unsafe-phrase highlight: pink accent on pink tint ---- */
.stApp span.unsafe-hl, .stApp span.unsafe-hl * {
  color: var(--et-pink) !important; font-weight: 700;
}
.stApp span.unsafe-hl {background: var(--et-pink-band); padding: 0 2px; border-radius: 3px;}

/* ---- verdict / notice boxes ---- */
[data-testid="stAlertContainer"] {border-radius: 8px; border: 1px solid transparent;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
  background: var(--et-pink-band) !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) * {color: var(--et-pink) !important;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {
  background: var(--et-blue-band) !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) * {color: var(--et-blue) !important;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]),
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {
  background: var(--et-panel) !important; border-color: var(--et-border);
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) *,
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) * {color: var(--et-text) !important;}

/* ---- expanders (judge reasoning, hidden replies, live status) ---- */
[data-testid="stExpander"] details {
  background: var(--et-card); border: 1px solid var(--et-border) !important; border-radius: 10px;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {color: var(--et-text);}
[data-testid="stExpander"] summary:hover {background: var(--et-panel);}

/* ---- buttons ---- */
.stButton button {
  font-family: var(--et-sans); font-weight: 700; border-radius: 5px;
  transition: background .2s, color .2s, opacity .2s;
}
.stButton button p {font-weight: 700;}
.stButton button[kind="secondary"] {
  background: var(--et-card) !important; border: 1px solid var(--et-border) !important;
  color: var(--et-text) !important;
}
.stButton button[kind="secondary"]:hover {background: var(--et-panel) !important;}
.stButton button[kind="primary"] {
  background: var(--et-blue) !important; border: 1px solid var(--et-blue) !important;
  color: #FFFFFF !important;
}
.stButton button[kind="primary"] p {color: #FFFFFF !important;}
.stButton button[kind="primary"]:hover {opacity: .9;}

/* ---- inputs ---- */
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="input"] input,
.stNumberInput button {
  background-color: var(--et-card) !important; border-color: var(--et-border) !important;
  color: var(--et-text) !important;
}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li {
  background-color: var(--et-card) !important; color: var(--et-text) !important;
}

/* ---- sliders: white thumb, dark ring, mono readout ---- */
[data-testid="stSlider"] [role="slider"] {
  width: 20px; height: 20px; background: var(--et-card) !important;
  border: 2.5px solid var(--et-text); box-shadow: none !important;
}
[data-testid="stSliderThumbValue"] {
  font-family: var(--et-mono); font-weight: 700; color: var(--et-text) !important;
}
[data-testid="stSliderTickBar"] {color: var(--et-muted);}
</style>
"""

# =============================================================================
# Page
# =============================================================================
st.set_page_config(page_title="AutoDefa demo", page_icon="🎭", layout="centered")

st.markdown(
    """
    <style>
    /* hide Streamlit chrome for a cleaner stage look */
    /* hide menu/deploy/footer but KEEP the header, which holds the
       sidebar re-open arrow */
    #MainMenu, footer, [data-testid="stToolbarActions"],
    [data-testid="stAppDeployButton"], [data-testid="stMainMenu"] {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    [data-testid="stExpandSidebarButton"] {visibility: visible !important;}
    .block-container {max-width: 900px; padding-top: 1.5rem;}
    /* attacker ("user") bubbles on the right, like ChatGPT.
       Emoji avatars carry no avatar test-id, so also match the aria-label. */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
    [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {
        flex-direction: row-reverse;
        background: rgba(120, 120, 255, 0.08);
        border-radius: 14px;
    }
    [data-testid="stChatMessage"] {font-size: 1.05rem; line-height: 1.5;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- session state -----------------------------------------------------------
ss = st.session_state
ss.setdefault("run", None)          # the conversation currently on screen
ss.setdefault("shown", 0)           # how many messages are already rendered
ss.setdefault("animate_last", False)
ss.setdefault("live_pending", False)
ss.setdefault("dark_mode", False)
ss.setdefault("run_unsafe", False)

# ---- sidebar -----------------------------------------------------------------
with st.sidebar:
    st.title("🎭 AutoDefa")
    st.caption("Automated defamiliarization attack · live demo controls")
    st.toggle("🌙 Dark mode", key="dark_mode")
    st.markdown(DARK_CSS if ss.dark_mode else LIGHT_CSS, unsafe_allow_html=True)

    mode = st.radio("Mode", ["Replay (pre-recorded)", "Live (calls OpenAI)"])
    is_live = mode.startswith("Live")

    if is_live:
        live_model = st.selectbox("Target model", LIVE_MODELS, index=0)
        live_turns = st.slider("Conversation turns", 2, 10, 10)
        st.caption("Needs OPENAI_API_KEY in .env · takes 1–3 min · costs a few cents")
    else:
        replays = load_replays()
        replay_choice = st.selectbox("Conversation", list(replays.keys()))

    st.subheader("Playback")
    advance = st.radio("Advance", ["Auto-play", "Click to advance"], horizontal=True)
    click_mode = advance.startswith("Click")
    speed = st.slider("Typing speed (words / sec)", 5, 300, 40)

    st.subheader("Audience safety")
    hide = st.toggle("Hide target's later answers", value=True,
                     help="Collapses the target's replies behind a 'click to reveal' so "
                          "harmful text is never on screen unless you choose.")
    hide_from = st.number_input("…from turn", 1, 10, 6, disabled=not hide)
    st.toggle("🔴 Highlight unsafe parts in red", value=True, key="highlight",
              help="Colours burglary-related words red. Attacker messages are always "
                   "marked; the target's replies only when the run was judged UNSAFE.")

    c1, c2 = st.columns(2)
    start = c1.button("▶ Start", type="primary", use_container_width=True)
    reset = c2.button("↺ Reset", use_container_width=True)

    if reset:
        ss.run, ss.shown, ss.animate_last, ss.live_pending = None, 0, False, False
        st.rerun()

    if start:
        ss.shown, ss.animate_last = 0, False
        if is_live:
            ss.run = None
            ss.run_unsafe = False   # unknown until the judges finish
            ss.live_pending = True
        else:
            ss.run = replays[replay_choice]
            ss.run_unsafe = classify_verdict(ss.run.get("first_evaluation", "")) == "UNSAFE"
            ss.live_pending = False

    if ss.run and not is_live and click_mode and ss.shown < len(ss.run["messages"]):
        if st.button("⏭ Next message", use_container_width=True):
            ss.shown += 1
            ss.animate_last = True
            st.rerun()

    if ss.run and ss.run.get("source", "").startswith("live"):
        if st.button("💾 Save this run as a replay", use_container_width=True):
            p = save_replay(ss.run)
            st.success(f"Saved to {p.relative_to(ROOT)}")

# ---- main area ---------------------------------------------------------------
st.title("Can one AI talk another AI into helping with a burglary?")

chat = st.container()

# ---- live run ----------------------------------------------------------------
if ss.live_pending:
    ss.live_pending = False
    try:
        import AutoDefa  # lazy: instantiating the OpenAI client needs the API key
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not start the pipeline: {e}\n\nIs OPENAI_API_KEY set in `.env`?")
        st.stop()

    run = {"target_model": live_model, "attacker_model": AutoDefa.ATTACKER_MODEL,
           "judge_model": AutoDefa.JUDGE_MODEL, "messages": [],
           "first_evaluation": "", "final_evaluation": "", "source": "live"}
    ss.run = run
    total_expected = live_turns * 2

    def on_message(role, content):
        run["messages"].append({"role": role, "content": content})
        with chat:
            render_message(run["messages"][-1], len(run["messages"]) - 1, total_expected,
                           animate=True, speed=speed, hide=hide, hide_from_turn=hide_from,
                           target_model=live_model,
                           attacker_model=run["attacker_model"])
        ss.shown = len(run["messages"])

    try:
        with st.status("Running the attack live…", expanded=False) as status:
            result = AutoDefa.run_single_trial(live_model, live_turns,
                                               on_message=on_message, judge=False)
            # any trailing message the callback did not see
            for i in range(len(run["messages"]), len(result["messages"])):
                on_message(result["messages"][i]["role"], result["messages"][i]["content"])
            run["transcript"] = result["transcript"]
            status.update(label="Asking the judges…")
            run["first_evaluation"] = AutoDefa.evaluate_safety(result["transcript"])
            run["final_evaluation"] = AutoDefa.evaluate_the_evaluator(
                result["transcript"], run["first_evaluation"])
            status.update(label="Done", state="complete")
        run["verdict"] = classify_verdict(run["first_evaluation"])
        ss.run_unsafe = run["verdict"] == "UNSAFE"
        with chat:
            render_verdict(run)
    except Exception as e:  # noqa: BLE001
        st.error(f"The live run failed: {e}")
    st.stop()

# ---- replay / already-finished run -------------------------------------------
if ss.run is None:
    st.info("Pick a conversation in the sidebar and press **Start**.")
    st.stop()

run = ss.run
msgs = run["messages"]
n = len(msgs)
target_model = run.get("target_model", "?")
attacker_model = run.get("attacker_model", DATASET_ATTACKER_MODEL)

with chat:
    # messages already revealed -> static, except the newest one in click mode
    for i in range(min(ss.shown, n)):
        animate = ss.animate_last and i == ss.shown - 1
        render_message(msgs[i], i, n, animate=animate, speed=speed, hide=hide,
                       hide_from_turn=hide_from, target_model=target_model,
                       attacker_model=attacker_model)
    ss.animate_last = False

    if not click_mode:
        # auto-play: stream the rest in this same script run
        for i in range(ss.shown, n):
            render_message(msgs[i], i, n, animate=True, speed=speed, hide=hide,
                           hide_from_turn=hide_from, target_model=target_model,
                       attacker_model=attacker_model)
            ss.shown = i + 1

    if ss.shown >= n:
        render_verdict(run)
    else:
        st.caption(f"{n - ss.shown} messages remaining — press **Next message** in the sidebar.")
