"""AI Signal KR - Gmail 발송 + Google Sheets 구독자 읽기"""
import smtplib, os, sys, json, base64
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build

GMAIL_USER         = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
SPREADSHEET_ID     = os.getenv("SPREADSHEET_ID", "1YRsMkIAzpiOAKKdcz_6ooSu-w1Y694Vgq5teFfNqBC4")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS", "")  # JSON 문자열
SHEET_RANGE        = "A2:A1000"
SCOPES             = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_subscribers():
    if not GOOGLE_CREDENTIALS:
        print("GOOGLE_CREDENTIALS 환경변수 없음")
        return []
    creds_info = json.loads(GOOGLE_CREDENTIALS)
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE).execute()
    values = result.get("values", [])
    emails = [row[0].strip() for row in values if row and "@" in row[0]]
    print(f"구독자 {len(emails)}명 확인")
    return emails

def send_newsletter(date, html, subscribers):
    date_fmt = datetime.strptime(date, "%Y-%m-%d").strftime("%Y년 %m월 %d일")
    subject  = f"[AI Signal] {date_fmt} 오늘의 AI 인사이트"
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    success = 0
    for email in subscribers:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"AI Signal KR <{GMAIL_USER}>"
            msg["To"]      = email
            msg.attach(MIMEText(html, "html", "utf-8"))
            server.sendmail(GMAIL_USER, email, msg.as_string())
            print(f"  발송 완료: {email}")
            success += 1
        except Exception as e:
            print(f"  발송 실패: {email} — {e}")
    server.quit()
    print(f"발송 완료: {success}명")

def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    html_path = Path(f"drafts/{date}_newsletter.html")
    if not html_path.exists():
        print(f"초안 없음: {html_path}")
        return
    html = html_path.read_text(encoding="utf-8")
    subscribers = get_subscribers()
    if not subscribers:
        print("구독자 없음")
        return
    send_newsletter(date, html, subscribers)

if __name__ == "__main__":
    main()
