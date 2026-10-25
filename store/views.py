from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, Product
from orders.models import Order


def home(request):
    """
    Main storefront view with visual categories, search filtering, and sorting.
    """
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    products = Product.objects.filter(is_available=True)

    # 1. Category Filter
    selected_category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if selected_category_slug:
        selected_category = get_object_or_404(Category, slug=selected_category_slug)
        products = products.filter(category=selected_category)

    # 2. Search Filter
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # 3. Sorting
    sort = request.GET.get('sort', '').strip()
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    else:
        # Default: newest first, featured prioritized
        products = products.order_by('-is_featured', '-created_at')

    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'query': query,
        'sort': sort,
        'total_count': products.count(),
    }
    return render(request, 'store/home.html', context)


def product_detail(request, slug):
    """
    Detailed product view showing images, size picker, fabric details,
    1-click WhatsApp order, and related clothing items.
    """
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(
        category=product.category, 
        is_available=True
    ).exclude(id=product.id)[:5]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)


def track_order(request):
    """
    Live customer order tracking by Mobile Number or Order ID.
    Provides visual delivery progress across 5 stages.
    """
    query = request.GET.get('q', '').strip()
    order = None
    searched = False
    status_step = 1

    if query:
        searched = True
        clean_query = query.replace('#', '').strip()
        order = Order.objects.filter(
            Q(order_number__iexact=clean_query) | 
            Q(order_number__iexact=f"WV-{clean_query}") |
            Q(phone_number__icontains=clean_query)
        ).first()

        if order:
            status_map = {
                'PENDING': 1,
                'CONFIRMED': 2,
                'PROCESSING': 3,
                'SHIPPED': 4,
                'DELIVERED': 5,
                'CANCELLED': 0,
            }
            status_step = status_map.get(order.status, 1)

    context = {
        'order': order,
        'query': query,
        'searched': searched,
        'status_step': status_step,
    }
    return render(request, 'store/track_order.html', context)
