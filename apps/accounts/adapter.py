"""
Custom allauth adapter to handle email sending with error handling and logging.
"""
from allauth.account.adapter import DefaultAccountAdapter
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter that adds logging and error handling for email sending.
    Ensures emails are properly sent via Brevo API in production.
    """
    
    def send_mail(self, template_prefix, email, context):
        """
        Send email with proper error handling and logging.
        Called by django-allauth for confirmation emails.
        
        Important: With anymail+Brevo, send_mail() returns 1 if sent to API,
        but that doesn't guarantee delivery. Monitor Brevo dashboard for bounces.
        """
        try:
            logger.info(f"[SIGNUP_EMAIL] Attempting to send {template_prefix} email to {email}")
            logger.info(f"[SIGNUP_EMAIL] Email backend: {settings.EMAIL_BACKEND}")
            logger.debug(f"[SIGNUP_EMAIL] Template: {template_prefix}, Context keys: {list(context.keys())}")
            
            # Get the rendered email subject and body
            subject_line = self.get_subject_line(template_prefix, context)
            body_text = self.get_message_body(template_prefix, context)
            html_body = self.get_message_html(template_prefix, context)
            
            logger.debug(f"[SIGNUP_EMAIL] Subject: {subject_line}")
            logger.debug(f"[SIGNUP_EMAIL] Has HTML: {bool(html_body)}")
            
            # Call parent to send email via django-allauth's mechanism
            result = super().send_mail(template_prefix, email, context)
            
            logger.info(f"[SIGNUP_EMAIL] Successfully sent {template_prefix} email to {email} (result={result})")
            return result
            
        except Exception as e:
            logger.error(f"[SIGNUP_EMAIL] FAILED to send {template_prefix} email to {email}")
            logger.error(f"[SIGNUP_EMAIL] Error: {type(e).__name__}: {str(e)}", exc_info=True)
            # Re-raise so allauth knows there was an error
            raise
    
    def save_user(self, request, sociallogin=None, form=None):
        """
        Override to add logging when user is created.
        """
        user = super().save_user(request, sociallogin, form)
        logger.info(f"[SIGNUP] New user created: {user.username} ({user.email})")
        return user
