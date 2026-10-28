from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import CustomerProfile, Address, validate_bangladesh_phone


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_bangladesh_phone_validator(self):
        valid, clean = validate_bangladesh_phone("01712345678")
        self.assertTrue(valid)
        self.assertEqual(clean, "01712345678")

        valid_with_code, clean2 = validate_bangladesh_phone("+8801812345678")
        self.assertTrue(valid_with_code)
        self.assertEqual(clean2, "01812345678")

        # Test Bengali numerals
        valid_bn, clean_bn = validate_bangladesh_phone("০১৭১২৩৪৫৬৭৮")
        self.assertTrue(valid_bn)
        self.assertEqual(clean_bn, "01712345678")

        # Test formatted number with spaces and dashes
        valid_fmt, clean_fmt = validate_bangladesh_phone("+88 01912-345 678")
        self.assertTrue(valid_fmt)
        self.assertEqual(clean_fmt, "01912345678")

        # Test 10 digits without leading 0
        valid_10, clean_10 = validate_bangladesh_phone("1712345678")
        self.assertTrue(valid_10)
        self.assertEqual(clean_10, "01712345678")

        invalid, _ = validate_bangladesh_phone("12345")
        self.assertFalse(invalid)

        invalid_op, _ = validate_bangladesh_phone("01234567890")
        self.assertFalse(invalid_op)

    def test_user_registration_and_profile_signal(self):
        url = reverse('accounts:register')
        payload = {
            'first_name': 'Nabila',
            'last_name': 'Islam',
            'username': 'nabila_i',
            'email': 'nabila@example.com',
            'phone_number': '01912345678',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)

        user = User.objects.filter(username='nabila_i').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.profile.phone_number, '01912345678')

    def test_address_management_default_flag(self):
        user = User.objects.create_user(username='addresstester', password='password123')
        profile = user.profile

        addr1 = Address.objects.create(
            customer=profile,
            title="Home",
            recipient_name="Tester",
            phone_number="01700000000",
            address_line="Road 1, Dhanmondi",
            is_default=True
        )

        addr2 = Address.objects.create(
            customer=profile,
            title="Office",
            recipient_name="Tester",
            phone_number="01700000000",
            address_line="Gulshan 2",
            is_default=True
        )

        # addr1 should now have is_default=False because addr2 is default
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)

    def test_google_auto_login_and_user_creation(self):
        url = reverse('accounts:google_auto_login')
        response = self.client.post(url, {
            'email': 'tahmid.hassan@gmail.com',
            'full_name': 'Tahmid Hassan',
            'next': reverse('cart:checkout')
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:checkout'))

        user = User.objects.filter(email='tahmid.hassan@gmail.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Tahmid')
        self.assertEqual(user.last_name, 'Hassan')
        self.assertFalse(user.has_usable_password())
        self.assertIsNotNone(user.profile)

    def test_google_login_redirect_unconfigured(self):
        """When Google OAuth is unconfigured, user is redirected to login page with warning."""
        with self.settings(GOOGLE_CLIENT_ID='', GOOGLE_CLIENT_SECRET=''):
            url = reverse('accounts:google_login')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('accounts:login'), response.url)

    def test_google_login_redirect_configured(self):
        """When Google OAuth is configured, user is redirected to Google OAuth endpoint."""
        with self.settings(GOOGLE_CLIENT_ID='test_client_id', GOOGLE_CLIENT_SECRET='test_secret'):
            url = reverse('accounts:google_login')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('accounts.google.com', response.url)

    def test_login_with_email_and_password(self):
        """Users can authenticate using either username or email with password."""
        user = User.objects.create_user(username='customer_arif', email='arif@example.com', password='Secr3tPassword!')
        login_url = reverse('accounts:login')

        # Test login using email
        response = self.client.post(login_url, {
            'username': 'arif@example.com',
            'password': 'Secr3tPassword!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_login_with_phone_number_and_password(self):
        """Users can authenticate using their registered mobile number and password."""
        user = User.objects.create_user(username='phone_customer', email='phone@example.com', password='PhonePass123!')
        user.profile.phone_number = '01712345678'
        user.profile.save()

        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {
            'username': '01712345678',
            'password': 'PhonePass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
