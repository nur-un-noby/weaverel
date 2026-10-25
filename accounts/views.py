import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .forms import CustomerLoginForm, CustomerRegistrationForm, CustomerProfileForm, AddressForm
from .models import Address, CustomerProfile
from orders.models import Order
from cart.services import merge_guest_cart_into_user_cart
from .google_auth import (
    get_or_create_google_user,
    get_google_auth_url,
    exchange_code_for_profile,
)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            guest_session_key = request.session.session_key
            user = form.save()
            login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
            merge_guest_cart_into_user_cart(request, user, guest_session_key=guest_session_key)
            messages.success(request, f"স্বাগতম, {user.first_name}! আপনার অ্যাকাউন্ট তৈরি সম্পন্ন হয়েছে।")
            next_url = request.GET.get('next') or request.POST.get('next') or 'accounts:dashboard'
            return redirect(next_url)
    else:
        form = CustomerRegistrationForm()

    has_google_auth = bool(
        getattr(settings, 'GOOGLE_CLIENT_ID', '').strip() and
        getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()
    )

    return render(request, 'accounts/register.html', {
        'form': form,
        'has_google_auth': has_google_auth,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            guest_session_key = request.session.session_key
            user = form.get_user()
            login(request, user)
            merge_guest_cart_into_user_cart(request, user, guest_session_key=guest_session_key)
            messages.success(request, f"স্বাগতম, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next') or 'accounts:dashboard'
            return redirect(next_url)
        else:
            messages.error(request, _("ইউজারনেম/ইমেইল অথবা পাসওয়ার্ড সঠিক নয়। দয়া করে আবার চেষ্টা করুন।"))
    else:
        form = CustomerLoginForm()

    has_google_auth = bool(
        getattr(settings, 'GOOGLE_CLIENT_ID', '').strip() and
        getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()
    )

    return render(request, 'accounts/login.html', {
        'form': form,
        'has_google_auth': has_google_auth,
    })


def logout_view(request):
    logout(request)
    messages.info(request, _("You have been signed out successfully."))
    return redirect('store:home')


@login_required
def dashboard_view(request):
    user = request.user
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    recent_orders = Order.objects.filter(user=user).prefetch_related('items')[:5]
    addresses = profile.saved_addresses.all()[:3]
    total_orders_count = Order.objects.filter(user=user).count()

    context = {
        'recent_orders': recent_orders,
        'addresses': addresses,
        'total_orders_count': total_orders_count,
        'profile': profile,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_edit_view(request):
    user = request.user
    profile, _ = CustomerProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            form.save()
            messages.success(request, _("Your profile has been updated successfully."))
            return redirect('accounts:dashboard')
    else:
        form = CustomerProfileForm(instance=profile, initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        })

    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def address_list_view(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    addresses = profile.saved_addresses.all()
    return render(request, 'accounts/address_list.html', {'addresses': addresses})


@login_required
def address_add_view(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.customer = profile
            address.save()
            messages.success(request, _("New delivery address added."))
            return redirect('accounts:address_list')
    else:
        form = AddressForm()

    return render(request, 'accounts/address_form.html', {'form': form, 'action': 'Add'})


@login_required
def address_edit_view(request, address_id):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    address = get_object_or_404(Address, id=address_id, customer=profile)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, _("Address updated successfully."))
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {'form': form, 'action': 'Edit', 'address': address})


@login_required
def address_delete_view(request, address_id):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    address = get_object_or_404(Address, id=address_id, customer=profile)
    if request.method == 'POST':
        address.delete()
        messages.info(request, _("Address deleted."))
        return redirect('accounts:address_list')
    return render(request, 'accounts/address_confirm_delete.html', {'address': address})


@login_required
def order_history_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    return render(request, 'accounts/order_history.html', {'orders': orders})


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order, 'items': order.items.all()})


@login_required
def order_cancel_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method == 'POST':
        if order.status == Order.STATUS_PENDING:
            order.update_status(Order.STATUS_CANCELLED, user=request.user, notes="Cancelled by customer")
            # Restore variant stock
            for item in order.items.all():
                if item.variant:
                    item.variant.stock += item.quantity
                    item.variant.save(update_fields=['stock', 'updated_at'])
            messages.success(request, f"অর্ডার #{order.order_number} সফলভাবে বাতিল করা হয়েছে।")
        else:
            messages.error(request, "এই অর্ডারটি বর্তমানে বাতিল করা সম্ভব নয় কারণ এটি প্রক্রিয়াকরণে চলে গেছে।")
        return redirect('accounts:order_detail', order_number=order.order_number)

    return render(request, 'accounts/order_cancel_confirm.html', {'order': order})


def google_login_view(request):
    """
    Initiates Google OAuth 2.0 flow.
    Remembers previous destination (e.g. checkout) and guest cart session.
    """
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('cart:checkout')
    request.session['google_next'] = next_url
    if request.session.session_key:
        request.session['guest_cart_session_key'] = request.session.session_key

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()

    # If live Google OAuth credentials are provided, redirect to Google OAuth
    if client_id and client_secret:
        state = uuid.uuid4().hex
        request.session['google_oauth_state'] = state
        redirect_uri = request.build_absolute_uri(reverse('accounts:google_callback'))
        auth_url = get_google_auth_url(redirect_uri, state)
        return redirect(auth_url)

    # If Google OAuth credentials are not configured in settings:
    messages.warning(
        request,
        _("Google Sign-In is not configured yet. Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in settings, or sign in with your username/email and password.")
    )
    return redirect(f"{reverse('accounts:login')}?next={next_url}")


def google_callback_view(request):
    """
    Google OAuth 2.0 callback endpoint.
    Verifies code, fetches user profile, authenticates user, merges cart,
    and forwards straight to checkout/destination.
    """
    code = request.GET.get('code')
    state = request.GET.get('state')
    expected_state = request.session.get('google_oauth_state')

    if not code or (expected_state and state != expected_state):
        messages.error(request, _("Google authentication failed or was cancelled. Please try again."))
        return redirect('accounts:login')

    redirect_uri = request.build_absolute_uri(reverse('accounts:google_callback'))
    profile, error = exchange_code_for_profile(code, redirect_uri)

    if not profile:
        messages.error(request, f"Google login error: {error}")
        return redirect('accounts:login')

    email = profile.get('email')
    given_name = profile.get('given_name') or profile.get('name', '').split(' ')[0]
    family_name = profile.get('family_name', '')

    guest_session_key = request.session.get('guest_cart_session_key') or request.session.session_key

    user = get_or_create_google_user(
        email=email,
        first_name=given_name,
        last_name=family_name
    )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    merge_guest_cart_into_user_cart(request, user, guest_session_key=guest_session_key)

    messages.success(request, f"স্বাগতম {user.first_name or user.username}! Google একাউন্টে সফলভাবে লগইন হয়েছে।")
    next_url = request.session.get('google_next') or reverse('cart:checkout')
    return redirect(next_url)


def google_auto_login_view(request):
    """
    Development endpoint for automated testing with POST data in DEBUG mode.
    Does NOT allow automatic fake sign-in or unauthenticated bypass.
    """
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('cart:checkout')
    guest_session_key = request.session.session_key

    if request.method != 'POST':
        messages.warning(request, _("Direct sign-in via GET is disabled. Please sign in with your username/email and password."))
        return redirect(f"{reverse('accounts:login')}?next={next_url}")

    raw_email = request.POST.get('email', '').strip()
    full_name = request.POST.get('full_name', '').strip()

    if not raw_email:
        messages.error(request, _("Please provide a valid email address."))
        return redirect(f"{reverse('accounts:login')}?next={next_url}")

    if '@' not in raw_email:
        raw_email = f"{raw_email}@gmail.com"

    first_name = full_name.split(' ')[0] if full_name else raw_email.split('@')[0].capitalize()
    last_name = ' '.join(full_name.split(' ')[1:]) if (full_name and len(full_name.split(' ')) > 1) else ''

    user = get_or_create_google_user(
        email=raw_email,
        first_name=first_name,
        last_name=last_name
    )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    merge_guest_cart_into_user_cart(request, user, guest_session_key=guest_session_key)

    messages.success(request, f"স্বাগতম {user.first_name or user.username}!")
    return redirect(next_url)

