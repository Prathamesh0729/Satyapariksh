# Fake News Detector — Website

This is the web version of the Python/Tkinter detector.

## Project structure

- `app.py` — Flask backend + ML model
- `templates/index.html` — website UI
- `static/style.css` — styling
- `static/app.js` — browser interaction
- `news_dataset.csv` — demo dataset included for testing
- `requirements.txt` — Python packages

## Run in VS Code / Windows

Open a terminal in this folder:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open:

http://127.0.0.1:5000

The first launch trains the model and saves `fake_news_model.pkl`.

## Use your own dataset

Replace `news_dataset.csv` with your real dataset.

It must contain:

```text
text,label
```

Labels must be `REAL` or `FAKE`.

For meaningful evaluation, use verified articles/claims rather than synthetic examples. The included dataset is only for demonstrating that the website works.

## Important

The model predicts linguistic patterns. It does not independently verify current events. A high probability is not proof. For a serious fact-checking system, add an evidence/retrieval layer that checks primary sources.
