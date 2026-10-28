from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
import re


BENGALI_TO_ASCII_DIGITS = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')


def validate_bangladesh_phone(phone):
    """
    Validates Bangladesh standard mobile phone numbers.
    Accepts 013, 014, 015, 016, 017, 018, 019 formats (11 digits, or with +880 / 880 / Bengali digits).
    Cleans punctuation, invisible unicode markers, whitespace, and country prefixes.
    Returns (is_valid: bool, clean_phone: str).
    """
    if not phone:
        return False, ''

    # 1. Convert Bengali numerals to ASCII numerals
    converted = str(phone).translate(BENGALI_TO_ASCII_DIGITS)

    # 2. Extract digits only
    digits = re.sub(r'\D', '', converted)

    # 3. Strip international BD prefix (+88 / 88 / 880)
    if digits.startswith('880'):
        digits = digits[2:]  # leaves 01...
    elif digits.startswith('88') and len(digits) > 11:
        digits = digits[2:]

    # 4. Handle 10-digit number missing leading 0 (e.g. 1712345678)
    if not digits.startswith('0') and len(digits) == 10 and digits.startswith(('13', '14', '15', '16', '17', '18', '19')):
        digits = '0' + digits

    # 5. Standard Bangladesh mobile pattern: exactly 11 digits starting with 01[3-9]
    pattern = r'^01[3-9]\d{8}$'
    is_valid = bool(re.match(pattern, digits))
    return is_valid, digits if is_valid else str(phone).strip()


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=25, blank=True, db_index=True, help_text=_("Bangladesh mobile number (e.g. 017XXXXXXXX)"))
    alternative_phone = models.CharField(max_length=25, blank=True)
    district = models.CharField(max_length=100, default='Dhaka', blank=True)
    address = models.TextField(blank=True, help_text=_("Default delivery address"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.phone_number or 'No Phone'})"


class Address(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='saved_addresses')
    title = models.CharField(max_length=50, default=_("Home"), help_text=_("e.g. Home, Office"))
    recipient_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=25)
    district = models.CharField(max_length=100, default="Dhaka")
    address_line = models.TextField(help_text=_("House, Road, Area details"))
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = _("Customer Address")
        verbose_name_plural = _("Customer Addresses")

    def __str__(self):
        return f"{self.title}: {self.recipient_name}, {self.district}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set other addresses for this customer to is_default=False
            Address.objects.filter(customer=self.customer).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    CustomerProfile.objects.get_or_create(user=instance)
