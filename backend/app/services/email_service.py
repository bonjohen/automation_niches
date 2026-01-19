"""Email service for sending notifications."""
from abc import ABC, abstractmethod
from typing import Optional

from jinja2 import Template

from app.config.settings import get_settings

settings = get_settings()


class EmailMessage:
    """Represents an email message."""

    def __init__(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ):
        self.to_email = to_email
        self.subject = subject
        self.html_body = html_body
        self.text_body = text_body or self._strip_html(html_body)
        self.from_email = from_email or settings.email_from_address
        self.from_name = from_name or settings.email_from_name
        self.reply_to = reply_to

    def _strip_html(self, html: str) -> str:
        """Strip HTML tags for plain text version."""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    def send(self, message: EmailMessage) -> dict:
        """Send an email message. Returns dict with send status and external_id."""
        pass


class ConsoleEmailProvider(EmailProvider):
    """Console email provider for development - prints emails to stdout."""

    def send(self, message: EmailMessage) -> dict:
        print("\n" + "=" * 60)
        print("📧 EMAIL (Console Provider)")
        print("=" * 60)
        print(f"From: {message.from_name} <{message.from_email}>")
        print(f"To: {message.to_email}")
        print(f"Subject: {message.subject}")
        print("-" * 60)
        print(message.text_body[:500])
        if len(message.text_body) > 500:
            print("... [truncated]")
        print("=" * 60 + "\n")

        return {
            "success": True,
            "external_id": f"console-{id(message)}",
            "message": "Email printed to console",
        }


class SendGridEmailProvider(EmailProvider):
    """SendGrid email provider."""

    def __init__(self):
        if not settings.sendgrid_api_key:
            raise ValueError("SENDGRID_API_KEY is required for SendGrid provider")

        try:
            from sendgrid import SendGridAPIClient
            self.client = SendGridAPIClient(settings.sendgrid_api_key)
        except ImportError:
            raise RuntimeError("sendgrid package is required for SendGrid provider")

    def send(self, message: EmailMessage) -> dict:
        from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent

        sg_message = Mail(
            from_email=Email(message.from_email, message.from_name),
            to_emails=To(message.to_email),
            subject=message.subject,
        )
        sg_message.add_content(Content("text/plain", message.text_body))
        sg_message.add_content(HtmlContent(message.html_body))

        if message.reply_to:
            sg_message.reply_to = Email(message.reply_to)

        try:
            response = self.client.send(sg_message)
            return {
                "success": response.status_code in (200, 201, 202),
                "external_id": response.headers.get("X-Message-Id", ""),
                "status_code": response.status_code,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


class MailgunEmailProvider(EmailProvider):
    """Mailgun email provider."""

    def __init__(self):
        if not settings.mailgun_api_key or not settings.mailgun_domain:
            raise ValueError("MAILGUN_API_KEY and MAILGUN_DOMAIN are required")

        self.api_key = settings.mailgun_api_key
        self.domain = settings.mailgun_domain

    def send(self, message: EmailMessage) -> dict:
        import requests

        response = requests.post(
            f"https://api.mailgun.net/v3/{self.domain}/messages",
            auth=("api", self.api_key),
            data={
                "from": f"{message.from_name} <{message.from_email}>",
                "to": message.to_email,
                "subject": message.subject,
                "text": message.text_body,
                "html": message.html_body,
            },
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "external_id": data.get("id", ""),
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code,
            }


class EmailService:
    """Email service that uses configured provider."""

    def __init__(self):
        self.provider = self._get_provider()

    def _get_provider(self) -> EmailProvider:
        """Get the configured email provider."""
        provider_name = settings.email_provider.lower()

        if provider_name == "sendgrid":
            return SendGridEmailProvider()
        elif provider_name == "mailgun":
            return MailgunEmailProvider()
        else:
            # Default to console for development
            return ConsoleEmailProvider()

    def send(self, message: EmailMessage) -> dict:
        """Send an email message."""
        return self.provider.send(message)

    def send_template(
        self,
        to_email: str,
        subject_template: str,
        body_template: str,
        context: dict,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> dict:
        """
        Send an email using Jinja2 templates.

        Args:
            to_email: Recipient email address
            subject_template: Jinja2 template for subject line
            body_template: Jinja2 template for HTML body
            context: Template context variables
            from_email: Optional sender email
            from_name: Optional sender name
        """
        # Render templates
        subject = Template(subject_template).render(**context)
        html_body = Template(body_template).render(**context)

        message = EmailMessage(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            from_email=from_email,
            from_name=from_name,
        )

        return self.send(message)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
