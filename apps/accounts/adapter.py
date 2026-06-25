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
    """
    
    def send_mail(self, template_prefix, email, context):
        """
        Send email with proper error handling and logging.
        Called by django-allauth for confirmation emails.
        """
        try:
            logger.info(f"[SIGNUP_EMAIL] Attempting to send {template_prefix} email to {email}")
            
            # Call parent to send email
            result = super().send_mail(template_prefix, email, context)
            
            logger.info(f"[SIGNUP_EMAIL] Successfully sent {template_prefix} email to {email}")
            return result
            
        except Exception as e:
            logger.error(f"[SIGNUP_EMAIL] Failed to send {template_prefix} email to {email}: {str(e)}", exc_info=True)
            # Re-raise so allauth knows there was an error
            raise
    
    def save_user(self, request, sociallogin=None, form=None):
        """
        Override to add logging when user is created.
        """
        user = super().save_user(request, sociallogin, form)
        logger.info(f"[SIGNUP] New user created: {user.username} ({user.email})")
        return user
