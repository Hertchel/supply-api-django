import os
import resend
from django.core.mail import send_mail
from dotenv import load_dotenv

load_dotenv()

# Get API key from environment
api_key = os.environ.get('RESEND_API_KEY')
sender_domain_name = os.environ.get('DOMAIN_NAME')

# Only set resend API key if it exists
if api_key:
    resend.api_key = api_key


def send_mail_resend(receiver, subject, html):
    """
    Sends email using Resend in production.
    In development it just prints the email.
    """

    if os.getenv("DJANGO_ENV") == "production":
        # Check if API key is configured
        if not api_key:
            print(f"\n⚠️  EMAIL DISABLED - No RESEND_API_KEY configured")
            print(f"TO: {receiver}")
            print(f"SUBJECT: {subject}")
            print(f"CONTENT PREVIEW: {html[:200]}...")
            print("================================\n")
            return {"message": "Email disabled - No API key configured"}
        
        # Check if domain is configured
        if not sender_domain_name:
            print("===============================================\n")
            print("===============================================\n")
            print("===============================================\n")
            print(f"\n⚠️  EMAIL DISABLED - No DOMAIN_NAME configured")
            print(f"TO: {receiver}")
            print(f"SUBJECT: {subject}")
            print("===============================================\n")
            print("===============================================\n")
            print("===============================================\n")
            return {"message": "Email disabled - No domain configured"}
        
        try:
            params = {
                "from": f"supply-office@{sender_domain_name}",
                "to": [receiver],
                "subject": subject,
                "html": html
            }
            response = resend.Emails.send(params)
            print(f"✅ Email sent successfully to {receiver}")
            return response
        except Exception as e:
            print(f"❌ Error sending email to {receiver}: {e}")
            return {"error": str(e)}

    else:
        print("\n===== DEV EMAIL (NOT SENT) =====")
        print("TO:", receiver)
        print("SUBJECT:", subject)
        print("CONTENT:", html[:200] + "..." if len(html) > 200 else html)
        print("================================\n")
        return {"message": "Email printed in console (development mode)"}


def send_mail_django(message, subject, email):
    """Send email using Django's built-in email system"""
    try:
        send_mail(subject, message, 'settings.EMAIL_HOST_USER', [email], fail_silently=False)
        print(f"✅ Django email sent to {email}")
        return {"message": "Email sent successfully"}
    except Exception as e:
        print(f"❌ Error sending Django email to {email}: {e}")
        return {"error": str(e)}


def send_file(file, email, html):
    """Send file attachment via email"""

    if os.getenv("DJANGO_ENV") != "production":
        print("\n===== DEV FILE EMAIL =====")
        print("TO:", email)
        print("FILE:", file.name)
        print("==========================\n")
        return {"message": "File email skipped in development"}

    # Check if API key is configured
    if not api_key:
        print(f"\n⚠️  FILE EMAIL DISABLED - No RESEND_API_KEY configured")
        print(f"TO: {email}")
        print(f"FILE: {file.name}")
        print("================================\n")
        return {"message": "File email disabled - No API key configured"}

    if not sender_domain_name:
        print(f"\n⚠️  FILE EMAIL DISABLED - No DOMAIN_NAME configured")
        print(f"TO: {email}")
        print(f"FILE: {file.name}")
        print("================================\n")
        return {"message": "File email disabled - No domain configured"}

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

        response = resend.Emails.send(params)
        print(f"✅ File email sent successfully to {email} with attachment: {file.name}")
        return {"message": "Email sent successfully."}

    except Exception as e:
        print(f"❌ Error sending file email to {email}: {e}")
        return {"error": str(e)}

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)