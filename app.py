import os, json, webbrowser, urllib.parse
from flask import Flask, render_template, request, jsonify
from git import Repo
import requests
from pathlib import Path

app = Flask(__name__)
CONFIG_FILE = os.path.expanduser("~/.gitmaster_config.json")
PROJECTS_DIR = os.path.expanduser("~/GitMaster_Projects")

def get_token():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: return json.load(f).get("github_token", "")
    return ""

def save_token(token):
    with open(CONFIG_FILE, 'w') as f: json.dump({"github_token": token}, f)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/set_token', methods=['POST'])
def set_token():
    save_token(request.json.get('token'))
    return jsonify({"status": "ok", "msg": "توکن با موفقیت ذخیره شد."})

@app.route('/api/repos')
def get_repos():
    token = get_token()
    if not token: return jsonify({"error": "توکن تنظیم نشده است."})
    res = requests.get("https://api.github.com/user/repos?per_page=100", headers={"Authorization": f"token {token}"})
    return jsonify([r['name'] for r in res.json()] if res.status_code == 200 else {"error": "خطا در دریافت ریپوها."})

@app.route('/api/local_dirs')
def get_local_dirs():
    base_path = request.args.get('path')
    if not base_path:
        # مسیر پیش‌فرض بر اساس سیستم‌عامل
        if os.path.exists('/sdcard'): base_path = '/sdcard' # اندروید
        elif os.path.exists('/storage/emulated/0'): base_path = '/storage/emulated/0'
        else: base_path = os.path.expanduser("~") # کامپیوتر
    
    target_dir = Path(base_path).expanduser()
    if not target_dir.exists() or not target_dir.is_dir():
        return jsonify({"error": "مسیر پیدا نشد."})
        
    try:
        dirs = []
        for p in target_dir.iterdir():
            if p.is_dir() and not p.name.startswith('.'):
                dirs.append({"name": p.name, "path": str(p)})
        dirs.sort(key=lambda x: x["name"].lower())
        return jsonify({"current_path": str(target_dir), "dirs": dirs})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/git', methods=['POST'])
def git_action():
    data = request.json
    action = data.get('action')
    repo_name = data.get('repo')
    repo_path = os.path.join(PROJECTS_DIR, repo_name)
    
    try:
        if action == 'clone':
            os.makedirs(PROJECTS_DIR, exist_ok=True)
            if not os.path.exists(repo_path):
                username = requests.get("https://api.github.com/user", headers={"Authorization": f"token {get_token()}"}).json().get('login')
                Repo.clone_from(f"https://{get_token()}@github.com/{username}/{repo_name}.git", repo_path)
                return jsonify({"msg": f"ریپوی {repo_name} با موفقیت کلون شد."})
            return jsonify({"msg": "این ریپو از قبل وجود دارد."})
        elif action == 'pull':
            Repo(repo_path).remotes.origin.pull()
            return jsonify({"msg": "دریافت تغییرات (Pull) موفق بود."})
        elif action == 'push':
            repo = Repo(repo_path)
            repo.git.add(A=True)
            if repo.is_dirty(untracked_files=True): repo.index.commit("Auto commit via GitMaster")
            repo.remotes.origin.push()
            return jsonify({"msg": "ارسال تغییرات (Push) موفق بود."})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    print("\033[92m✅ سرور GitMaster اجرا شد. در حال باز کردن مرورگر...\033[0m")
    webbrowser.open("http://127.0.0.1:5000")
    app.run(port=5000, debug=False)
