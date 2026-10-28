from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import validate_bangladesh_phone

UserModel = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that allows users to authenticate using either
    their username, their registered email address, or their verified phone number.
    Lookup is case-insensitive for both fields.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if not username or not password:
            return None

        clean_identifier = str(username).strip()
        is_phone, clean_phone = validate_bangladesh_phone(clean_identifier)

        try:
            lookup = Q(username__iexact=clean_identifier) | Q(email__iexact=clean_identifier)
            if is_phone:
                lookup |= Q(profile__phone_number=clean_phone)
            user = UserModel.objects.filter(lookup).first()
        except Exception:
            return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
