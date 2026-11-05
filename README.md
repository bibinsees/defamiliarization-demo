# Defamiliarization Attack — Interactive Demo

A ChatGPT-style web demo for the paper **"Defamiliarization Attack: Literary Theory Enabled Discussion of LLM Safety"**.

📄 **Paper:** [Electronics (MDPI), 15(5), 1047](https://www.mdpi.com/2079-9292/15/5/1047)
💻 **Full research code and datasets:** [bibinsees/Adversarial-attack](https://github.com/bibinsees/Adversarial-attack)

## What the demo shows

One AI model (the **attacker**) holds a friendly, harmless-sounding conversation with another AI model (the **target**). Turn by turn it steers the chat toward a harmful goal (planning a home burglary) without ever asking for it directly. When the conversation ends, two independent AI judges decide whether the target was tricked into giving unsafe advice.

- 🎭 **Attacker** messages appear on the right, like a user typing in ChatGPT.
- 🤖 **Target** replies appear on the left.
- 🔴 Phrases related to the harmful goal are **highlighted in red**, so the audience can follow how the conversation drifts.
- 🚨 / ✅ A final card shows the judges' verdict: **UNSAFE** or **SAFE**.

Older models (GPT‑4.x) are usually talked into it, while newer models (GPT‑5.x) keep refusing.

## Quick start

Requires Python 3.9+.

```bash
git clone https://github.com/bibinsees/defamiliarization-demo.git
cd defamiliarization-demo
pip install -r requirements.txt
python -m streamlit run demo_app.py
```

Your browser opens at `http://localhost:8501`.

## Modes

| Mode | Needs | What it does |
|---|---|---|
| **Replay (pre-recorded)** | Nothing | Plays back one of the 7 recorded conversations from the paper with a typing animation. Instant and reliable for live presentations. |
| **Live (calls OpenAI)** | OpenAI API key | Runs a new attack against the model you choose, then asks the judges. Takes 1–3 minutes and costs a few cents. |

For Live mode, copy `.env.example` to `.env` and add your key:

```
OPENAI_API_KEY=sk-...
```

A finished live run can be saved with **💾 Save this run as a replay** (written to `demo_replays/`) and replayed later.

## Presenter controls (sidebar)

- **Auto-play / Click to advance:** let the conversation type itself, or step through it one message at a time while you explain.
- **Typing speed**
- **Hide target's later answers** (on by default): collapses the target's replies from a chosen turn onward behind "click to reveal", so harmful text only appears on screen if you choose to show it.
- **🔴 Highlight unsafe parts in red** (on by default)
- **🌙 Dark mode**

Suggested order for a talk: replay **gpt‑4‑turbo** (UNSAFE), then **gpt‑5.2** (SAFE).

## Files

```
demo_app.py                    # Streamlit demo UI
AutoDefa.py                    # automated attack pipeline (used by Live mode; also runs on its own: python AutoDefa.py)
dataset_AutoDefa/home_theft/   # recorded attack conversations + judge verdicts (Replay mode)
.streamlit/config.toml         # default light theme
requirements.txt
.env.example
```

## Authors

Bibin Babu, Yana Agafonova, Sebastian Biedermann, Ivan Yamshchikov

## Ethics and disclaimer

This work is for AI safety research and education only. It shows how current language models can be manipulated so that their safety mechanisms can be improved. The recorded transcripts contain model outputs that describe unsafe behaviour. Do not use these techniques to cause harm.
