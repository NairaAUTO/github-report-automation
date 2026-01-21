import requests
import os
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
# Report Generators
# =========================
def generate_report():
    repo = get_repo_info()
    commits = get_commits_last_7_days()

    return f"""
GitHub Weekly Report

Repository: {repo['full_name']}
Stars: {repo['stargazers_count']}
Forks: {repo['forks_count']}
Open Issues: {repo['open_issues_count']}
Commits (Last 7 Days): {commits}
Generated: {datetime.utcnow()}
"""


def generate_html_report(repo_data):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

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
            max-width: 600px;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }}
        h1 {{
            color: #24292e;
            font-size: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 10px;
            border-bottom: 1px solid #e1e4e8;
            text-align: left;
        }}
        th {{
            background-color: #f6f8fa;
        }}
        .footer {{
            margin-top: 20px;
            font-size: 12px;
            color: #6a737d;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Weekly GitHub Report</h1>
        <p><strong>Repository:</strong> {repo_data['full_name']}</p>

        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>⭐ Stars</td><td>{repo_data['stargazers_count']}</td></tr>
            <tr><td>🍴 Forks</td><td>{repo_data['forks_count']}</td></tr>
            <tr><td>🐞 Open Issues</td><td>{repo_data['open_issues_count']}</td></tr>
            <tr><td>🧱 Commits (Last 7 Days)</td><td>{get_commits_last_7_days()}</td></tr>
        </table>

        <div class="footer">
            Generated automatically on {timestamp}<br>
            GitHub Weekly Reports Automation
        </div>
    </div>
</body>
</html>
"""


# =========================
# Email Sender (Multipart)
# =========================
def send_email_report(report):
    assert EMAIL_ADDRESS, "EMAIL_ADDRESS missing"
    assert EMAIL_PASSWORD, "EMAIL_PASSWORD missing"
    assert EMAIL_TO, "EMAIL_TO missing"

    repo_data = get_repo_info()
    text_report = report
    html_report = generate_html_report(repo_data)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Weekly GitHub Repository Report"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO

    msg.attach(MIMEText(text_report, "plain"))
    msg.attach(MIMEText(html_report, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    report = generate_report()
    send_email_report(report)
