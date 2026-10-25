from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from store.models import Category, Product, ProductVariant, Size, Color


class StoreCatalogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Panjabi",
            name_bn="পাঞ্জাবি",
            slug="panjabi",
            is_active=True
        )
        self.size_40 = Size.objects.create(name="40", display_order=1)
        self.size_42 = Size.objects.create(name="42", display_order=2)
        self.color_navy = Color.objects.create(name="Royal Navy", name_bn="রয়্যাল নেভি ব্লু", hex_code="#1e3a8a")

        self.product = Product.objects.create(
            category=self.category,
            name="Silk Cotton Panjabi",
            name_bn="সিল্ক কটন পাঞ্জাবি",
            slug="silk-cotton-panjabi",
            sku="WV-PAN-01",
            price=Decimal("2000.00"),
            discount_price=Decimal("1800.00"),
            is_available=True,
            is_featured=True,
        )

        self.variant_40 = ProductVariant.objects.create(
            product=self.product,
            size=self.size_40,
            color=self.color_navy,
            sku="WV-PAN-01-40-NVY",
            stock=15,
            is_active=True
        )

    def test_product_properties(self):
        self.assertEqual(self.product.current_price, Decimal("1800.00"))
        self.assertTrue(self.product.has_discount)
        self.assertEqual(self.product.discount_percent, 10)
        self.assertEqual(self.product.total_stock, 15)
        self.assertTrue(self.product.is_in_stock)

    def test_variant_unique_constraint(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ProductVariant.objects.create(
                product=self.product,
                size=self.size_40,
                color=self.color_navy,
                sku="WV-PAN-01-40-NVY-DUPLICATE",
                stock=5
            )

    def test_homepage_filtering_and_search(self):
        # 1. Search in English
        response = self.client.get(reverse('store:home'), {'q': 'Silk'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Silk Cotton Panjabi")

        # 2. Search in Bangla
        response_bn = self.client.get(reverse('store:home'), {'q': 'সিল্ক'})
        self.assertEqual(response_bn.status_code, 200)
        self.assertContains(response_bn, "সিল্ক কটন পাঞ্জাবি")

        # 3. Category Filter
        response_cat = self.client.get(reverse('store:home'), {'category': 'panjabi'})
        self.assertEqual(response_cat.status_code, 200)
        self.assertContains(response_cat, "Silk Cotton Panjabi")

        # 4. Size Filter
        response_size = self.client.get(reverse('store:home'), {'size': '40'})
        self.assertEqual(response_size.status_code, 200)
        self.assertContains(response_size, "Silk Cotton Panjabi")

    def test_product_detail_and_variant_info(self):
        response = self.client.get(reverse('store:product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Silk Cotton Panjabi")

        # Variant info endpoint
        v_url = reverse('store:get_variant_info', kwargs={'product_id': self.product.id})
        v_resp = self.client.get(v_url, {'size_id': self.size_40.id, 'color_id': self.color_navy.id})
        self.assertEqual(v_resp.status_code, 200)
        data = v_resp.json()
        self.assertTrue(data['available'])
        self.assertEqual(data['stock'], 15)
        self.assertEqual(data['sku'], "WV-PAN-01-40-NVY")

    def test_seo_and_health_endpoints(self):
        # Health check
        resp_health = self.client.get(reverse('store:health_check'))
        self.assertEqual(resp_health.status_code, 200)
        self.assertEqual(resp_health.content, b"OK")

        # robots.txt
        resp_robots = self.client.get(reverse('store:robots_txt'))
        self.assertEqual(resp_robots.status_code, 200)
        self.assertIn(b"User-agent: *", resp_robots.content)

        # sitemap.xml
        resp_sitemap = self.client.get(reverse('store:sitemap_xml'))
        self.assertEqual(resp_sitemap.status_code, 200)
        self.assertIn(b"<urlset", resp_sitemap.content)
