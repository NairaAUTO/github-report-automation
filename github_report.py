import requests
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

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
    params = {"since": since.isoformat() + "Z"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return len(response.json())


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


def send_email_report(report):
    assert EMAIL_ADDRESS, "EMAIL_ADDRESS missing"
    assert EMAIL_PASSWORD, "EMAIL_PASSWORD missing"
    assert EMAIL_TO, "EMAIL_TO missing"

    msg = MIMEText(report)
    msg["Subject"] = "Weekly GitHub Repository Report"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


if __name__ == "__main__":
    report = generate_report()
    send_email_report(report)
