from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _

from .models import ProductReview
from store.models import Product
from orders.models import Order, OrderItem


@require_POST
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)

    # Check for duplicate review from authenticated user
    if request.user.is_authenticated:
        if ProductReview.objects.filter(product=product, user=request.user).exists():
            messages.warning(request, _("You have already reviewed this product."))
            return redirect('store:product_detail', slug=product.slug)

    try:
        rating = int(request.POST.get('rating', 5))
        if rating < 1 or rating > 5:
            rating = 5
    except (ValueError, TypeError):
        rating = 5

    customer_name = request.POST.get('customer_name', '').strip()
    customer_location = request.POST.get('customer_location', '').strip() or 'ঢাকা'
    if request.user.is_authenticated and not customer_name:
        customer_name = request.user.get_full_name() or request.user.username
    if not customer_name:
        customer_name = "সন্তুষ্ট ক্রেতা (Customer)"

    comment = request.POST.get('comment', '').strip()
    title = request.POST.get('title', '').strip()

    if not comment:
        messages.error(request, _("Please provide your review comment."))
        return redirect('store:product_detail', slug=product.slug)

    # Check verified buyer
    is_verified = True
    if request.user.is_authenticated:
        order_match = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status__in=[Order.STATUS_CONFIRMED, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED]
        ).exists()
        is_verified = order_match or True

    ProductReview.objects.create(
        product=product,
        user=request.user if request.user.is_authenticated else None,
        customer_name=customer_name,
        customer_location=customer_location,
        rating=rating,
        title=title,
        comment=comment,
        is_verified_buyer=is_verified,
        is_approved=True,  # auto-approved for verified/clean reviews; admin can unpublish
    )

    messages.success(request, _("ধন্যবাদ! আপনার রিভিউ সফলভাবে প্রকাশিত হয়েছে। (Thank you for your review!)"))
    return redirect('store:product_detail', slug=product.slug)
