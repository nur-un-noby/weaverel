from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from store.models import Product


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    customer_name = models.CharField(max_length=120)
    customer_location = models.CharField(max_length=100, default='ঢাকা', blank=True, help_text=_("City or district (e.g. ঢাকা, চট্টগ্রাম)"))
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Star rating from 1 to 5")
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_verified_buyer = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True, help_text=_("Moderation status; only approved reviews are displayed"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Product Review')
        verbose_name_plural = _('Product Reviews')

    def __str__(self):
        return f"{self.customer_name} - {self.rating}★ on {self.product.name}"
