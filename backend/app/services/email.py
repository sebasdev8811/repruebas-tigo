import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import asyncio

async def send_reset_password_email(email: str, token: str):
    msg = MIMEMultipart()
    msg['From'] = settings.MAIL_FROM
    msg['To'] = email
    msg['Subject'] = "Restablecer contraseña - Sistema Tigo"

    reset_link = f"http://localhost:5500/reset-password.html?token={token}"
    
    body = f"""
    <h2>Restablecer contraseña</h2>
    <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>
    <a href="{reset_link}">{reset_link}</a>
    <p>Este enlace expira en 1 hora.</p>
    <p>Si no solicitaste este cambio, ignora este correo.</p>
    """
    
    msg.attach(MIMEText(body, 'html'))

    def _send():
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_FROM, email, msg.as_string())

    await asyncio.get_event_loop().run_in_executor(None, _send)
