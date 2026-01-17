import requests
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")


OWNER = "torvalds"
REPO = "linux"
GITHUB_API = "https://api.github.com"
def get_repo_info():
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_commits_last_7_days():
    since = datetime.utcnow() - timedelta(days=7)
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/commits"

    params = {
        "since": since.isoformat() + "Z"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return len(response.json())

def generate_report():
    repo = get_repo_info()
    commits = get_commits_last_7_days()

    full_name = repo["full_name"]
    stars = repo["stargazers_count"]
    forks = repo["forks_count"]
    issues = repo["open_issues_count"]
    generated_time = datetime.now()

def send_email_report(report):
    msg = MIMEText(report)
    msg["Subject"] = "Weekly GitHub Repository Report"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


    report = f"""
GitHub Weekly Report
Repository: {full_name}
Stars: {stars}
Forks: {forks}
Open Issues: {issues}
Commits (Last 7 Days): {commits}
Generated: {generated_time}
"""
    return report

if __name__ == "__main__":
    report = generate_report()
send_email_report(report)

