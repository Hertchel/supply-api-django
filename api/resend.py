import os
import resend
from django.core.mail import send_mail
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.environ.get('RESEND_API_KEY')
sender_domain_name = os.environ.get('DOMAIN_NAME')


def send_mail_resend(receiver, subject, html):
    """
    Sends email using Resend in production.
    In development it just prints the email.
    """

    if os.getenv("DJANGO_ENV") == "production":
        params = {
            "from": f"supply-office@{sender_domain_name}",
            "to": [receiver],
            "subject": subject,
            "html": html
        }
        return resend.Emails.send(params)

    else:
        print("\n===== DEV EMAIL (NOT SENT) =====")
        print("TO:", receiver)
        print("SUBJECT:", subject)
        print("CONTENT:", html)
        print("================================\n")
        return {"message": "Email printed in console (development mode)"}


def send_mail_django(message, subject, email):
    send_mail(subject, message, 'settings.EMAIL_HOST_USER', [email], fail_silently=False)


def send_file(file, email, html):

    if os.getenv("DJANGO_ENV") != "production":
        print("\n===== DEV FILE EMAIL =====")
        print("TO:", email)
        print("FILE:", file.name)
        print("==========================\n")
        return {"message": "File email skipped in development"}

    temp_file_path = os.path.join("temp", file.name)
    os.makedirs("temp", exist_ok=True)

    try:
        with open(temp_file_path, "wb") as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)

        with open(temp_file_path, "rb") as f:
            file_content = f.read()

        attachment = {
            "content": list(file_content),
            "filename": file.name,
        }

        params = {
            "from": f'supply-office@{sender_domain_name}',
            "to": [email],
            "subject": "Your File Attachment",
            "html": html,
            "attachments": [attachment],
        }

        resend.Emails.send(params)

        return {"message": "Email sent successfully."}

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)