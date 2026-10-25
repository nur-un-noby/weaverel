from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import CustomerProfile, Address, validate_bangladesh_phone


class CustomerLoginForm(AuthenticationForm):
    """
    Standard customer login form supporting username or email address.
    """
    username = forms.CharField(
        label=_("ইউজারনেম অথবা ইমেইল (Username or Email)"),
        widget=forms.TextInput(attrs={
            'placeholder': _("ইউজারনেম বা ইমেইল অ্যাড্রেস লিখুন"),
            'class': 'w-full p-3 rounded-xl border border-stone-300 focus:ring-1 focus:ring-stone-900 focus:outline-none text-xs',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_("পাসওয়ার্ড (Password)"),
        widget=forms.PasswordInput(attrs={
            'placeholder': _("আপনার পাসওয়ার্ড লিখুন"),
            'class': 'w-full p-3 rounded-xl border border-stone-300 focus:ring-1 focus:ring-stone-900 focus:outline-none text-xs',
        })
    )


class CustomerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, label=_("First Name"))
    last_name = forms.CharField(max_length=50, required=True, label=_("Last Name"))
    email = forms.EmailField(required=True, label=_("Email Address"))
    phone_number = forms.CharField(max_length=20, required=True, label=_("Mobile Number (017XXXXXXXX)"))
    password = forms.CharField(widget=forms.PasswordInput, required=True, label=_("Password"), min_length=8)
    password_confirm = forms.CharField(widget=forms.PasswordInput, required=True, label=_("Confirm Password"))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(_("This username is already taken. Please choose another."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email already exists."))
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        valid, clean_phone = validate_bangladesh_phone(phone)
        if not valid:
            raise ValidationError(_("Please enter a valid Bangladesh mobile number (e.g. 01712345678)."))
        return clean_phone

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        pw_confirm = cleaned_data.get('password_confirm')
        if pw and pw_confirm and pw != pw_confirm:
            raise ValidationError(_("Passwords do not match."))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            profile = user.profile
            profile.phone_number = self.cleaned_data['phone_number']
            profile.save()
        return user


class CustomerProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomerProfile
        fields = ('phone_number', 'alternative_phone', 'district', 'address')

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            valid, clean_phone = validate_bangladesh_phone(phone)
            if not valid:
                raise ValidationError(_("Please enter a valid Bangladesh mobile number."))
            return clean_phone
        return phone


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('title', 'recipient_name', 'phone_number', 'district', 'address_line', 'is_default')

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        valid, clean_phone = validate_bangladesh_phone(phone)
        if not valid:
            raise ValidationError(_("Please enter a valid Bangladesh mobile number."))
        return clean_phone
