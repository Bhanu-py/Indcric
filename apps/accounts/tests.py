import io
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from PIL import Image

from .forms import OnboardingForm, ProfileForm, AVATAR_MAX_BYTES

User = get_user_model()


def _png_upload(name='pic.png', size=(8, 8)):
    """Build a tiny in-memory PNG SimpleUploadedFile for upload tests."""
    buf = io.BytesIO()
    Image.new('RGB', size, (22, 101, 52)).save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/png')


class AvatarUrlTests(TestCase):
    def test_falls_back_to_ui_avatars_when_empty(self):
        u = User.objects.create_user(username='rohit', password='x')
        url = u.avatar_url
        self.assertIn('ui-avatars.com', url)
        self.assertIn('name=rohit', url)
        self.assertIn('background=166534', url)

    def test_returns_file_url_when_set(self):
        u = User.objects.create_user(username='virat', password='x')
        u.avatar.save('a.png', _png_upload(), save=True)
        self.assertEqual(u.avatar_url, u.avatar.url)
        self.assertNotIn('ui-avatars.com', u.avatar_url)


class ProfileFormAvatarValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='sachin', password='x')
        self.base = {
            'first_name': 'Sachin', 'last_name': 'T', 'role': 'batsman',
            'batting_rating': '4.5', 'bowling_rating': '2.0', 'fielding_rating': '3.0',
        }

    def test_accepts_valid_image(self):
        form = ProfileForm(
            self.base, {'avatar': _png_upload()}, instance=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_non_image(self):
        bad = SimpleUploadedFile('notes.txt', b'hello world', content_type='text/plain')
        form = ProfileForm(self.base, {'avatar': bad}, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)

    def test_rejects_oversize_file(self):
        big = SimpleUploadedFile(
            'big.png', b'\x00' * (AVATAR_MAX_BYTES + 1), content_type='image/png'
        )
        form = ProfileForm(self.base, {'avatar': big}, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)


class RatingFormLockTests(TestCase):
    def test_profile_form_ignores_posted_rating_fields(self):
        user = User.objects.create_user(
            username='jadeja', password='x',
            batting_rating=Decimal('1.5'),
            bowling_rating=Decimal('2.0'),
            fielding_rating=Decimal('3.0'),
        )
        form = ProfileForm({
            'first_name': 'Ravindra',
            'last_name': 'Jadeja',
            'role': 'allrounder',
            'batting_rating': '5.0',
            'bowling_rating': '5.0',
            'fielding_rating': '5.0',
        }, instance=user)

        self.assertNotIn('batting_rating', form.fields)
        self.assertNotIn('bowling_rating', form.fields)
        self.assertNotIn('fielding_rating', form.fields)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        user.refresh_from_db()
        self.assertEqual(user.batting_rating, Decimal('1.5'))
        self.assertEqual(user.bowling_rating, Decimal('2.0'))
        self.assertEqual(user.fielding_rating, Decimal('3.0'))

    def test_onboarding_form_ignores_posted_rating_fields(self):
        user = User.objects.create_user(
            username='newbie', password='x',
            batting_rating=Decimal('1.5'),
            bowling_rating=Decimal('2.0'),
            fielding_rating=Decimal('3.0'),
        )
        form = OnboardingForm({
            'full_name': 'New Member',
            'role': 'batsman',
            'batting_rating': '5.0',
            'bowling_rating': '5.0',
            'fielding_rating': '5.0',
        }, instance=user)

        self.assertNotIn('batting_rating', form.fields)
        self.assertNotIn('bowling_rating', form.fields)
        self.assertNotIn('fielding_rating', form.fields)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        user.refresh_from_db()
        self.assertEqual(user.batting_rating, Decimal('1.5'))
        self.assertEqual(user.bowling_rating, Decimal('2.0'))
        self.assertEqual(user.fielding_rating, Decimal('3.0'))


class AvatarChangeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='dhoni', password='x')
        self.client.force_login(self.user)

    def test_upload_sets_avatar(self):
        resp = self.client.post(
            reverse('profile-avatarchange'),
            {'avatar': _png_upload()},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)

    def test_remove_flow_clears_field(self):
        self.user.avatar.save('a.png', _png_upload(), save=True)
        self.assertTrue(self.user.avatar)
        resp = self.client.post(
            reverse('profile-avatarchange'),
            {'remove': '1'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)


class StaffUserManagementViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staff_user', password='x', is_staff=True)
        self.member = User.objects.create_user(username='member_user', password='x')
        self.client.force_login(self.staff)

    def test_edit_user_full_page_renders(self):
        resp = self.client.get(reverse('edit-user', args=[self.member.id]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Edit User')
        self.assertContains(resp, reverse('edit-user', args=[self.member.id]))

    def test_edit_user_htmx_partial_renders(self):
        resp = self.client.get(
            reverse('edit-user', args=[self.member.id]),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Edit Player')
        self.assertContains(resp, reverse('edit-user', args=[self.member.id]))
