import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models import Setting

def send_email(recipient, subject, body):
    """
    Sends an email using the SMTP settings configured in the application.
    
    Args:
        recipient (str): The email address of the recipient.
        subject (str): The subject of the email.
        body (str): The HTML body of the email.
        
    Returns:
        tuple: A tuple containing a boolean success status and a message.
    """
    # Retrieve SMTP settings from the database
    settings_list = Setting.query.all()
    settings = {s.key: s.value for s in settings_list}

    smtp_server = settings.get('smtp_server')
    smtp_port = settings.get('smtp_port')
    smtp_username = settings.get('smtp_username')
    smtp_password = settings.get('smtp_password')
    smtp_sender_email = settings.get('smtp_sender_email')
    smtp_use_tls = settings.get('smtp_use_tls') == 'true'

    if not all([smtp_server, smtp_port, smtp_username, smtp_password, smtp_sender_email]):
        return False, "SMTP settings are not fully configured."

    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = smtp_sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            if smtp_use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        return True, "Email sent successfully."

    except Exception as e:
        return False, f"Failed to send email: {e}"
