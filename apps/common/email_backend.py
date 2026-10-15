import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    """Django email backend that sends via Resend API."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        resend.api_key = settings.RESEND_API_KEY

    def send_messages(self, email_messages):
        sent = 0
        for msg in email_messages:
            try:
                html = None
                if msg.alternatives:
                    for alt_content, alt_type in msg.alternatives:
                        if alt_type == 'text/html':
                            html = alt_content
                            break
                params = {
                    'from': msg.from_email or settings.DEFAULT_FROM_EMAIL,
                    'to': msg.to,
                    'subject': msg.subject,
                }
                if html:
                    params['html'] = html
                else:
                    params['text'] = msg.body
                if msg.cc:
                    params['cc'] = msg.cc
                if msg.bcc:
                    params['bcc'] = msg.bcc
                if msg.reply_to:
                    params['reply_to'] = msg.reply_to
                resend.Emails.send(params)
                sent += 1
            except Exception as e:
                if not self.fail_silently:
                    raise e
        return sent
