import requests
import os
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# Environment Variables
# =========================
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

# =========================
# GitHub Config
# =========================
OWNER = "torvalds"
REPO = "linux"
GITHUB_API = "https://api.github.com"

# =========================
# Snapshot Config
# =========================
SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# =========================
# GitHub API Helpers
# =========================
def get_repo_info():
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_commits_last_7_days():
    since = datetime.utcnow() - timedelta(days=7)
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/commits"
    params = {"since": since.isoformat() + "Z"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return len(response.json())

# =========================
# Snapshot Handling (PART A)
# =========================
def save_weekly_snapshot(repo_data, commits):
    snapshot = {
        "repo": repo_data["full_name"],
        "stars": repo_data["stargazers_count"],
        "forks": repo_data["forks_count"],
        "open_issues": repo_data["open_issues_count"],
        "commits_last_7_days": commits,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    }

    filename = datetime.utcnow().strftime("%Y-%m-%d") + ".json"
    filepath = os.path.join(SNAPSHOT_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(snapshot, f, indent=2)

    return snapshot


def load_previous_snapshot():
    files = sorted(os.listdir(SNAPSHOT_DIR))
    if len(files) < 2:
        return None

    previous_file = files[-2]
    with open(os.path.join(SNAPSHOT_DIR, previous_file), "r") as f:
        return json.load(f)

# =========================
# Diff Calculations (PART B)
# =========================
def calculate_diff(current, previous):
    if previous is None:
        return None

    diff = {}

    for key in ["stars", "forks", "open_issues", "commits_last_7_days"]:
        current_val = current[key]
        previous_val = previous[key]

        change = current_val - previous_val
        percent = 0 if previous_val == 0 else (change / previous_val) * 100

        if change > 0:
            arrow = "↑"
        elif change < 0:
            arrow = "↓"
        else:
            arrow = "→"

        diff[key] = {
            "change": change,
            "percent": round(percent, 2),
            "arrow": arrow
        }

    return diff

# =========================
# Text Report Generator
# =========================
def generate_text_report(snapshot, diff):
    lines = [
        "GitHub Weekly Report\n",
        f"Repository: {snapshot['repo']}",
        f"Stars: {snapshot['stars']}",
        f"Forks: {snapshot['forks']}",
        f"Open Issues: {snapshot['open_issues']}",
        f"Commits (Last 7 Days): {snapshot['commits_last_7_days']}",
    ]

    if diff:
        lines.append("\nWeek-over-Week Change:")
        labels = {
            "stars": "Stars",
            "forks": "Forks",
            "open_issues": "Open Issues",
            "commits_last_7_days": "Commits"
        }
        for key, label in labels.items():
            d = diff[key]
            lines.append(
                f"{label}: {d['arrow']} {d['change']} ({d['percent']}%)"
            )

    lines.append(f"\nGenerated: {snapshot['generated_at']}")
    return "\n".join(lines)

# =========================
# HTML Report Generator
# =========================
def generate_html_report(snapshot, diff):
    def diff_cell(key):
        if not diff:
            return "—"
        d = diff[key]
        return f"{d['arrow']} {d['change']} ({d['percent']}%)"

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{
    font-family: Arial, sans-serif;
    background-color: #f6f8fa;
    padding: 20px;
}}
.container {{
    max-width: 650px;
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
}}
th, td {{
    padding: 10px;
    border-bottom: 1px solid #e1e4e8;
}}
th {{
    background-color: #f6f8fa;
}}
.footer {{
    font-size: 12px;
    color: #6a737d;
    margin-top: 20px;
    text-align: center;
}}
</style>
</head>
<body>
<div class="container">
<h2>📊 Weekly GitHub Report</h2>

<table>
<tr>
<th>Metric</th>
<th>Value</th>
<th>WoW Change</th>
</tr>

<tr>
<td>⭐ Stars</td>
<td>{snapshot['stars']}</td>
<td>{diff_cell("stars")}</td>
</tr>

<tr>
<td>🍴 Forks</td>
<td>{snapshot['forks']}</td>
<td>{diff_cell("forks")}</td>
</tr>

<tr>
<td>🐞 Open Issues</td>
<td>{snapshot['open_issues']}</td>
<td>{diff_cell("open_issues")}</td>
</tr>

<tr>
<td>🧱 Commits (7 days)</td>
<td>{snapshot['commits_last_7_days']}</td>
<td>{diff_cell("commits_last_7_days")}</td>
</tr>
</table>

<div class="footer">
Generated on {snapshot['generated_at']}<br>
GitHub Report Automation
</div>
</div>
</body>
</html>
"""

# =========================
# Email Sender
# =========================
def send_email(text_report, html_report):
    assert EMAIL_ADDRESS, "EMAIL_ADDRESS missing"
    assert EMAIL_PASSWORD, "EMAIL_PASSWORD missing"
    assert EMAIL_TO, "EMAIL_TO missing"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Weekly GitHub Repository Report"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO

    msg.attach(MIMEText(text_report, "plain"))
    msg.attach(MIMEText(html_report, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    repo_data = get_repo_info()
    commits = get_commits_last_7_days()

    snapshot = save_weekly_snapshot(repo_data, commits)
    previous_snapshot = load_previous_snapshot()
    diff = calculate_diff(snapshot, previous_snapshot)

    text_report = generate_text_report(snapshot, diff)
    html_report = generate_html_report(snapshot, diff)

    send_email(text_report, html_report)
