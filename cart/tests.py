from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from store.models import Category, Product, ProductVariant, Size, Color
from cart.models import Cart, CartItem
from cart.services import (
    get_or_create_cart,
    add_item_to_cart,
    merge_guest_cart_into_user_cart,
    calculate_order_financials,
    process_checkout,
)
from shipping.models import ShippingZone
from orders.models import Order


class CartAndCheckoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testcustomer', password='password123', email='test@customer.com')
        
        self.category = Category.objects.create(name="Shirts", slug="shirts")
        self.size_m = Size.objects.create(name="M")
        self.color_blue = Color.objects.create(name="Blue", hex_code="#0000ff")

        self.product = Product.objects.create(
            category=self.category,
            name="Formal Cotton Shirt",
            slug="formal-cotton-shirt",
            sku="WV-SH-01",
            price=Decimal("1500.00"),
            discount_price=Decimal("1200.00"),
            is_available=True
        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            size=self.size_m,
            color=self.color_blue,
            sku="WV-SH-01-M-BLU",
            stock=10,
            is_active=True
        )

        self.zone = ShippingZone.objects.create(
            code='DHAKA',
            name_en='Inside Dhaka',
            name_bn='ঢাকা মেট্রো',
            charge=Decimal('70.00'),
            free_delivery_allowed=True
        )

    def test_add_to_cart_and_stock_limits(self):
        session = self.client.session
        session.create()
        cart = Cart.objects.create(session_key=session.session_key)

        # Add 3 units
        success, msg, item = add_item_to_cart(cart, self.variant.id, 3)
        self.assertTrue(success)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(cart.subtotal, Decimal("3600.00"))  # 3 x ৳ 1,200

        # Attempt to add more than stock (currently 3 in cart, stock is 10, try adding 8)
        success, msg, item = add_item_to_cart(cart, self.variant.id, 8)
        self.assertFalse(success)
        self.assertIn("Only 10 items available in stock", msg)

    def test_guest_cart_merge_on_login(self):
        # Create guest session cart
        session = self.client.session
        session.create()
        guest_cart = Cart.objects.create(session_key=session.session_key)
        add_item_to_cart(guest_cart, self.variant.id, 2)

        # Mock request with session
        class MockRequest:
            def __init__(self, s):
                self.session = s

        mock_req = MockRequest(session)
        merge_guest_cart_into_user_cart(mock_req, self.user)

        user_cart = Cart.objects.filter(user=self.user).first()
        self.assertIsNotNone(user_cart)
        self.assertEqual(user_cart.total_items, 2)
        # Verify guest cart is cleared
        self.assertFalse(Cart.objects.filter(session_key=session.session_key).exists())

    def test_process_checkout_inventory_deduction(self):
        cart = Cart.objects.create(user=self.user)
        add_item_to_cart(cart, self.variant.id, 2)

        class MockRequest:
            def __init__(self, u, c):
                self.user = u
                self.session = Client().session

        mock_req = MockRequest(self.user, cart)

        form_data = {
            'full_name': 'Sakib Al Hasan',
            'phone_number': '01711223344',
            'address': 'Dhanmondi, Dhaka',
            'district': 'Dhaka',
            'delivery_zone': 'DHAKA',
            'payment_method': Order.PAYMENT_COD,
        }

        initial_stock = self.variant.stock
        order = process_checkout(mock_req, form_data)

        self.assertIsNotNone(order)
        self.assertEqual(order.full_name, 'Sakib Al Hasan')
        self.assertEqual(order.subtotal, Decimal("2400.00"))
        self.assertEqual(order.total_amount, Decimal("2470.00"))  # 2400 + 70 delivery
        self.assertEqual(order.items.count(), 1)

        # Refresh variant from DB and verify stock decremented by 2
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, initial_stock - 2)

        # Cart should be empty
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)
