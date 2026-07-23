import smtplib
from email.message import EmailMessage

def send_mail(to, subject, body):
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

    try:
        server.login("jyoshnavii.k@gmail.com", "yqkt qfyp xnvk serh")

        msg = EmailMessage()
        msg["From"] = "jyoshnavii.k@gmail.com"
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        server.send_message(msg)
        print("Mail sent successfully!")

    finally:
        server.quit()