from django.contrib import admin
from .models import Coupon, CouponUsage


class CouponUsageInline(admin.TabularInline):
    model = CouponUsage
    extra = 0
    readonly_fields = ('user', 'guest_phone', 'order_number', 'discount_applied', 'used_at')
    can_delete = False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_purchase_amount', 'usage_count', 'usage_limit', 'is_active', 'valid_to')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_to')
    list_editable = ('is_active',)
    search_fields = ('code',)
    inlines = [CouponUsageInline]


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'guest_phone', 'order_number', 'discount_applied', 'used_at')
    list_filter = ('coupon', 'used_at')
    search_fields = ('order_number', 'guest_phone', 'user__username', 'coupon__code')
