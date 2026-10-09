# HSK Vocab Trainer — PythonAnywhere Deployment Guide

The app uses **Flask + SQLite** (no Supabase needed). Everything syncs to your own database on PythonAnywhere.

## 1. Sign up at PythonAnywhere
- Go to https://www.pythonanywhere.com → sign up (free "Beginner" account).
- Pick a username (this becomes part of your URL: `https://YOURUSERNAME.pythonanywhere.com`).

## 2. Clone the repo into PythonAnywhere
- Go to **Consoles** → click **Bash** (under "Start a new console").
- Run:
  ```bash
  git clone https://github.com/Aongkon29/hsk-vocab.git
  cd hsk-vocab
  pip install -r requirements.txt --user
  ```
  (Ignore any "already satisfied" messages.)

## 3. Create the web app
- Go to the **Web** tab → **Add a new web app** → **Next**.
- Choose **Flask** → choose **Python 3.10** (or 3.11).
- For the project path, enter: `/home/YOURUSERNAME/hsk-vocab/app.py`
  (replace `YOURUSERNAME` with your PythonAnywhere username)
- Click through to finish.

## 4. Point the WSGI at our app
- On the **Web** tab, scroll to **Code** → click the WSGI file link (e.g. `/var/www/YOURUSERNAME_pythonanywhere_com_wsgi.py`).
- Replace the **entire file** with:
  ```python
  import sys
  sys.path.insert(0, '/home/YOURUSERNAME/hsk-vocab')
  from app import app as application
  ```
  (Replace `YOURUSERNAME` with your PythonAnywhere username.)
- Save and close.

## 5. Set the working directory & virtualenv (optional but recommended)
- Still on the **Web** tab, under **Code**:
  - **Working directory**: set to `/home/YOURUSERNAME/hsk-vocab`
  - **Virtualenv**: leave empty (we installed with `--user`).
- Under **Static files**, you don't need to add anything — Flask serves `index.html` at `/`.

## 6. Reload
- Click the green **Reload** button at the top of the **Web** tab.

## 7. Open your site
Visit `https://YOURUSERNAME.pythonanywhere.com`

- Click **Create account** → pick a username + password.
- Use the **same** username + password on your phone and PC to sync.

---

## How the sync works
- All progress (stars, known/unknown, best score, theme, **Revise deck**, Revision session) is saved to `hsk.db` (SQLite) on PythonAnywhere.
- On login, your data is pulled from the server.
- Every change is pushed back immediately.
- Only your account can touch your data (token-based auth).

## Updating later (when I push new changes)
In a **Bash console**:
```bash
cd ~/hsk-vocab
git pull
pip install -r requirements.txt --user
```
Then click **Reload** on the Web tab.

---

## Troubleshooting
- **Site shows 404**: make sure the WSGI file path is correct and you reloaded.
- **"Internal Server Error"**: check the **Web** tab → **Log files** → `error.log`.
- **Login fails**: open browser DevTools → Network → check the `/api/signup` or `/api/login` response.
