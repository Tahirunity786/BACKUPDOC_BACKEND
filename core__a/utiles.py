from django.core.mail import EmailMessage
from django.conf import settings

def send_password_reset_email(data):
    email = EmailMessage(
        subject=data['subject'],
        body=data['html_content'],
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[data['email']],
    )
    email.content_subtype = 'html'  # This is important to render HTML properly
    email.send()
