# Retirement Calculator

This project now supports two run modes:

- Desktop app (Tkinter): `calc.py`
- Browser app (Streamlit): `web_app.py`

## 1. Run As A Web Page Locally

1. Create and activate a virtual environment:
	- Linux/macOS:
	  - `python3 -m venv venv`
	  - `source venv/bin/activate`
2. Install dependencies:
	- `pip install -r requirements.txt`
3. Start the web app:
	- `streamlit run web_app.py`
4. Open the browser URL shown in the terminal (usually `http://localhost:8501`).

## 2. Deploy Publicly (Streamlit Community Cloud)

The easiest deployment path for this app is Streamlit Community Cloud.

1. Push this project to a GitHub repository.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click "New app" and select:
	- Repository: your repo
	- Branch: your branch (for example, `main`)
	- Main file path: `web_app.py`
4. Click "Deploy".

Streamlit Cloud will install dependencies from `requirements.txt` and host your app with a public URL.

## 3. Keep Desktop App Support

If you still want the original desktop UI:

- Install system Tk packages if needed (Linux):
  - `sudo apt-get install python3-tk python3-pil python3-pil.imagetk`
- Run:
  - `python3 calc.py`
