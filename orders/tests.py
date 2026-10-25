from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from orders.models import Order, OrderItem, OrderStatusHistory


class OrderLifecycleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ordertester', password='password123')
        self.order = Order.objects.create(
            user=self.user,
            full_name="Mahmud Hasan",
            phone_number="01711223344",
            address="Banani, Dhaka",
            delivery_zone="DHAKA",
            payment_method=Order.PAYMENT_COD,
            subtotal=Decimal("1800.00"),
            delivery_charge=Decimal("70.00"),
            total_amount=Decimal("1870.00"),
            status=Order.STATUS_PENDING
        )

    def test_legal_status_transitions_and_history(self):
        self.assertEqual(self.order.status, Order.STATUS_PENDING)
        self.assertTrue(self.order.is_cancellable_by_customer)

        # Transition 1: PENDING -> CONFIRMED
        self.order.update_status(Order.STATUS_CONFIRMED, user=self.user, notes="Customer confirmed phone call")
        self.assertEqual(self.order.status, Order.STATUS_CONFIRMED)
        self.assertFalse(self.order.is_cancellable_by_customer)

        # Transition 2: CONFIRMED -> PROCESSING
        self.order.update_status(Order.STATUS_PROCESSING, user=self.user, notes="Packaging order")
        self.assertEqual(self.order.status, Order.STATUS_PROCESSING)

        # Transition 3: PROCESSING -> PACKED
        self.order.update_status(Order.STATUS_PACKED, user=self.user, notes="Box sealed")
        self.assertEqual(self.order.status, Order.STATUS_PACKED)

        # Transition 4: PACKED -> SHIPPED
        self.order.update_status(Order.STATUS_SHIPPED, user=self.user, notes="Dispatched to Steadfast Courier")
        self.assertEqual(self.order.status, Order.STATUS_SHIPPED)

        # Transition 5: SHIPPED -> DELIVERED
        self.order.update_status(Order.STATUS_DELIVERED, user=self.user, notes="Customer received item")
        self.assertEqual(self.order.status, Order.STATUS_DELIVERED)

        # Verify audit history count
        self.assertEqual(OrderStatusHistory.objects.filter(order=self.order).count(), 5)

    def test_illegal_status_transition_raises_error(self):
        # DELIVERED order cannot be transitioned directly back to PENDING
        self.order.status = Order.STATUS_DELIVERED
        self.order.save()

        with self.assertRaises(ValueError):
            self.order.update_status(Order.STATUS_PENDING, notes="Illegal attempt")
