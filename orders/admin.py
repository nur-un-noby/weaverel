from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'size', 'price', 'quantity', 'total_price')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Enterprise Order management panel for staff and store admins.
    Shows customer phone, full address, delivery zone, and ordered items.
    """
    list_display = (
        'order_number', 
        'full_name', 
        'phone_number', 
        'delivery_zone', 
        'payment_method', 
        'total_amount_bdt', 
        'status', 
        'created_at'
    )
    list_filter = ('status', 'delivery_zone', 'payment_method', 'created_at')
    list_editable = ('status',)
    search_fields = ('order_number', 'full_name', 'phone_number', 'address')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'subtotal', 'delivery_charge', 'total_amount')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'

    def total_amount_bdt(self, obj):
        return f"৳ {int(obj.total_amount):,}"
    total_amount_bdt.short_description = "Total Amount"

    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered']

    @admin.action(description='Mark selected orders as Confirmed')
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='CONFIRMED')

    @admin.action(description='Mark selected orders as Shipped (Handed over to courier)')
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='SHIPPED')

    @admin.action(description='Mark selected orders as Delivered')
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='DELIVERED')
