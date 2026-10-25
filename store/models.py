from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """
    Enterprise-level Category model.
    Admin can dynamically create, edit, reorder, or toggle categories anytime
    (e.g., Panjabi, Shirts, T-Shirts, Pants, Polo, Winter Collection).
    """
    name = models.CharField(max_length=120, unique=True, help_text="Category name (e.g., Panjabi, Casual Shirts, T-Shirts)")
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(blank=True, default='', help_text="Short description in simple language")
    display_order = models.PositiveIntegerField(default=0, help_text="Order in menus (lower numbers appear first: 1, 2, 3...)")
    is_active = models.BooleanField(default=True, help_text="Check to display on the website; uncheck to hide")
    image_url = models.URLField(max_length=500, blank=True, help_text="Optional cover image URL for this category")

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        return self.products.filter(is_available=True).count()

    @property
    def display_image(self):
        if self.image_url:
            return self.image_url
        first_product = self.products.filter(is_available=True).first()
        if first_product:
            return first_product.display_image
        return 'https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=600&q=80'


class Product(models.Model):
    """
    Enterprise-level Product model with inventory, SKU, pricing in BDT,
    and size management suited for mass-market clothing businesses.
    """
    sku = models.CharField(
        max_length=50, 
        blank=True, 
        default='',
        help_text="Product Code / SKU (e.g., WV-PAN-01, WV-SH-02)"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products',
        help_text="Select category (Panjabi, Shirts, T-Shirts, etc.)"
    )
    name = models.CharField(max_length=220, help_text="Clear product title (e.g., Premium Cotton Panjabi)")
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(help_text="Product details written in simple language that customers understand easily")
    fabric_details = models.CharField(
        max_length=200, 
        default="100% Combed Cotton / প্রিমিয়াম সুতি", 
        blank=True,
        help_text="Fabric specification (e.g., 100% Cotton, Linen, Silk blend)"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Regular price in BDT (৳)"
    )
    discount_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Offer price in BDT (৳) if there is a discount"
    )
    image_url = models.URLField(
        max_length=600, 
        blank=True, 
        help_text="Direct image link"
    )
    image = models.ImageField(
        upload_to='products/', 
        blank=True, 
        null=True, 
        help_text="Upload local photo if available"
    )
    available_sizes = models.CharField(
        max_length=150, 
        default='38, 40, 42, 44', 
        help_text="Comma-separated sizes (Panjabi: 38, 40, 42, 44 | Shirts: M, L, XL, XXL)"
    )
    color = models.CharField(max_length=80, default='Standard / আসমানী নীল', help_text="Color name")
    badge = models.CharField(
        max_length=60, 
        blank=True, 
        help_text="Special tag (e.g., BESTSELLER, EID SPECIAL, NEW, HOT SALE)"
    )
    stock = models.PositiveIntegerField(default=50, help_text="Quantity available in stock")
    is_featured = models.BooleanField(default=False, help_text="Show on homepage top featured section")
    is_available = models.BooleanField(default=True, help_text="Set to False to mark as Out of Stock")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            cat_prefix = self.category.name[:3].upper() if self.category else "WVR"
            self.sku = f"{cat_prefix}-{slugify(self.name)[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (৳ {int(self.current_price)})"

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80'

    @property
    def current_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def has_discount(self):
        return bool(self.discount_price and self.discount_price < self.price)

    @property
    def discount_percent(self):
        if self.has_discount and self.price > 0:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return int(round(discount))
        return 0

    @property
    def size_list(self):
        return [s.strip() for s in self.available_sizes.split(',') if s.strip()]

    @property
    def formatted_price(self):
        return f"৳ {int(self.current_price):,}"

    @property
    def formatted_regular_price(self):
        return f"৳ {int(self.price):,}"
