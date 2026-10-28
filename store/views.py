from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Min, Max
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import Category, Product, ProductVariant, Size, Color
from orders.models import Order
from reviews.models import ProductReview
from store_settings.models import HeroBanner, SiteConfiguration


def home(request):
    """
    Storefront homepage featuring:
    - Dynamic hero banners from database
    - Visual categories
    - Featured products & New arrivals
    - Trust indicators
    - Real-time shopping bag counter
    """
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    banners = HeroBanner.objects.filter(is_active=True).order_by('display_order')
    
    products = Product.objects.filter(is_available=True).select_related('category').prefetch_related('variants')
    
    # Check for explicit reset flag
    is_reset = request.GET.get('reset', '').strip() == '1'

    # Category Filter
    selected_category_slug = '' if is_reset else request.GET.get('category', '').strip()
    selected_category = None
    if selected_category_slug:
        selected_category = Category.objects.filter(slug=selected_category_slug, is_active=True).first()
        if selected_category:
            products = products.filter(category=selected_category)

    # Search Filter (bilingual search in English and Bangla)
    query = '' if is_reset else request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(name_bn__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query) |
            Q(description_bn__icontains=query) |
            Q(category__name__icontains=query) |
            Q(category__name_bn__icontains=query) |
            Q(fabric_details__icontains=query) |
            Q(fabric_details_bn__icontains=query)
        ).distinct()

    # Size filter
    size_filter = '' if is_reset else request.GET.get('size', '').strip()
    if size_filter:
        products = products.filter(variants__size__name=size_filter).distinct()

    # Color filter
    color_filter = '' if is_reset else request.GET.get('color', '').strip()
    if color_filter:
        products = products.filter(variants__color__name=color_filter).distinct()

    # In-stock only filter
    in_stock_only = '' if is_reset else request.GET.get('in_stock', '').strip()
    if in_stock_only == '1':
        products = products.filter(variants__stock__gt=0).distinct()

    # Price range filter
    min_price = None if is_reset else request.GET.get('min_price')
    max_price = None if is_reset else request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Sorting
    sort = '' if is_reset else request.GET.get('sort', '').strip()
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    else:
        # Default: priority by display_order (admin managed), then featured, then newest
        products = products.order_by('display_order', '-is_featured', '-created_at')

    has_active_filters = bool(selected_category or query or size_filter or color_filter or in_stock_only or min_price or max_price)

    # Exactly 12 products per page
    total_count = products.count()
    per_page = 12

    paginator = Paginator(products, per_page)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    all_sizes = Size.objects.all().order_by('display_order')
    all_colors = Color.objects.all().order_by('name')
    featured_products = Product.objects.filter(is_available=True, is_featured=True).order_by('display_order', '-created_at')[:6]
    new_arrivals = Product.objects.filter(is_available=True, is_new_arrival=True).order_by('display_order', '-created_at')[:6]

    # Live approved customer reviews from database for the 3-at-a-time carousel
    featured_reviews = ProductReview.objects.filter(is_approved=True).select_related('product').order_by('-created_at')[:12]
    total_reviews_count = ProductReview.objects.filter(is_approved=True).count()

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'banners': banners,
        'all_sizes': all_sizes,
        'all_colors': all_colors,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'featured_reviews': featured_reviews,
        'total_reviews_count': total_reviews_count,
        'query': query,
        'sort': sort,
        'size_filter': size_filter,
        'color_filter': color_filter,
        'in_stock_only': in_stock_only,
        'min_price': min_price,
        'max_price': max_price,
        'total_count': total_count,
        'has_active_filters': has_active_filters,
    }

    # HTMX Partial Rendering for smooth filter updates without full page reload
    if request.headers.get('HX-Request') and not request.headers.get('HX-Target') == 'cart-drawer':
        return render(request, 'store/partials/product_grid.html', context)

    return render(request, 'store/home.html', context)


