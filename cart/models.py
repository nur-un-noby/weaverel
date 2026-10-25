from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from store.models import ProductVariant
from decimal import Decimal


class Cart(models.Model):
    """
    Shopping cart supporting both guest visitors (via session_key)
    and authenticated customers (via user FK).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')

    def __str__(self):
        owner = self.user.username if self.user else f"Session: {self.session_key[:8]}"
        return f"Cart ({owner}) - {self.total_items} items"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.select_related('variant', 'variant__product'))

    def clear(self):
        self.items.all().delete()


class CartItem(models.Model):
    """
    Cart line item linked to a specific ProductVariant.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(fields=['cart', 'variant'], name='unique_cart_variant')
        ]
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')

    def __str__(self):
        return f"{self.variant} x {self.quantity}"

    @property
    def unit_price(self):
        return self.variant.current_price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    @property
    def is_in_stock(self):
        return self.variant.is_in_stock and self.variant.stock >= self.quantity
