from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from decimal import Decimal, InvalidOperation

from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from .models import User, PlayerProfile
from .forms import ProfileForm, EmailForm, UsernameForm, OnboardingForm, PhoneForm
from .tables import UserHTMxTable
from .filters import UserFilter

User = get_user_model()


class UsersHtmxTableView(SingleTableMixin, FilterView):
    model = User
    table_class = UserHTMxTable
    filterset_class = UserFilter
    template_name = "cric/pages/user_table_htmx.html"

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["cric/partials/user_table_partial.html"]
        return [self.template_name]

    def get_queryset(self):
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request'] = self.request
        return context


@login_required
def profile_view(request, username=None):
    if not username:
        username = request.user.username
    user = get_object_or_404(User, username=username)

    edit_mode = request.GET.get('edit', False)
    if edit_mode:
        form = ProfileForm(instance=user)
        if request.method == 'POST':
            form = ProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('profile')
        context = {'user': user, 'form': form, 'edit_mode': True, 'is_profile_page': True}
    else:
        context = {'user': user, 'is_profile_page': True}

    return render(request, 'cric/pages/profile.html', context)


@login_required
def profile_edit_view(request):
    return redirect(f"{reverse('profile')}?edit=True")


@login_required
def profile_settings_view(request):
    return render(request, 'cric/pages/profile_settings.html', {'is_profile_page': True})


@login_required
def profile_emailchange(request):
    if request.htmx:
        if request.method == 'GET':
            form = EmailForm(instance=request.user)
            return render(request, 'partials/email_form.html', {'form': form})
        if request.method == 'POST':
            form = EmailForm(request.POST, instance=request.user)
            if form.is_valid():
                email = form.cleaned_data['email']
                if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                    messages.warning(request, f'{email} is already in use.')
                    return redirect('profile-settings')
                form.save()
                messages.success(request, 'Email updated successfully.')
                return redirect('profile-settings')
            return render(request, 'partials/email_form.html', {'form': form})

    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.warning(request, f'{email} is already in use.')
                return redirect('profile-settings')
            form.save()
            messages.success(request, 'Email updated successfully.')
        else:
            messages.warning(request, 'Email not valid or already in use')
    return redirect('profile-settings')


@login_required
def profile_usernamechange(request):
    if request.htmx:
        if request.method == 'GET':
            form = UsernameForm(instance=request.user)
            return render(request, 'partials/username_form.html', {'form': form})
        if request.method == 'POST':
            form = UsernameForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Username updated successfully.')
                return redirect('profile-settings')
            return render(request, 'partials/username_form.html', {'form': form})

    if request.method == 'POST':
        form = UsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Username updated successfully.')
        else:
            messages.warning(request, 'Username not valid or already in use')
    return redirect('profile-settings')


@login_required
def profile_emailverify(request):
    from allauth.account.utils import send_email_confirmation
    send_email_confirmation(request, request.user)
    return redirect('profile-settings')


@login_required
def profile_phonechange(request):
    if request.htmx:
        if request.method == 'GET':
            form = PhoneForm(instance=request.user)
            return render(request, 'partials/phone_form.html', {'form': form})
        if request.method == 'POST':
            form = PhoneForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'WhatsApp number updated.')
                return redirect('profile-settings')
            return render(request, 'partials/phone_form.html', {'form': form})

    if request.method == 'POST':
        form = PhoneForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'WhatsApp number updated.')
        else:
            messages.warning(request, 'Invalid phone number.')
    return redirect('profile-settings')


@login_required
def profile_delete_view(request):
    user = request.user
    if request.method == "POST":
        logout(request)
        user.delete()
        messages.success(request, 'Account deleted, what a pity')
        return redirect('home')
    return render(request, 'cric/pages/profile_delete.html')


@login_required
def profile_onboarding_view(request):
    if request.user.phone:
        return redirect('profile')
    if request.method == 'POST':
        form = OnboardingForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = OnboardingForm(instance=request.user)
    return render(request, 'cric/pages/profile_onboarding.html', {'form': form})


