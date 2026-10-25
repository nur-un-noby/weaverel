from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'product_sku', 'size_name', 'color_name', 'unit_price', 'quantity', 'total_price')
    readonly_fields = ('product_name', 'product_sku', 'size_name', 'color_name', 'unit_price', 'quantity', 'total_price')
    can_delete = False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'notes', 'created_at')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'full_name',
        'phone_number',
        'district',
        'payment_method',
        'payment_status',
        'status',
        'formatted_total',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'payment_status', 'district', 'created_at')
    list_editable = ('status', 'payment_status')
    search_fields = ('order_number', 'full_name', 'phone_number', 'address', 'tracking_number')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'subtotal', 'discount_amount', 'shipping_charge', 'total_amount')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Order Identification', {
            'fields': ('order_number', 'status', 'created_at', 'updated_at')
        }),
        ('Customer & Delivery Information', {
            'fields': ('full_name', 'phone_number', 'alternative_phone', 'email', 'district', 'address', 'customer_notes', 'tracking_number')
        }),
        ('Payment & Financials', {
            'fields': ('payment_method', 'payment_status', 'subtotal', 'discount_amount', 'coupon_code', 'shipping_charge', 'total_amount')
        }),
        ('Internal Administration', {
            'fields': ('admin_notes',)
        }),
    )

    def formatted_total(self, obj):
        return f"৳ {int(obj.total_amount):,}"
    formatted_total.short_description = "Total BDT"

    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_paid']

    @admin.action(description='Transition status: Mark as Confirmed')
    def mark_as_confirmed(self, request, queryset):
        for order in queryset:
            if order.can_transition_to(Order.STATUS_CONFIRMED):
                order.update_status(Order.STATUS_CONFIRMED, user=request.user, notes="Bulk confirmed by admin")

    @admin.action(description='Transition status: Mark as Processing / Packaging')
    def mark_as_processing(self, request, queryset):
        for order in queryset:
            if order.can_transition_to(Order.STATUS_PROCESSING):
                order.update_status(Order.STATUS_PROCESSING, user=request.user, notes="Packaging in progress")

    @admin.action(description='Transition status: Mark as Shipped to Courier')
    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            if order.can_transition_to(Order.STATUS_SHIPPED):
                order.update_status(Order.STATUS_SHIPPED, user=request.user, notes="Dispatched to courier")

    @admin.action(description='Transition status: Mark as Delivered')
    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            if order.can_transition_to(Order.STATUS_DELIVERED):
                order.update_status(Order.STATUS_DELIVERED, user=request.user, notes="Delivered to customer")

    @admin.action(description='Payment status: Mark as Paid')
    def mark_as_paid(self, request, queryset):
        queryset.update(payment_status=Order.PAYMENT_STATUS_PAID)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status', 'created_at')
    search_fields = ('order__order_number', 'notes')
