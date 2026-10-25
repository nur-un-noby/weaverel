import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from store.models import Product, ProductVariant
from shipping.models import ShippingZone
from promotions.models import Coupon


class Order(models.Model):
    """
    Enterprise Order model with state machine transitions,
    bilingual status tracking, snapshot storage, and audit logs.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_PACKED = 'PACKED'
    STATUS_SHIPPED = 'SHIPPED'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_RETURNED = 'RETURNED'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending Confirmation / অপেক্ষমাণ')),
        (STATUS_CONFIRMED, _('Confirmed / নিশ্চিতকৃত')),
        (STATUS_PROCESSING, _('Processing / প্যাকেজিং চলছে')),
        (STATUS_PACKED, _('Packed / পার্সেল প্রস্তুত')),
        (STATUS_SHIPPED, _('Shipped / কুরিয়ারে হস্তান্তর')),
        (STATUS_DELIVERED, _('Delivered / সফলভাবে ডেলিভারি সম্পন্ন')),
        (STATUS_CANCELLED, _('Cancelled / বাতিলকৃত')),
        (STATUS_RETURNED, _('Returned / ফেরত')),
    ]

    PAYMENT_COD = 'COD'

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_COD, _('Cash on Delivery (ক্যাশ অন ডেলিভারি)')),
    ]

    PAYMENT_STATUS_PENDING = 'PENDING'
    PAYMENT_STATUS_PAID = 'PAID'
    PAYMENT_STATUS_FAILED = 'FAILED'
    PAYMENT_STATUS_CANCELLED = 'CANCELLED'
    PAYMENT_STATUS_REFUNDED = 'REFUNDED'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, _('Payment Pending / পরিশোধ অপেক্ষমাণ')),
        (PAYMENT_STATUS_PAID, _('Paid / সম্পূর্ণ পরিশোধিত')),
        (PAYMENT_STATUS_FAILED, _('Failed / ব্যর্থ')),
        (PAYMENT_STATUS_CANCELLED, _('Cancelled / বাতিল')),
        (PAYMENT_STATUS_REFUNDED, _('Refunded / রিফান্ড সম্পন্ন')),
    ]

    DELIVERY_CHOICES = [
        ('DHAKA', 'Inside Dhaka / ঢাকা মেট্রো (৳ 70)'),
        ('SUBURB', 'Dhaka Suburbs / সাভার, গাজীপুর, নারায়ণগঞ্জ (৳ 100)'),
        ('OUTSIDE', 'Outside Dhaka / সমগ্র বাংলাদেশ (৳ 130)'),
    ]

    ALLOWED_TRANSITIONS = {
        STATUS_PENDING: [STATUS_CONFIRMED, STATUS_CANCELLED],
        STATUS_CONFIRMED: [STATUS_PROCESSING, STATUS_CANCELLED],
        STATUS_PROCESSING: [STATUS_PACKED, STATUS_CANCELLED],
        STATUS_PACKED: [STATUS_SHIPPED, STATUS_CANCELLED],
        STATUS_SHIPPED: [STATUS_DELIVERED, STATUS_RETURNED],
        STATUS_DELIVERED: [STATUS_RETURNED],
        STATUS_CANCELLED: [],
        STATUS_RETURNED: [],
    }

    order_number = models.CharField(max_length=40, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    # Customer Contact Info
    full_name = models.CharField(max_length=150, help_text=_("Customer name"))
    phone_number = models.CharField(max_length=25, db_index=True, help_text=_("Primary Bangladesh mobile number"))
    alternative_phone = models.CharField(max_length=25, blank=True, default='')
    email = models.EmailField(blank=True, default='')

    # Delivery Details
    shipping_zone = models.ForeignKey(ShippingZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    delivery_zone = models.CharField(max_length=30, choices=DELIVERY_CHOICES, default='DHAKA')
    district = models.CharField(max_length=100, default='Dhaka')
    address = models.TextField(help_text=_("Full delivery address (house/road/area)"))

    # Statuses
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_COD)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING, db_index=True)

    # Financial Breakdowns in BDT
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('70.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Promotion link
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    coupon_code = models.CharField(max_length=50, blank=True, default='')

    customer_notes = models.TextField(blank=True, default='', help_text=_("Special instructions from customer"))
    admin_notes = models.TextField(blank=True, default='', help_text=_("Internal order fulfillment notes"))
    tracking_number = models.CharField(max_length=100, blank=True, default='', help_text=_("Courier tracking ID"))

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"WV-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} - {self.full_name} (৳ {int(self.total_amount):,})"

    @property
    def shipping_charge(self):
        return self.delivery_charge

    @property
    def total_items_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def is_cancellable_by_customer(self):
        return self.status == self.STATUS_PENDING

    def can_transition_to(self, new_status):
        if self.status == new_status:
            return True
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        return new_status in allowed

    def update_status(self, new_status, user=None, notes=""):
        if not self.can_transition_to(new_status):
            raise ValueError(f"Illegal status transition from '{self.status}' to '{new_status}'")
        
        old_status = self.status
        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])

        OrderStatusHistory.objects.create(
            order=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            notes=notes
        )


class OrderItem(models.Model):
    """
    Immutable snapshot of items ordered.
    Preserves exact pricing, size, color, SKU and names even if product is deleted.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    
    product_name = models.CharField(max_length=250)
    product_name_bn = models.CharField(max_length=250, blank=True, default='')
    product_sku = models.CharField(max_length=80, blank=True, default='')
    size = models.CharField(max_length=50, default='Standard')
    color_name = models.CharField(max_length=60, blank=True, default='')
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text=_("BDT price at time of purchase"))
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} ({self.size}) x {self.quantity}"

    @property
    def unit_price(self):
        return self.price

    @property
    def size_name(self):
        return self.size


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Order Status History')
        verbose_name_plural = _('Order Status Histories')

    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} -> {self.new_status}"
