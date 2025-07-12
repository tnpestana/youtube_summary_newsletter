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
    try:
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

        print(f"📬 Email sent successfully to {recipient_email}")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print("💡 Tip: Make sure you're using a Gmail App Password, not your regular password")
        raise
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error occurred: {e}")
        raise
    except Exception as e:
        print(f"❌ Failed to send email: {type(e).__name__}: {e}")
        raise