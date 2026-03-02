import smtplib
from email.message import EmailMessage

from utils.credentials import get_mail_config


def send_email(to, subject, content):
    msg = EmailMessage()
    msg.set_content(content)

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = subject
    msg['From'] = 'ov3@sanger.ac.uk'
    msg['To'] = to

    # Send the message via our own SMTP server.
    s = smtplib.SMTP(get_mail_config())
    s.send_message(msg)
    s.quit()
