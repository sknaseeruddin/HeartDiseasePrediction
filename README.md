# HeartCare — Heart Disease Model Demo & Daily Wellness Tracker

HeartCare is an educational Streamlit application combining a saved machine-learning model demonstration with daily self-reported wellness tracking.

## Features
- Registration/login using PBKDF2-HMAC password hashing
- Preserves existing SQLite `users` and `records` tables
- Daily wellness entries for mood, sleep, activity, and stress
- One wellness entry per user/date, enforced by a database uniqueness constraint
- Weekly trend charts and summaries
- Accuracy, precision, recall, F1-score, confusion matrix, and classification report
- CSV export of wellness history
- Streamlit dashboard and navigation

## Project files
Keep these files in the same folder:
- `app.py`
- `heart.csv`
- `heart_model.pkl`
- `train_model.py` (if you want to retain the training script)
- `requirements.txt`

## Run locally (Windows CMD)
```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```
The app loads the existing `heart_model.pkl`; it does not retrain the model.

## GitHub
Do not commit `.venv/`, `heartcare.db`, real personal records, passwords, or secrets. `.gitignore` excludes the local SQLite database. Use fictional data for demonstrations.

```bash
git add app.py train_model.py heart.csv heart_model.pkl requirements.txt README.md .gitignore .streamlit/config.toml screenshots
git commit -m "Upgrade HeartCare dashboard and wellness analytics"
git push
```
If Git has not been initialized, create a repository on GitHub and follow its instructions to add the remote and push `main`.

## Streamlit Community Cloud
1. Push the source files, `heart.csv`, `heart_model.pkl`, and `requirements.txt` to GitHub.
2. Connect the repository in Streamlit Community Cloud.
3. Set the main file path to `app.py`, then deploy.
4. Review app logs if dependency/model loading errors occur.

**Persistence limitation:** this app uses a local SQLite database. Hosted filesystems may be ephemeral, so user accounts and entries may be lost after restarts or redeployments. For a persistent public app, use a managed database before relying on it. Do not store real sensitive health information in this prototype.

## Screenshots
Run the app and capture Dashboard, Daily Wellness, Wellness Analytics, and Model Evaluation pages. Save the images in `screenshots/` and embed them here if desired.

## Disclaimer
For educational and portfolio demonstration only. The model is not clinically validated and must not be used to diagnose disease or make healthcare decisions. Wellness charts are based on self-reported entries, not clinical measurements.
