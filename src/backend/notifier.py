import os
import re
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

class Notifier:
    def __init__(self):
        smtp_url = os.getenv("SMTP_URL", "")
        # Expected format: smtp://user:pass@host:port
        # Defaulting if not found
        username = os.getenv("MAIL_USERNAME", "admin@edu-mitra.com")
        password = os.getenv("MAIL_PASSWORD", "")
        host = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        port = int(os.getenv("MAIL_PORT", 587))

        if smtp_url and "@" in smtp_url:
            try:
                parts = re.match(r"smtp://([^:]+):([^@]+)@([^:]+):(\d+)", smtp_url)
                if parts:
                    username, password, host, port = parts.groups()
                    port = int(port)
            except Exception as e:
                print(f"Error parsing SMTP URL: {e}")

        self.conf = ConnectionConfig(
            MAIL_USERNAME = username,
            MAIL_PASSWORD = password,
            MAIL_FROM = username,
            MAIL_PORT = port,
            MAIL_SERVER = host,
            MAIL_STARTTLS = True,
            MAIL_SSL_TLS = False,
            USE_CREDENTIALS = True,
            VALIDATE_CERTS = True
        )
        self.fastmail = FastMail(self.conf)

    async def send_at_risk_alert(self, teacher_email: str, student_name: str, risk_factor: str):
        html = f"""
        <p>Hi Teacher,</p>
        <p>This is an automated alert from <b>EduMitra</b>.</p>
        <p>Student <b>{student_name}</b> has been identified as <b>High-Risk</b>.</p>
        <p>Primary Risk Factor: {risk_factor}</p>
        <p>Please check the Admin Dashboard for more details.</p>
        <br>
        <p>EduMitra Performance Monitoring System</p>
        """
        message = MessageSchema(
            subject=f"URGENT: High-Risk Alert - {student_name}",
            recipients=[teacher_email],
            body=html,
            subtype=MessageType.html
        )
        try:
            await self.fastmail.send_message(message)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
