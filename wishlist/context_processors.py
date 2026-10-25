def wishlist_context(request):
    """
    Context processor to make wishlist counter badge available across all templates.
    Supports both authenticated users and guest sessions.
    """
    count = 0
    if request.user.is_authenticated:
        try:
            from wishlist.models import Wishlist
            wishlist = Wishlist.objects.filter(user=request.user).first()
            if wishlist:
                count = wishlist.items.count()
        except Exception:
            count = 0
    else:
        guest_wishlist = request.session.get('guest_wishlist', [])
        count = len(guest_wishlist)

    return {
        'wishlist_count': count,
    }
