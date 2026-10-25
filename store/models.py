from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Category(models.Model):
    """
    Hierarchical product category with bilingual support (English & Bangla).
    Configurable by admin (Panjabi, Shirts, T-Shirts, Jubba, Thobe, Pajama, etc.).
    """
    name = models.CharField(max_length=120, unique=True, help_text=_("Category name in English"))
    name_bn = models.CharField(max_length=120, blank=True, default='', help_text=_("Category name in Bangla"))
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    description = models.TextField(blank=True, default='', help_text=_("Description in English"))
    description_bn = models.TextField(blank=True, default='', help_text=_("Description in Bangla"))
    display_order = models.PositiveIntegerField(default=0, help_text=_("Order in menus (1, 2, 3...)"))
    is_active = models.BooleanField(default=True, help_text=_("Display on storefront"))
    image_url = models.URLField(max_length=600, blank=True, help_text=_("Cover image URL"))
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.name_bn:
            self.name_bn = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.name_bn})" if self.name_bn and self.name_bn != self.name else self.name

    @property
    def display_name(self):
        return self.name_bn if self.name_bn else self.name

    @property
    def product_count(self):
        return self.products.filter(is_available=True).count()

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        first_product = self.products.filter(is_available=True).first()
        if first_product:
            return first_product.display_image
        return 'https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=600&q=80'


class Size(models.Model):
    name = models.CharField(max_length=40, unique=True, help_text=_("Size label e.g., 38, 40, 42, 44, M, L, XL"))
    display_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('Size')
        verbose_name_plural = _('Sizes')

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=60, unique=True, help_text=_("Color in English (e.g., Royal Navy)"))
    name_bn = models.CharField(max_length=60, blank=True, default='', help_text=_("Color in Bangla (e.g., রয়্যাল নেভি ব্লু)"))
    hex_code = models.CharField(max_length=20, default='#1e293b', help_text=_("Hex color code e.g. #000000"))

    class Meta:
        ordering = ['name']
        verbose_name = _('Color')
        verbose_name_plural = _('Colors')

    def __str__(self):
        return f"{self.name} ({self.name_bn})" if self.name_bn else self.name


class Product(models.Model):
    """
    Enterprise-level Product catalog model with bilingual support,
    BDT pricing, and variant relationships.
    """
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products',
        help_text=_("Product category")
    )
    name = models.CharField(max_length=220, help_text=_("Product title in English"))
    name_bn = models.CharField(max_length=220, blank=True, default='', help_text=_("Product title in Bangla"))
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    sku = models.CharField(max_length=60, blank=True, default='', db_index=True, help_text=_("Base SKU code"))
    
    description = models.TextField(help_text=_("Product description in English"))
    description_bn = models.TextField(blank=True, default='', help_text=_("Product description in Bangla"))
    
    fabric_details = models.CharField(
        max_length=200, 
        default="100% Combed Cotton / ১০০% খাঁটি সুতি",
        blank=True
    )
    fabric_details_bn = models.CharField(max_length=200, blank=True, default='')

    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text=_("Regular retail price in BDT (৳)")
    )
    discount_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text=_("Discounted price in BDT (৳) if on promotion")
    )

    image_url = models.URLField(max_length=600, blank=True, default='')
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    badge = models.CharField(
        max_length=60, 
        blank=True, 
        default='',
        help_text=_("Promotional badge (e.g., BESTSELLER, EID SPECIAL, NEW, HOT SALE)")
    )
    
    stock = models.PositiveIntegerField(default=50, help_text=_("Base aggregate stock"))
    available_sizes = models.CharField(max_length=150, default='38, 40, 42, 44', blank=True)
    color = models.CharField(max_length=80, default='Standard', blank=True)

    is_featured = models.BooleanField(default=False, help_text=_("Display in homepage featured section"))
    is_new_arrival = models.BooleanField(default=True, help_text=_("Mark as new arrival"))
    is_available = models.BooleanField(default=True, help_text=_("Overall active/published status"))
    display_order = models.PositiveIntegerField(
        default=100, 
        help_text=_("Position order (1 = first, 2 = second, etc.). Lower number appears first across pages.")
    )

    # SEO metadata
    meta_title = models.CharField(max_length=250, blank=True, default='')
    meta_description = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-is_featured', '-created_at']
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            cat_code = self.category.slug[:3].upper() if self.category else "WVR"
            self.sku = f"{cat_code}-{slugify(self.name)[:8].upper()}"
        if not self.name_bn:
            self.name_bn = self.name
        if not self.description_bn:
            self.description_bn = self.description
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (৳ {int(self.current_price)})"

    @property
    def regular_price(self):
        return self.price

    @property
    def sale_price(self):
        return self.discount_price

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
    def display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        first_img = self.images.first()
        if first_img:
            return first_img.display_image
        return 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80'

    @property
    def total_stock(self):
        variant_count = self.variants.filter(is_active=True).count()
        if variant_count > 0:
            val = self.variants.filter(is_active=True).aggregate(models.Sum('stock'))['stock__sum']
            return val if val is not None else 0
        return self.stock

    @property
    def is_in_stock(self):
        return self.total_stock > 0

    @property
    def formatted_price(self):
        return f"৳ {int(self.current_price):,}"

    @property
    def formatted_regular_price(self):
        return f"৳ {int(self.price):,}"

    @property
    def size_list(self):
        variant_sizes = list(self.variants.filter(is_active=True).values_list('size__name', flat=True).distinct())
        if variant_sizes:
            return [s for s in variant_sizes if s]
        return [s.strip() for s in self.available_sizes.split(',') if s.strip()]


class ProductVariant(models.Model):
    """
    Individual variant combinations (Size + Color).
    Has its own unique SKU, stock quantity, and optional price override.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name='variants')
    sku = models.CharField(max_length=80, unique=True, help_text=_("Variant SKU code (e.g. WV-PAN-01-40-BLU)"))
    price_override = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text=_("Optional price override in BDT")
    )
    stock = models.PositiveIntegerField(default=10, help_text=_("Current inventory count"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['size__display_order', 'color__name']
        constraints = [
            models.UniqueConstraint(fields=['product', 'size', 'color'], name='unique_product_variant')
        ]
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')

    def __str__(self):
        size_name = self.size.name if self.size else 'Standard'
        color_name = self.color.name if self.color else ''
        details = f"{size_name}" + (f" - {color_name}" if color_name else "")
        return f"{self.product.name} ({details}) [Stock: {self.stock}]"

    def save(self, *args, **kwargs):
        if not self.sku:
            size_part = self.size.name if self.size else "STD"
            color_part = self.color.name[:3].upper() if self.color else "DEF"
            self.sku = f"{self.product.sku}-{size_part}-{color_part}".replace(' ', '')
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        if self.price_override is not None:
            return self.price_override
        return self.product.current_price

    @property
    def is_in_stock(self):
        return self.is_active and self.stock > 0


class ProductImage(models.Model):
    """
    Multi-image gallery per product.
    Supports zooming, thumbnails, and responsive views.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=600, blank=True, default='')
    image = models.ImageField(upload_to='products/gallery/', blank=True, null=True)
    alt_text = models.CharField(max_length=200, blank=True, default='')
    display_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')

    def __str__(self):
        return f"Image #{self.display_order} for {self.product.name}"

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80'