def product_detail(request, slug):
    """
    Detailed product showcase with:
    - Multiple image gallery & thumbnail switcher
    - Real-time variant picker (size & color) with stock check
    - Fabric & specifications
    - Size guide modal
    - Verified customer reviews
    - Related clothing recommendations
    """
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'variants__size', 'variants__color'),
        slug=slug, 
        is_available=True
    )

    variants = product.variants.filter(is_active=True).select_related('size', 'color')
    sizes = list(dict.fromkeys([v.size for v in variants if v.size]))
    colors = list(dict.fromkeys([v.color for v in variants if v.color]))

    # Default variant
    first_variant = variants.filter(stock__gt=0).first() or variants.first()

    # Approved customer reviews
    reviews = product.reviews.filter(is_approved=True)
    avg_rating = 5.0
    if reviews.exists():
        avg_rating = round(sum(r.rating for r in reviews) / reviews.count(), 1)

    related_products = Product.objects.filter(
        category=product.category, 
        is_available=True
    ).exclude(id=product.id)[:4]

    # Exactly 3 related photos for product description section
    description_photos = []
    # 1. Product gallery images
    for g_img in product.images.all():
        img_url = g_img.display_image
        if img_url and not any(p['url'] == img_url for p in description_photos):
            description_photos.append({
                'url': img_url,
                'title': g_img.alt_text or f"{product.name} - ডিটেইল ফটো",
                'badge': 'ডিটেইল ফটো',
            })
        if len(description_photos) >= 3:
            break

    # 2. If fewer than 3, add images from related products in the same category
    if len(description_photos) < 3:
        for rp in related_products:
            rp_img = rp.display_image
            if rp_img and not any(p['url'] == rp_img for p in description_photos):
                description_photos.append({
                    'url': rp_img,
                    'title': f"{rp.name}",
                    'badge': 'সম্পর্কিত পোশাক',
                    'slug': rp.slug
                })
            if len(description_photos) >= 3:
                break

    # 3. Curated lifestyle/fabric detail fallbacks
    curated_fallbacks = [
        {'url': 'https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=800&q=80', 'title': '১০০% সুতি ফেব্রিক টেক্সচার', 'badge': 'ফেব্রিক জুম'},
        {'url': 'https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?auto=format&fit=crop&w=800&q=80', 'title': 'নিখুঁত কলার ও স্টিচিং ডিটেইল', 'badge': 'হ্যান্ডক্রাফট'},
        {'url': 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=800&q=80', 'title': 'প্রিমিয়াম ফিট ও কাটিং', 'badge': 'ফিটিং ভিউ'},
    ]
    for fb in curated_fallbacks:
        if len(description_photos) >= 3:
            break
        if not any(p['url'] == fb['url'] for p in description_photos):
            description_photos.append(fb)

    description_photos = description_photos[:3]

    context = {
        'product': product,
        'variants': variants,
        'sizes': sizes,
        'colors': colors,
        'default_variant': first_variant,
        'reviews': reviews,
        'review_count': reviews.count(),
        'avg_rating': avg_rating,
        'related_products': related_products,
        'description_photos': description_photos,
    }
    return render(request, 'store/product_detail.html', context)


@require_GET
def get_variant_info(request, product_id):
    """
    HTMX / JSON endpoint to query variant stock, price, and availability
    when customer selects a specific size and color combination.
    """
    size_id = request.GET.get('size_id')
    color_id = request.GET.get('color_id')

    query = Q(product_id=product_id, is_active=True)
    if size_id:
        query &= Q(size_id=size_id)
    if color_id:
        query &= Q(color_id=color_id)

    variant = ProductVariant.objects.filter(query).first()
    if not variant:
        return JsonResponse({
            'available': False,
            'stock': 0,
            'message': 'এই কম্বিনেশনটি বর্তমানে উপলব্ধ নেই (Not Available)',
        })

    return JsonResponse({
        'available': variant.stock > 0,
        'variant_id': variant.id,
        'sku': variant.sku,
        'stock': variant.stock,
        'price': str(variant.current_price),
        'formatted_price': f"৳ {int(variant.current_price):,}",
        'in_stock_text': f"মজুদ আছে ({variant.stock} টি অবশিষ্ট)" if variant.stock > 0 else "স্টক আউট (Out of Stock)",
    })


def track_order(request):
    """
    Customer order tracking by Mobile Number or Order Number.
    Displays current stage, courier tracking ID, item breakdown, and delivery address.
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
        ).prefetch_related('items', 'status_history').first()

        if order:
            status_map = {
                Order.STATUS_PENDING: 1,
                Order.STATUS_CONFIRMED: 2,
                Order.STATUS_PROCESSING: 3,
                Order.STATUS_PACKED: 3,
                Order.STATUS_SHIPPED: 4,
                Order.STATUS_DELIVERED: 5,
                Order.STATUS_CANCELLED: 0,
                Order.STATUS_RETURNED: 0,
            }
            status_step = status_map.get(order.status, 1)

    context = {
        'order': order,
        'query': query,
        'searched': searched,
        'status_step': status_step,
    }
    return render(request, 'store/track_order.html', context)


def guide_view(request):
    """Size chart and fabric care guide."""
    return render(request, 'store/guide.html')


def health_check(request):
    """Production health-check endpoint for load balancers and uptime monitors."""
    return HttpResponse("OK", content_type="text/plain")


def robots_txt(request):
    """SEO robots.txt file."""
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /cart/checkout/",
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request):
    """SEO XML sitemap listing active clothing products and categories."""
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_available=True)

    items = []
    base_url = request.build_absolute_uri('/')[:-1]

    # Home
    items.append(f"<url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>")

    for cat in categories:
        items.append(f"<url><loc>{base_url}/?category={cat.slug}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")

    for prod in products:
        items.append(f"<url><loc>{base_url}/product/{prod.slug}/</loc><lastmod>{prod.updated_at.strftime('%Y-%m-%d')}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(items)}
</urlset>"""
    return HttpResponse(xml_content, content_type="application/xml")


def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)
