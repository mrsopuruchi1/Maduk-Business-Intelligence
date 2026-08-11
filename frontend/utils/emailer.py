import os
import smtplib
from email.message import EmailMessage


def send_email(to_email, subject, body, attachment_path):
    """
    Send email with attachment.
    Safe SMTP handling with environment validation.
    """

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Validate environment variables
    if not smtp_server or not smtp_port or not smtp_email or not smtp_password:
        raise Exception("SMTP settings are missing from the application environment")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = to_email
    msg.set_content(body)

    # Attach file if exists
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            file_data = f.read()

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="pdf",
            filename="D2D_Report.pdf"
        )

    # Send email
    with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)


from utils.emailer import send_email

def email_report(email, report_path):

    subject = "Your D2D Intelligence Business Report"

    message = "Your automated business analysis report is attached."

    send_email(email, subject, message, report_path)