@login_required
def manage_users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'True'
        wallet_amount = request.POST.get('wallet_amount')
        try:
            wallet_amount = Decimal(wallet_amount) if wallet_amount else Decimal('0.00')
        except (ValueError, InvalidOperation):
            wallet_amount = Decimal('0.00')

        try:
            user = User.objects.get(pk=user_id)
            user.username = name
            user.email = email
            user.role = role
            user.is_active = is_active
            user.save()
            wallet = user.wallet_set.first()
            if wallet:
                wallet.amount = wallet_amount
                wallet.save()
            else:
                user.wallet_set.create(amount=wallet_amount)
            messages.success(request, "User updated successfully!")
        except User.DoesNotExist:
            messages.error(request, "User not found.")

    users = User.objects.all().order_by('first_name', 'username')
    return render(request, 'cric/pages/manage_users.html', {'users': users})


@login_required
def delete_user_view(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=user_id)
            if user == request.user:
                messages.error(request, "You cannot delete your own account.")
            elif user.is_superuser:
                messages.error(request, "Cannot delete admin accounts.")
            else:
                username = user.get_full_name() or user.username
                user.delete()
                messages.success(request, f"User '{username}' deleted successfully.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return redirect('manage-users')


@login_required
def edit_user_view(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        wallet = user.wallet_set.first()
        wallet_amount = wallet.amount if wallet else 0.00

        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            is_staff = request.POST.get('is_staff') == 'True'
            is_superuser = request.POST.get('is_superuser') == 'True'
            wallet_amount = request.POST.get('wallet_amount')
            batting_rating = request.POST.get('batting_rating')
            bowling_rating = request.POST.get('bowling_rating')
            fielding_rating = request.POST.get('fielding_rating')

            try:
                wallet_amount = Decimal(wallet_amount) if wallet_amount else Decimal('0.00')
                batting_rating = min(max(Decimal(batting_rating if batting_rating else '2.5'), Decimal('0')), Decimal('5'))
                bowling_rating = min(max(Decimal(bowling_rating if bowling_rating else '2.5'), Decimal('0')), Decimal('5'))
                fielding_rating = min(max(Decimal(fielding_rating if fielding_rating else '2.5'), Decimal('0')), Decimal('5'))
            except (ValueError, TypeError, InvalidOperation):
                wallet_amount = Decimal('0.00')
                batting_rating = Decimal('2.5')
                bowling_rating = Decimal('2.5')
                fielding_rating = Decimal('2.5')

            user.username = username
            user.email = email
            user.role = role
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.batting_rating = batting_rating
            user.bowling_rating = bowling_rating
            user.fielding_rating = fielding_rating
            user.save()

            wallet = user.wallet_set.first()
            if wallet:
                wallet.amount = wallet_amount
                wallet.save()
            else:
                user.wallet_set.create(amount=wallet_amount)

            messages.success(request, 'User updated successfully!')
            return redirect('manage-users')

        if request.headers.get('HX-Request'):
            return render(request, 'cric/partials/edit_user_form_partial.html', {
                'user': user,
                'wallet_amount': wallet_amount,
            })
        return render(request, 'cric/pages/edit_user_form.html', {
            'user': user,
            'wallet_amount': wallet_amount,
            'modal_view': True,
        })

    except User.DoesNotExist:
        if request.headers.get('HX-Request'):
            return render(request, 'cric/partials/edit_user_form_partial.html', {
                'message': 'User not found.',
                'success': False,
            })
        return render(request, 'cric/pages/edit_user_form.html', {
            'message': 'User not found.',
            'success': False,
        })


@login_required
def create_user_view(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('manage-users')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'batsman')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        wallet_amount = request.POST.get('wallet_amount', '0.00')

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'cric/pages/create_user_form.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"User '{username}' already exists.")
            return render(request, 'cric/pages/create_user_form.html', {
                'username': username, 'email': email, 'role': role,
                'is_staff': is_staff, 'is_superuser': is_superuser,
                'wallet_amount': wallet_amount,
            })

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.role = role
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()

            try:
                amount = Decimal(wallet_amount)
                user.wallet_set.create(amount=amount)
            except (ValueError, InvalidOperation):
                user.wallet_set.create(amount=Decimal('0.00'))

            messages.success(request, f"User '{username}' created successfully!")
            return redirect('manage-users')
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return render(request, 'cric/pages/create_user_form.html', {
                'username': username, 'email': email, 'role': role,
                'is_staff': is_staff, 'is_superuser': is_superuser,
                'wallet_amount': wallet_amount,
            })

    return render(request, 'cric/pages/create_user_form.html')
