from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class SiteConfiguration(models.Model):
    """
    Singleton model for enterprise store configuration.
    Enables administrators to customize store name, contact info,
    announcements, delivery thresholds, and social links without code edits.
    """
    site_name = models.CharField(
        max_length=150, default="Weaverel Apparel", help_text=_("Brand name in English"))
    site_name_bn = models.CharField(
        max_length=150, default="উইভারেল অ্যাপারেল", help_text=_("Brand name in Bangla"))
    logo = models.ImageField(
        upload_to="branding/", blank=True, null=True, help_text=_("Brand logo image (Header & Footer)"))
    tagline = models.CharField(
        max_length=255, default="Premium Clothing for Everyday Elegance", blank=True)
    tagline_bn = models.CharField(
        max_length=255, default="প্রিমিয়াম পাঞ্জাবি, শার্ট ও টি-শার্ট কালেকশন", blank=True)

    # Announcement Bar
    announcement_active = models.BooleanField(
        default=True, help_text=_("Show top announcement banner"))
    announcement_text_en = models.CharField(
        max_length=300,
        default="🚚 Cash on Delivery Nationwide | Free Shipping on orders over ৳ 2,500!",
        help_text=_("Announcement in English")
    )
    announcement_text_bn = models.CharField(
        max_length=300,
        default="🚚 সারাদেশে ক্যাশ অন ডেলিভারি | ৳ ২,৫০০+ অর্ডারে ডেলিভারি চার্জ সম্পূর্ণ ফ্রি!",
        help_text=_("Announcement in Bangla")
    )

    # Contact Information
    contact_phone = models.CharField(max_length=30, default="01334202784")
    whatsapp_number = models.CharField(max_length=30, default="8801334202784", help_text=_(
        "Without + sign (e.g., 8801334202784)"))
    contact_email = models.EmailField(default="weaverelshop@gmail.com.com")
    address_en = models.TextField(
        default="Jatrabari Kutubkhali Boro Madrasa Road, Dhaka-1205, Bangladesh")
    address_bn = models.TextField(
        default="বাড়ি ১২, রোড ৪, ধানমন্ডি, ঢাকা-১২০৫, বাংলাদেশ")

    # Financial and Delivery Rules
    currency_symbol = models.CharField(max_length=10, default="৳")
    currency_code = models.CharField(max_length=10, default="BDT")
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("2500.00"),
        help_text=_("Cart subtotal threshold in BDT for free shipping")
    )
    enable_cod = models.BooleanField(
        default=True, help_text=_("Allow Cash on Delivery checkout"))

    # Social Links
    facebook_url = models.URLField(
        blank=True, default="https://facebook.com/weaverel")
    instagram_url = models.URLField(
        blank=True, default="https://instagram.com/weaverel")
    youtube_url = models.URLField(blank=True, default="")

    # SEO
    meta_title = models.CharField(
        max_length=255, default="Weaverel | Premium Bangladeshi Clothing Brand", blank=True)
    meta_description = models.TextField(
        default="Shop exclusive Panjabi, Shirts, T-Shirts, Pajamas and Modest Men's Wear in Bangladesh. High quality fabrics, fast home delivery & easy COD.",
        blank=True
    )

    class Meta:
        verbose_name = _("Site Configuration")
        verbose_name_plural = _("Site Configuration")

    def __str__(self):
        return f"{self.site_name} Configuration"

    def save(self, *args, **kwargs):
        # Guarantee singleton pattern
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class HeroBanner(models.Model):
    """
    Manageable homepage carousel/hero section banners.
    """
    title_en = models.CharField(
        max_length=200, default="Authentic Bangladeshi Clothing")
    title_bn = models.CharField(
        max_length=200, default="খাঁটি কাপড়ে তৈরি প্রিমিয়াম পাঞ্জাবি ও ক্যাজুয়াল কালেকশন")
    subtitle_en = models.TextField(
        default="100% Combed Cotton, Linen, and Silk blends for festive and daily comfort.", blank=True)
    subtitle_bn = models.TextField(
        default="১০০% কম্বড সুতি ও লিনেন ফেব্রিকে তৈরি আরামদায়ক পোশাক। নিখুঁত সেলাই ও সারা দেশে দ্রুত ক্যাশ অন ডেলিভারি।", blank=True)
    badge_en = models.CharField(
        max_length=80, default="✨ NEW FESTIVE COLLECTION 2026", blank=True)
    badge_bn = models.CharField(
        max_length=80, default="✨ নতুন ঈদ ও ফেস্টিভ কালেকশন ২০২৬", blank=True)
    button_text_en = models.CharField(
        max_length=80, default="Shop Collection ↓")
    button_text_bn = models.CharField(
        max_length=80, default="পণ্যসমূহ দেখুন ↓")
    button_link = models.CharField(max_length=255, default="#products-grid")
    image_url = models.URLField(
        max_length=600, default="https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=2000&q=80")
    image = models.ImageField(upload_to="banners/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = _("Hero Banner")
        verbose_name_plural = _("Hero Banners")

    def __str__(self):
        return self.title_en

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url
