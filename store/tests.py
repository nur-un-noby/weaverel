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

    def test_twelve_products_per_page_pagination(self):
        # Create additional products to reach 15 products total
        for i in range(2, 16):
            Product.objects.create(
                category=self.category,
                name=f"Demo Clothing Product {i}",
                name_bn=f"ডেমো পোশাক {i}",
                slug=f"demo-product-{i}",
                sku=f"WV-TST-{i:02d}",
                price=Decimal("1500.00"),
                is_available=True,
                display_order=i
            )

        # Page 1: exactly 12 products
        resp_page1 = self.client.get(reverse('store:home'))
        self.assertEqual(resp_page1.status_code, 200)
        page1_obj = resp_page1.context['page_obj']
        self.assertEqual(len(page1_obj.object_list), 12)
        self.assertEqual(page1_obj.paginator.per_page, 12)
        self.assertEqual(page1_obj.paginator.num_pages, 2)
        self.assertTrue(page1_obj.has_next())

        # Page 2: remaining 3 products (15 - 12 = 3)
        resp_page2 = self.client.get(reverse('store:home'), {'page': 2})
        self.assertEqual(resp_page2.status_code, 200)
        page2_obj = resp_page2.context['page_obj']
        self.assertEqual(len(page2_obj.object_list), 3)
        self.assertTrue(page2_obj.has_previous())

    def test_product_description_three_related_photos(self):
        from store.models import ProductImage
        # Add 3 gallery images to product
        for idx in range(1, 4):
            ProductImage.objects.create(
                product=self.product,
                image_url=f"https://images.unsplash.com/photo-{idx}",
                alt_text=f"Detail Photo #{idx}",
                display_order=idx
            )

        resp = self.client.get(reverse('store:product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(resp.status_code, 200)
        photos = resp.context['description_photos']
        self.assertEqual(len(photos), 3)
        self.assertContains(resp, "পোশাকের সম্পর্কিত ছবি ও ফিনিশিং (3 Related Photos)")
        self.assertContains(resp, "Detail Photo #1")
        self.assertContains(resp, "Detail Photo #2")
        self.assertContains(resp, "Detail Photo #3")

    def test_reduced_image_aspect_ratio_in_templates(self):
        # Grid partial has aspect-square
        resp = self.client.get(reverse('store:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "aspect-square")

        # Product detail has aspect-square
        detail_resp = self.client.get(reverse('store:product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, "aspect-square")

    def test_filter_shows_results_and_reset_clears(self):
        # 1. Filter by category
        resp_filter = self.client.get(reverse('store:home'), {'category': 'panjabi'}, HTTP_HX_REQUEST='true')
        self.assertEqual(resp_filter.status_code, 200)
        self.assertTrue(resp_filter.context['has_active_filters'])
        self.assertContains(resp_filter, "ব্যাকে যান (ফিল্টার রিসেট)")
        self.assertContains(resp_filter, "Silk Cotton Panjabi")

        # 2. Reset filter via ?reset=1
        resp_reset = self.client.get(reverse('store:home'), {'reset': '1', 'category': 'panjabi'}, HTTP_HX_REQUEST='true')
        self.assertEqual(resp_reset.status_code, 200)
        self.assertFalse(resp_reset.context['has_active_filters'])
        self.assertIsNone(resp_reset.context['selected_category'])

        # 3. Product detail page contains back link to reset filters
        detail_resp = self.client.get(reverse('store:product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, "কালেকশনে ফিরে যান")
        self.assertContains(detail_resp, "weaverel_reset_filters_on_back")


