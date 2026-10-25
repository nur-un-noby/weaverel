import re
import uuid
import logging
import requests
from django.conf import settings
from django.contrib.auth.models import User
from .models import CustomerProfile

logger = logging.getLogger(__name__)

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_or_create_google_user(email, first_name='', last_name='', phone=''):
    """
    Finds or creates a Django User from a verified Google/Gmail address.
    Generates a unique username and links their CustomerProfile.
    """
    clean_email = email.strip().lower()
    user = User.objects.filter(email__iexact=clean_email).first()

    if not user:
        # Generate safe, clean username
        raw_prefix = clean_email.split('@')[0]
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', raw_prefix) or 'customer'
        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=clean_email,
            first_name=first_name or base_username.capitalize(),
            last_name=last_name,
        )
        user.set_unusable_password()
        user.save()

    # Ensure profile exists and update phone if provided
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    if phone and not profile.phone_number:
        profile.phone_number = phone
        profile.save(update_fields=['phone_number'])

    return user


def get_google_auth_url(redirect_uri, state):
    """
    Constructs Google OAuth 2.0 authorization URL.
    """
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'openid email profile',
        'redirect_uri': redirect_uri,
        'state': state,
        'prompt': 'select_account',
    }
    query_str = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
    return f"{GOOGLE_AUTH_ENDPOINT}?{query_str}"


def exchange_code_for_profile(code, redirect_uri):
    """
    Exchanges authorization code for Google user profile info.
    Returns: (dict profile, None) on success or (None, str error) on failure.
    """
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')

    if not client_id or not client_secret:
        return None, "Google OAuth Client ID and Secret are not configured in settings."

    try:
        # 1. Exchange code for tokens
        token_response = requests.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
            timeout=10
        )
        if token_response.status_code != 200:
            logger.error(f"Google Token Exchange failed: {token_response.text}")
            return None, f"Failed to exchange code: {token_response.text}"

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        # 2. Fetch User Profile
        userinfo_response = requests.get(
            GOOGLE_USERINFO_ENDPOINT,
            headers={'Authorization': f"Bearer {access_token}"},
            timeout=10
        )
        if userinfo_response.status_code != 200:
            logger.error(f"Google Userinfo fetch failed: {userinfo_response.text}")
            return None, f"Failed to fetch profile: {userinfo_response.text}"

        profile_data = userinfo_response.json()
        return profile_data, None

    except Exception as e:
        logger.error(f"Exception during Google OAuth exchange: {str(e)}")
        return None, str(e)
