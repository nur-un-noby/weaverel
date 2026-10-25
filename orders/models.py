import uuid
from django.db import models
from store.models import Product


class Order(models.Model):
    """
    Enterprise Order model for clothing business.
    Handles customer contact, delivery zones, order statuses, and totals in BDT.
    """
    DELIVERY_CHOICES = [
        ('DHAKA', 'Inside Dhaka / ঢাকা মেট্রো (৳ 70)'),
        ('SUBURB', 'Dhaka Suburbs / সাভার, গাজীপুর, নারায়ণগঞ্জ (৳ 100)'),
        ('OUTSIDE', 'Outside Dhaka / সমগ্র বাংলাদেশ (৳ 130)'),
    ]

    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery (ক্যাশ অন ডেলিভারি - পণ্য দেখে টাকা দিন)'),
        ('BKASH', 'bKash / Nagad Mobile Banking (বিকাশ / নগদ)'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending (অর্ডার গৃহীত হয়েছে)'),
        ('CONFIRMED', 'Confirmed (অর্ডার নিশ্চিত)'),
        ('PROCESSING', 'Packaging (প্যাকিং চলছে)'),
        ('SHIPPED', 'Handed over to Courier / ডেলিভারিতে পাঠানো হয়েছে'),
        ('DELIVERED', 'Delivered (ডেলিভারি সম্পন্ন)'),
        ('CANCELLED', 'Cancelled (বাতিলকৃত)'),
    ]

    order_number = models.CharField(max_length=30, unique=True, editable=False)
    
    # Customer Details (in simple, accessible format)
    full_name = models.CharField(max_length=150, help_text="Customer Full Name (ক্রেতার পুরো নাম)")
    phone_number = models.CharField(max_length=20, help_text="Mobile Number (সচল মোবাইল নম্বর e.g. 017XXXXXXXX)")
    alternative_phone = models.CharField(max_length=20, blank=True, help_text="Alternative Mobile Number (ঐচ্ছিক)")
    address = models.TextField(help_text="Full Delivery Address (বাসা/রোড/এলাকার নাম)")
    delivery_zone = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='DHAKA')
    
    # Payment and Status
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Financials in BDT
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=70.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    customer_notes = models.TextField(blank=True, help_text="Special instructions (e.g. ডেলিভারির আগে কল করবেন)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate clean enterprise order ID like WV-2610-8492
            self.order_number = f"WV-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} - {self.full_name} (৳ {int(self.total_amount)})"

    @property
    def total_items_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """
    Individual items inside a customer order.
    Saves snapshot of price, size, and SKU to maintain historical audit integrity.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=250)
    product_sku = models.CharField(max_length=60, blank=True)
    size = models.CharField(max_length=40, default='Standard')
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in BDT at time of order")
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} (Size: {self.size}, Qty: {self.quantity})"
