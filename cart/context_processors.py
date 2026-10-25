"""
Context processor for Weaverel shopping cart in BDT (৳).
Makes cart total and counter badge accessible across all templates.
"""

def cart_context(request):
    cart = request.session.get('cart', {})
    total_items = sum(item.get('quantity', 0) for item in cart.values())
    subtotal = sum(float(item.get('price', 0)) * item.get('quantity', 0) for item in cart.values())
    
    return {
        'cart_total_items': total_items,
        'cart_subtotal': round(subtotal, 2),
        'cart_subtotal_bdt': f"৳ {int(subtotal):,}",
    }
