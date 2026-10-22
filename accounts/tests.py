from io import BytesIO

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import ProfileForm, RegisterForm
from .models import MasterProfile


class RegisterFormTests(TestCase):
    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username='existing', email='user@example.com', password='test-pass-123'
        )
        form = RegisterForm(data={
            'username': 'new-user',
            'email': 'USER@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'strong-test-pass-123',
            'password2': 'strong-test-pass-123',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_registration_creates_inactive_user(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'pending-user',
            'email': 'pending@example.com',
            'first_name': 'Pending',
            'last_name': 'User',
            'password1': 'strong-test-pass-123',
            'password2': 'strong-test-pass-123',
        })

        self.assertRedirects(response, reverse('accounts:login'))
        self.assertFalse(User.objects.get(username='pending-user').is_active)


class AuthenticationViewTests(TestCase):
    def test_inactive_user_cannot_log_in(self):
        User.objects.create_user(
            username='inactive', password='test-pass-123', is_active=False
        )

        response = self.client.post(reverse('accounts:login'), {
            'username': 'inactive',
            'password': 'test-pass-123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_rejects_get_and_accepts_post(self):
        user = User.objects.create_user(username='master', password='test-pass-123')
        self.client.force_login(user)

        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        response = self.client.post(reverse('accounts:logout'))

        self.assertRedirects(response, reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_redirects_to_safe_next_url(self):
        User.objects.create_user(username='master', password='test-pass-123')

        response = self.client.post(
            reverse('accounts:login') + '?next=' + reverse('accounts:profile'),
            {'username': 'master', 'password': 'test-pass-123'},
        )

        self.assertRedirects(response, reverse('accounts:profile'))

    def test_login_ignores_external_next_url(self):
        User.objects.create_user(username='master', password='test-pass-123')

        response = self.client.post(
            reverse('accounts:login') + '?next=https://evil.example.com/',
            {'username': 'master', 'password': 'test-pass-123'},
        )

        self.assertRedirects(response, reverse('appointments:index'))

class ProfileFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='master', email='master@example.com', password='test-pass-123'
        )

    def test_user_can_keep_own_email(self):
        form = ProfileForm(data={
            'first_name': 'Master',
            'last_name': 'User',
            'email': 'MASTER@example.com',
        }, instance=self.user)

        self.assertTrue(form.is_valid(), form.errors)

    def test_another_users_email_is_rejected(self):
        User.objects.create_user(
            username='other', email='other@example.com', password='test-pass-123'
        )
        form = ProfileForm(data={
            'first_name': 'Master',
            'last_name': 'User',
            'email': 'OTHER@example.com',
        }, instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

def make_image_upload(name='photo.png', padding_bytes=0):
    image_buffer = BytesIO()
    Image.new('RGB', (10, 10), color='red').save(image_buffer, format='PNG')
    content = image_buffer.getvalue() + (b'\0' * padding_bytes)
    return SimpleUploadedFile(name, content, content_type='image/png')


@override_settings(STORAGES={
    'default': {
        'BACKEND': 'django.core.files.storage.memory.InMemoryStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
})
class ProfilePhotoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='photo-master',
            email='photo@example.com',
            password='test-pass-123',
        )
        self.client.force_login(self.user)
        self.profile_data = {
            'first_name': 'Photo',
            'last_name': 'Master',
            'email': 'photo@example.com',
        }

    def test_disallowed_photo_extension_is_rejected(self):
        form = ProfileForm(
            data=self.profile_data,
            files={'photo': make_image_upload('photo.bmp')},
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('photo', form.errors)

    def test_photo_larger_than_five_megabytes_is_rejected(self):
        form = ProfileForm(
            data=self.profile_data,
            files={'photo': make_image_upload(
                'photo.png', padding_bytes=5 * 1024 * 1024
            )},
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('photo', form.errors)

    def test_replacing_photo_deletes_old_file(self):
        first_response = self.client.post(
            reverse('accounts:profile'),
            {**self.profile_data, 'photo': make_image_upload('first.png')},
        )
        self.assertRedirects(first_response, reverse('accounts:profile'))

        profile = MasterProfile.objects.get(user=self.user)
        old_photo_name = profile.photo.name
        storage = profile.photo.storage
        self.assertTrue(storage.exists(old_photo_name))

        second_response = self.client.post(
            reverse('accounts:profile'),
            {**self.profile_data, 'photo': make_image_upload('second.png')},
        )
        self.assertRedirects(second_response, reverse('accounts:profile'))

        profile.refresh_from_db()
        self.assertFalse(storage.exists(old_photo_name))
        self.assertTrue(storage.exists(profile.photo.name))

    def test_deleting_profile_deletes_photo_file(self):
        profile = self.user.masterprofile
        profile.photo = make_image_upload('delete-me.png')
        profile.save()
        photo_name = profile.photo.name
        storage = profile.photo.storage
        self.assertTrue(storage.exists(photo_name))

        profile.delete()

        self.assertFalse(storage.exists(photo_name))
