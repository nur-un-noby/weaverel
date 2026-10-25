from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from decimal import Decimal

from orders.models import Order, OrderItem
from store.models import Product, ProductVariant
from promotions.models import Coupon, CouponUsage
from store_settings.models import SiteConfiguration


@staff_member_required
def admin_analytics_view(request):
    """
    Executive administration reporting dashboard:
    - Order counts & Fulfillment status
    - Total paid revenue vs. pending COD awaiting collection
    - Low-stock inventory warnings
    - Best-selling clothing products
    - Coupon usage breakdown
    """
    total_orders = Order.objects.count()
    pending_orders_count = Order.objects.filter(status=Order.STATUS_PENDING).count()
    confirmed_orders_count = Order.objects.filter(status=Order.STATUS_CONFIRMED).count()
    delivered_orders_count = Order.objects.filter(status=Order.STATUS_DELIVERED).count()

    # Revenue metrics
    paid_revenue = Order.objects.filter(payment_status=Order.PAYMENT_STATUS_PAID).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    cod_awaiting = Order.objects.filter(payment_method=Order.PAYMENT_COD, payment_status=Order.PAYMENT_STATUS_PENDING).exclude(status=Order.STATUS_CANCELLED).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    gross_order_value = Order.objects.exclude(status=Order.STATUS_CANCELLED).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # Low-Stock warnings (Variant stock <= 10)
    low_stock_variants = ProductVariant.objects.filter(stock__lte=10, is_active=True).select_related('product', 'size', 'color').order_by('stock')[:15]

    # Best-selling products
    best_sellers = OrderItem.objects.values('product__id', 'product__name').annotate(
        total_sold=Sum('quantity'),
        total_sales=Sum('total_price')
    ).order_by('-total_sold')[:5]

    # Recent Orders
    recent_orders = Order.objects.all().order_by('-created_at')[:10]

    # Coupon usage
    coupons = Coupon.objects.all().order_by('-usage_count')[:5]

    context = {
        'total_orders': total_orders,
        'pending_orders_count': pending_orders_count,
        'confirmed_orders_count': confirmed_orders_count,
        'delivered_orders_count': delivered_orders_count,
        'paid_revenue': paid_revenue,
        'cod_awaiting': cod_awaiting,
        'gross_order_value': gross_order_value,
        'low_stock_variants': low_stock_variants,
        'best_sellers': best_sellers,
        'recent_orders': recent_orders,
        'coupons': coupons,
        'title': 'Executive Business Analytics',
    }
    return render(request, 'admin/analytics_dashboard.html', context)
