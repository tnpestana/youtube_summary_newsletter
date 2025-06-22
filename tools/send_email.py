import markdown2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(
    markdown_text: str,
    recipient_email: str,
    sender_email: str,
    sender_password: str
):
    html = markdown2.markdown(markdown_text, extras=[
        "fenced-code-blocks", "tables", "strike", "cuddled-lists"
    ])

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📰 TLDR News Daily Summary"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg.attach(MIMEText(markdown_text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

    print(f"📬 Email sent to {recipient_email}")