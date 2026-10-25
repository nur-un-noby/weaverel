from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _

from .models import Wishlist, WishlistItem
from store.models import Product
from cart.services import get_or_create_cart, add_item_to_cart


def wishlist_view(request):
    """
    Displays the customer's wishlist items.
    Supports persistent database wishlist for logged-in users,
    and session wishlist for guests.
    """
    products = []
    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        products = [item.product for item in wishlist.items.select_related('product', 'product__category')]
    else:
        guest_ids = request.session.get('guest_wishlist', [])
        products = Product.objects.filter(id__in=guest_ids, is_available=True)

    context = {
        'products': products,
        'count': len(products),
    }
    return render(request, 'wishlist/wishlist.html', context)


@require_POST
def toggle_wishlist(request, product_id):
    """
    Adds or removes a product from the wishlist.
    Responds with HTMX partial button or JSON.
    """
    product = get_object_or_404(Product, id=product_id, is_available=True)
    is_in_wishlist = False

    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        existing = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
        if existing:
            existing.delete()
            is_in_wishlist = False
            msg = _(f"'{product.name}' removed from your wishlist.")
        else:
            WishlistItem.objects.create(wishlist=wishlist, product=product)
            is_in_wishlist = True
            msg = _(f"'{product.name}' added to your wishlist!")
        count = wishlist.items.count()
    else:
        guest_list = request.session.get('guest_wishlist', [])
        if product.id in guest_list:
            guest_list.remove(product.id)
            is_in_wishlist = False
            msg = _(f"'{product.name}' removed from your wishlist.")
        else:
            guest_list.append(product.id)
            is_in_wishlist = True
            msg = _(f"'{product.name}' added to your wishlist!")
        request.session['guest_wishlist'] = guest_list
        request.session.modified = True
        count = len(guest_list)

    if request.headers.get('HX-Request'):
        context = {
            'product': product,
            'is_in_wishlist': is_in_wishlist,
        }
        response = render(request, 'wishlist/partials/wishlist_button.html', context)
        response['HX-Trigger'] = f'{{"wishlistChanged": {{"count": {count}}}}}'
        return response

    messages.info(request, msg)
    return redirect(request.META.get('HTTP_REFERER') or 'wishlist:wishlist_view')


@require_POST
def move_to_cart(request, product_id):
    """
    Moves an item directly from wishlist to shopping cart.
    """
    product = get_object_or_404(Product, id=product_id, is_available=True)
    variant = product.variants.filter(is_active=True, stock__gt=0).first()
    if not variant:
        messages.warning(request, _("Sorry, this clothing item is currently out of stock."))
        return redirect('wishlist:wishlist_view')

    cart = get_or_create_cart(request)
    success, msg, _ = add_item_to_cart(cart, variant.id, 1)

    if success:
        # Remove from wishlist
        if request.user.is_authenticated:
            WishlistItem.objects.filter(wishlist__user=request.user, product=product).delete()
        else:
            guest_list = request.session.get('guest_wishlist', [])
            if product.id in guest_list:
                guest_list.remove(product.id)
                request.session['guest_wishlist'] = guest_list
                request.session.modified = True
        messages.success(request, f"'{product.name}' কার্টে যুক্ত করা হয়েছে (Moved to your shopping cart)!")
    else:
        messages.warning(request, msg)

    return redirect('cart:cart_detail')
