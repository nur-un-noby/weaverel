from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from store.models import Product


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Wishlist')
        verbose_name_plural = _('Wishlists')

    def __str__(self):
        return f"{self.user.username}'s Wishlist ({self.items.count()} items)"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(fields=['wishlist', 'product'], name='unique_wishlist_product')
        ]
        verbose_name = _('Wishlist Item')
        verbose_name_plural = _('Wishlist Items')

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s Wishlist"
