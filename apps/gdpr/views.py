from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import UserConsent
from .forms import ConsentForm
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
@require_http_methods(["POST"])
def consent_accept_view(request):
    """
    Accept GDPR consent terms.
    Called via AJAX from consent modal or signup flow.
    
    Note: HTML checkboxes that are unchecked don't appear in POST data.
    We need to explicitly check for their presence.
    """
    logger.info(f"[CONSENT] Received POST data: {dict(request.POST)}")
    logger.info(f"[CONSENT] User: {request.user.username}")
    
    # Get checkbox values - unchecked boxes won't be in POST
    privacy_policy_accepted = 'privacy_policy_accepted' in request.POST
    terms_accepted = 'terms_accepted' in request.POST
    whatsapp_accepted = 'whatsapp_accepted' in request.POST
    
    logger.info(f"[CONSENT] Checkbox values: privacy={privacy_policy_accepted}, terms={terms_accepted}, whatsapp={whatsapp_accepted}")
    
    # Validate that required fields are checked
    if not privacy_policy_accepted or not terms_accepted:
        error_msg = 'You must accept Privacy Policy and Terms of Service'
        logger.warning(f"[CONSENT] Validation failed: {error_msg}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_msg
            }, status=400)
        else:
            messages.error(request, error_msg)
            return redirect('gdpr:consent_form')
    
    # Create or update UserConsent record
    user_consent, created = UserConsent.objects.get_or_create(
        user=request.user
    )
    
    # Update consent fields
    user_consent.privacy_policy_accepted = privacy_policy_accepted
    user_consent.terms_accepted = terms_accepted
    user_consent.whatsapp_accepted = whatsapp_accepted
    user_consent.ip_address = get_client_ip(request)
    # Update the accepted_at timestamp to current time when re-accepting
    user_consent.accepted_at = timezone.now()
    user_consent.save()
    
    # Clear the session flag since consent has been accepted
    if 'show_consent_modal' in request.session:
        del request.session['show_consent_modal']
        logger.info(f"[CONSENT] Cleared session flag for {request.user.username}")
    
    logger.info(f"[CONSENT] Successfully saved consent for {request.user.username}")
    logger.info(f"[CONSENT] Database values: privacy={user_consent.privacy_policy_accepted}, terms={user_consent.terms_accepted}, whatsapp={user_consent.whatsapp_accepted}, all_accepted={user_consent.all_consents_accepted}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Consent accepted'})
    else:
        messages.success(request, 'Thank you for accepting our terms!')
        return redirect(request.POST.get('next', 'home'))


@login_required
@require_http_methods(["GET", "POST"])
def delete_account_view(request):
    """
    Delete account - step 1: Show confirmation form.
    User must confirm they want to delete and will receive email link.
    """
    if request.method == 'POST':
        if request.POST.get('confirm_delete') == 'on':
            # Generate deletion token and send email
            uid = urlsafe_base64_encode(force_bytes(request.user.pk))
            token = default_token_generator.make_token(request.user)
            
            # Build confirmation link
            confirmation_url = request.build_absolute_uri(
                f'/gdpr/account/delete/confirm/{uid}/{token}/'
            )
            
            # Send confirmation email
            subject = 'Confirm Account Deletion'
            html_message = render_to_string('gdpr/deletion_email.html', {
                'user': request.user,
                'confirmation_url': confirmation_url,
            })
            
            try:
                send_mail(
                    subject,
                    'Please confirm account deletion by clicking the link in the HTML version of this email.',
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    html_message=html_message,
                )
                logger.info(f"[DELETE_ACCOUNT] Confirmation email sent to {request.user.email}")
                
                messages.success(
                    request,
                    'Confirmation email sent. Please check your inbox to complete deletion.'
                )
            except Exception as e:
                logger.error(f"[DELETE_ACCOUNT] Failed to send confirmation email to {request.user.email}: {str(e)}")
                messages.error(
                    request,
                    'Failed to send confirmation email. Please try again later.'
                )
                return render(request, 'gdpr/delete_account.html')
            
            return redirect('home')
        else:
            messages.error(request, 'You must confirm account deletion.')
    
    return render(request, 'gdpr/delete_account.html')


@require_http_methods(["GET", "POST"])
def delete_account_confirm_view(request, uidb64, token):
    """
    Delete account - step 2: Confirm via email link.
    User clicks link from email, account is permanently deleted.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        # Use the User model directly, don't rely on request.user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid deletion link.')
        return redirect('home')
    
    if not default_token_generator.check_token(user, token):
        messages.error(request, 'Invalid or expired deletion link.')
        return redirect('home')
    
    if request.method == 'POST':
        if request.POST.get('confirm_final_delete') == 'on':
            # Permanently delete user account
            user.delete()
            messages.success(request, 'Your account has been permanently deleted.')
            logout(request)
            return redirect('home')
        else:
            messages.error(request, 'You must confirm final deletion.')
    
    return render(request, 'gdpr/delete_account_confirm.html', {'user': user})


def privacy_policy_view(request):
    """Display privacy policy"""
    return render(request, 'gdpr/privacy_policy.html')


def terms_of_service_view(request):
    """Display terms of service"""
    return render(request, 'gdpr/terms_of_service.html')
