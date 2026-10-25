from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from store.models import Category, Size, Color, Product, ProductVariant, ProductImage
from shipping.models import ShippingZone
from promotions.models import Coupon
from store_settings.models import SiteConfiguration, HeroBanner
from reviews.models import ProductReview


class Command(BaseCommand):
    help = 'Seeds enterprise clothing categories, variants, inventory, shipping zones, and store settings.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting enterprise clothing demo seeding...'))

        # 1. Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@weaverel.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created superuser: username="admin", password="admin123"'))

        # 2. Site Configuration
        config = SiteConfiguration.get_solo()
        config.site_name = "Weaverel Apparel"
        config.site_name_bn = "উইভারেল অ্যাপারেল"
        config.tagline = "Premium Clothing for Modern Life"
        config.tagline_bn = "প্রিমিয়াম পাঞ্জাবি, শার্ট ও টি-শার্ট কালেকশন"
        config.announcement_active = True
        config.announcement_text_en = "🚚 Nationwide Cash on Delivery | Free shipping on orders over ৳ 2,500!"
        config.announcement_text_bn = "🚚 সারাদেশে ক্যাশ অন ডেলিভারি | ৳ ২,৫০০+ অর্ডারে ডেলিভারি চার্জ সম্পূর্ণ ফ্রি!"
        config.contact_phone = "01700-000000"
        config.whatsapp_number = "8801334202784"
        config.contact_email = "support@weaverel.com"
        config.free_shipping_threshold = Decimal("2500.00")
        config.save()
        self.stdout.write(self.style.SUCCESS('Site configuration updated.'))

        # 3. Hero Banners
        HeroBanner.objects.all().delete()
        HeroBanner.objects.create(
            title_en="Handcrafted Panjabi & Casual Wear",
            title_bn="খাঁটি কাপড়ে তৈরি প্রিমিয়াম পাঞ্জাবি ও ক্যাজুয়াল কালেকশন",
            subtitle_en="100% Combed Cotton, Linen, and Silk blends for festive and daily comfort.",
            subtitle_bn="১০০% কম্বড সুতি ও লিনেন ফেব্রিকে তৈরি আরামদায়ক পোশাক। নিখুঁত সেলাই ও সারা দেশে দ্রুত ক্যাশ অন ডেলিভারি।",
            badge_en="✨ NEW FESTIVE COLLECTION 2026",
            badge_bn="✨ নতুন ঈদ ও ফেস্টিভ কালেকশন ২০২৬",
            button_text_en="Shop Collection ↓",
            button_text_bn="পণ্যসমূহ দেখুন ↓",
            button_link="#products-grid",
            image_url="https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=2000&q=80",
            display_order=1,
            is_active=True
        )

        # 4. Shipping Zones for Bangladesh
        ShippingZone.objects.all().delete()
        zones_data = [
            {
                'code': 'DHAKA',
                'name_en': 'Inside Dhaka / Dhaka Metro',
                'name_bn': 'ঢাকা মেট্রো',
                'charge': Decimal('70.00'),
                'estimated_delivery_en': '24-48 hours',
                'estimated_delivery_bn': '২৪-৪৮ ঘণ্টা',
                'display_order': 1,
            },
            {
                'code': 'SUBURB',
                'name_en': 'Dhaka Suburbs (Savar, Gazipur, Narayanganj)',
                'name_bn': 'সাভার / গাজীপুর / নারায়ণগঞ্জ',
                'charge': Decimal('100.00'),
                'estimated_delivery_en': '2-3 business days',
                'estimated_delivery_bn': '২-৩ কর্মদিবস',
                'display_order': 2,
            },
            {
                'code': 'OUTSIDE',
                'name_en': 'Outside Dhaka (All Bangladesh)',
                'name_bn': 'সমগ্র বাংলাদেশ (ঢাকার বাইরে)',
                'charge': Decimal('130.00'),
                'estimated_delivery_en': '3-5 business days',
                'estimated_delivery_bn': '৩-৫ কর্মদিবস',
                'display_order': 3,
            },
        ]
        for z in zones_data:
            ShippingZone.objects.create(
                code=z['code'],
                name_en=z['name_en'],
                name_bn=z['name_bn'],
                charge=z['charge'],
                estimated_delivery_en=z['estimated_delivery_en'],
                estimated_delivery_bn=z['estimated_delivery_bn'],
                free_delivery_allowed=True,
                display_order=z['display_order'],
                is_active=True
            )
        self.stdout.write(self.style.SUCCESS('Created 3 Bangladesh shipping zones.'))

        # 5. Coupons
        Coupon.objects.all().delete()
        Coupon.objects.create(
            code="EID2026",
            discount_type=Coupon.DISCOUNT_PERCENTAGE,
            discount_value=Decimal("10.00"),
            min_purchase_amount=Decimal("1500.00"),
            max_discount_amount=Decimal("500.00"),
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=90),
            usage_limit=1000,
            is_active=True
        )
        Coupon.objects.create(
            code="WEAVEREL100",
            discount_type=Coupon.DISCOUNT_FIXED,
            discount_value=Decimal("100.00"),
            min_purchase_amount=Decimal("1000.00"),
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=60),
            usage_limit=500,
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS('Created promotion coupons (EID2026, WEAVEREL100).'))

        # 6. Sizes
        Size.objects.all().delete()
        sizes_dict = {}
        size_names = ['38', '40', '42', '44', '46', 'S', 'M', 'L', 'XL', 'XXL']
        for idx, s_name in enumerate(size_names, start=1):
            sizes_dict[s_name] = Size.objects.create(name=s_name, display_order=idx)

        # 7. Colors
        Color.objects.all().delete()
        colors_data = [
            {'name': 'Royal Navy', 'name_bn': 'রয়্যাল নেভি ব্লু', 'hex_code': '#1e3a8a'},
            {'name': 'Pearl White', 'name_bn': 'মুক্তা সাদা', 'hex_code': '#f8fafc'},
            {'name': 'Jet Black', 'name_bn': 'জেট ব্ল্যাক', 'hex_code': '#0f172a'},
            {'name': 'Forest Green', 'name_bn': 'গাঢ় সবুজ', 'hex_code': '#14532d'},
            {'name': 'Maroon', 'name_bn': 'মেরুন', 'hex_code': '#7f1d1d'},
            {'name': 'Sky Blue', 'name_bn': 'আকাশী নীল', 'hex_code': '#38bdf8'},
            {'name': 'Charcoal Grey', 'name_bn': 'চারকোল ধূসর', 'hex_code': '#374151'},
            {'name': 'Beige / Khaki', 'name_bn': 'বেজ / খাকি', 'hex_code': '#d4b996'},
        ]
        colors_dict = {}
        for c in colors_data:
            colors_dict[c['name']] = Color.objects.create(
                name=c['name'],
                name_bn=c['name_bn'],
                hex_code=c['hex_code']
            )

        # 8. Categories (including traditional Muslim clothing, Jubba, Thobe, Panjabi, Pajama, Shirts, T-shirts, Pants)
        Product.objects.all().delete()
        Category.objects.all().delete()

        categories_data = [
            {
                'slug': 'panjabi',
                'name': 'Panjabi',
                'name_bn': 'পাঞ্জাবি',
                'description': 'Exclusive cotton, silk, and semi-fitted Panjabi collection for Eid, weddings, and casual wear.',
                'description_bn': 'ঈদ, বিয়ে ও উৎসবের জন্য এক্সক্লুসিভ কটন, সিল্ক ও সেমি-ফিটেড পাঞ্জাবি কালেকশন।',
                'display_order': 1,
                'image_url': 'https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=600&q=80',
            },
            {
                'slug': 'jubba-thobe',
                'name': 'Jubba & Thobe',
                'name_bn': 'জুব্বা ও থোব',
                'description': 'Traditional modest Islamic clothing, Moroccan and Omani cut Jubba with elegant embroidery.',
                'description_bn': 'ঐতিহ্যবাহী মুসলিম পোশাক — ওমানি ও মরোক্কান কাটিং প্রিমিয়াম জুব্বা ও মার্জিত ডিজাইনের থোব।',
                'display_order': 2,
                'image_url': 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=600&q=80',
            },
            {
                'slug': 'pajama',
                'name': 'Pajama',
                'name_bn': 'পায়জামা',
                'description': 'Comfortable cotton Aligari, Churidar, and regular-fit Pajamas paired with Panjabi.',
                'description_bn': 'পাঞ্জাবির সাথে পরার উপযোগী আরামদায়ক খাঁটি সুতি আলিগড়ী, চুড়িদার ও রেগুলার পায়জামা।',
                'display_order': 3,
                'image_url': 'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=600&q=80',
            },
            {
                'slug': 'shirts',
                'name': 'Shirts',
                'name_bn': 'শার্ট',
                'description': 'Formal and casual 100% cotton & linen shirts tailored for Bangladeshi climate.',
                'description_bn': 'অফিস ও ক্যাজুয়াল ব্যবহারের জন্য প্রিমিয়াম ১০০% সুতি ও লিনেন ফেব্রিকের আরামদায়ক শার্ট।',
                'display_order': 4,
                'image_url': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=600&q=80',
            },
            {
                'slug': 't-shirts',
                'name': 'T-Shirts',
                'name_bn': 'টি-শার্ট',
                'description': 'High GSM combed cotton oversized drop-shoulder and classic regular crew-neck t-shirts.',
                'description_bn': 'উচ্চ জিএসএম কম্বড কটন ওভারসাইজড ড্রপ-শোল্ডার এবং ক্লাসিক রেগুলার ফিট টি-শার্ট।',
                'display_order': 5,
                'image_url': 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80',
            },
            {
                'slug': 'pants-trousers',
                'name': 'Pants & Trousers',
                'name_bn': 'প্যান্ট ও ট্রাউজার',
                'description': 'Smart stretch chinos, formal trousers, and everyday comfort cargo pants.',
                'description_bn': 'স্মার্ট স্ট্রেচ চিনো প্যান্ট, ফরমাল ট্রাউজার ও আরামদায়ক ক্যাজুয়াল প্যান্ট।',
                'display_order': 6,
                'image_url': 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=600&q=80',
            },
            {
                'slug': 'polo-shirts',
                'name': 'Polo Shirts',
                'name_bn': 'পোলো শার্ট',
                'description': 'Pique cotton fabric polo shirts with durable collars and contrast trims.',
                'description_bn': 'ক্লাসিক পিকু কটন ফেব্রিক পোলো শার্ট — ফরমাল ও ক্যাজুয়াল দুইভাবেই নিখুঁত।',
                'display_order': 7,
                'image_url': 'https://images.unsplash.com/photo-1625910513413-7e3e9d8e75e6?auto=format&fit=crop&w=600&q=80',
            },
        ]

        cat_objs = {}
        for cdata in categories_data:
            cat = Category.objects.create(
                slug=cdata['slug'],
                name=cdata['name'],
                name_bn=cdata['name_bn'],
                description=cdata['description'],
                description_bn=cdata['description_bn'],
                display_order=cdata['display_order'],
                image_url=cdata['image_url'],
                is_active=True
            )
            cat_objs[cat.slug] = cat
            self.stdout.write(f"Created category: {cat.name}")

        # 9. Realistic Products with Variants
        products_info = [
            {
                'category': cat_objs['panjabi'],
                'name': 'Royal Silk Cotton Semi-Fitted Panjabi',
                'name_bn': 'রয়্যাল সিল্ক কটন সেমি-ফিটেড পাঞ্জাবি',
                'sku': 'WV-PAN-01',
                'description': 'Crafted from premium silk-cotton blend fabric with fine contrast embroidery on collar and placket. Elegant metallic snap buttons and tailored fit make it the premier choice for Eid and formal events.',
                'description_bn': 'উচ্চমানের সিল্ক-কটন ব্লেন্ড ফেব্রিকে তৈরি আকর্ষণীয় পাঞ্জাবি। কলার ও প্ল্যাকেটে নিখুঁত কন্ট্রাস্ট সূচিকর্ম, প্রিমিয়াম মেটাল স্ন্যাপ বোতাম এবং আকর্ষণীয় সেমি-ফিট কাটিং। ঈদ ও যেকোনো অনুষ্ঠানের জন্য সেরা পছন্দ।',
                'fabric_details': 'Silk Cotton Blend / প্রিমিয়াম সিল্ক সুতি',
                'fabric_details_bn': 'সিল্ক কটন ব্লেন্ড (৬৫% খাঁটি সুতি, ৩৫% সিল্ক)',
                'price': Decimal('2450.00'),
                'discount_price': Decimal('1950.00'),
                'image_url': 'https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=800&q=80',
                'badge': 'EID SPECIAL',
                'is_featured': True,
                'is_new_arrival': True,
                'sizes': ['38', '40', '42', '44'],
                'colors': ['Royal Navy', 'Pearl White', 'Maroon'],
                'gallery': [
                    'https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=800&q=80',
                    'https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?auto=format&fit=crop&w=800&q=80'
                ]
            },
            {
                'category': cat_objs['panjabi'],
                'name': 'Festive Embroidered White Kabli Panjabi',
                'name_bn': 'ফেস্টিভ এমব্রয়ডারি করা সাদা কাবলি পাঞ্জাবি',
                'sku': 'WV-PAN-02',
                'description': 'Classic white Kabli Panjabi made from breathable organic cotton. Features subtle tonal embroidery on the chest and structured Mandarin collar.',
                'description_bn': '১০০% অরগানিক খাঁটি সুতি কাপড়ে তৈরি প্রিমিয়াম হোয়াইট কাবলি পাঞ্জাবি। বুকে মার্জিত ম্যাচিং সুতোর কাজ, আরামদায়ক লুজ ফিটিং যা সারাদিন পরার উপযোগী।',
                'fabric_details': '100% Breathable Organic Cotton',
                'fabric_details_bn': '১০০% অরগানিক বাতাস চলাচল উপযোগী সুতি',
                'price': Decimal('2250.00'),
                'discount_price': Decimal('1850.00'),
                'image_url': 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=800&q=80',
                'badge': 'BESTSELLER',
                'is_featured': True,
                'is_new_arrival': True,
                'sizes': ['38', '40', '42', '44', '46'],
                'colors': ['Pearl White', 'Beige / Khaki'],
                'gallery': [
                    'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=800&q=80',
                ]
            },
            {
                'category': cat_objs['jubba-thobe'],
                'name': 'Emirati Cut Classic Black Jubba Thobe',
                'name_bn': 'আমিরাতি কাটিং ক্লাসিক ব্ল্যাক জুব্বা থোব',
                'sku': 'WV-JUB-01',
                'description': 'Graceful Gulf-style Thobe with soft tassel (tarboosh) and concealed zipper. Premium wrinkle-resistant matte fabric with comfortable drape.',
                'description_bn': 'উপসাগরীয় ঐতিহ্যবাহী আমিরাতি স্টাইল জুব্বা থোব। নিখুঁত টারবুশ (ঝালর), গোপন জিপার ও রিঙ্কল-ফ্রি ম্যাট ফেব্রিক। জুমুআ ও দৈনন্দিন ইবাদতের জন্য অত্যন্ত আরামদায়ক।',
                'fabric_details': 'Polyester Viscose Blend / রিঙ্কল-ফ্রি ম্যাট ফেব্রিক',
                'fabric_details_bn': 'আমদানি করা মসৃণ পলিয়েস্টার ভিসকোস ব্লেন্ড',
                'price': Decimal('2850.00'),
                'discount_price': Decimal('2450.00'),
                'image_url': 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=800&q=80',
                'badge': 'MODEST WEAR',
                'is_featured': True,
                'is_new_arrival': True,
                'sizes': ['M', 'L', 'XL', 'XXL'],
                'colors': ['Jet Black', 'Pearl White', 'Charcoal Grey'],
                'gallery': [
                    'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=800&q=80'
                ]
            },
            {
                'category': cat_objs['pajama'],
                'name': 'Premium Combed Cotton Aligari Pajama',
                'name_bn': 'প্রিমিয়াম কম্বড কটন আলিগড়ী পায়জামা',
                'sku': 'WV-PAJ-01',
                'description': 'Soft 100% combed cotton Aligari pajama with elastic waistband, drawstring, and deep side pocket. Tailored to accompany both short and long Panjabis.',
                'description_bn': '১০০% নরম সুতি আলিগড়ী কাটিং পায়জামা। ড্রস্ট্রিং ও ইলাস্টিক কোমরবন্ধ, প্রশস্ত সাইড পকেট। পাঞ্জাবির নিচে পরার জন্য অত্যন্ত উপযোগী।',
                'fabric_details': '100% Fine Combed Cotton',
                'fabric_details_bn': '১০০% খাঁটি কম্বড কটন',
                'price': Decimal('750.00'),
                'discount_price': Decimal('590.00'),
                'image_url': 'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=800&q=80',
                'badge': 'ESSENTIAL',
                'is_featured': False,
                'is_new_arrival': False,
                'sizes': ['38', '40', '42', '44'],
                'colors': ['Pearl White', 'Beige / Khaki', 'Jet Black'],
                'gallery': [
                    'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=800&q=80'
                ]
            },
            {
                'category': cat_objs['shirts'],
                'name': 'Oxford Cotton Sky Blue Formal Shirt',
                'name_bn': 'অক্সফোর্ড কটন স্কাই ব্লু ফরমাল শার্ট',
                'sku': 'WV-SH-01',
                'description': 'Crisp Oxford weave 100% cotton shirt designed for professional corporate wear and smart casual evenings.',
                'description_bn': '১০০% খাঁটি অক্সফোর্ড উইভ সুতি কাপড়ে তৈরি প্রিমিয়াম শার্ট। অফিস ও ফর্মাল মিটিংয়ের জন্য স্মার্ট ও আরামদায়ক।',
                'fabric_details': '100% Oxford Cotton',
                'fabric_details_bn': '১০০% অক্সফোর্ড উইভ কটন',
                'price': Decimal('1650.00'),
                'discount_price': Decimal('1350.00'),
                'image_url': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=800&q=80',
                'badge': 'CORPORATE',
                'is_featured': True,
                'is_new_arrival': True,
                'sizes': ['M', 'L', 'XL', 'XXL'],
                'colors': ['Sky Blue', 'Pearl White'],
                'gallery': [
                    'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=800&q=80'
                ]
            },
            {
                'category': cat_objs['t-shirts'],
                'name': 'Heavyweight 220 GSM Drop Shoulder T-Shirt',
                'name_bn': 'হেভিওয়েট ২২০ জিএসএম ড্রপ শোল্ডার টি-শার্ট',
                'sku': 'WV-TSH-01',
                'description': 'Trendy 220 GSM heavyweight combed cotton oversized t-shirt. Compact bio-washed fabric with zero shrinkage.',
                'description_bn': '২২০ জিএসএম প্রিমিয়াম বায়ো-ওয়াশড কম্বড কটন ওভারসাইজড টি-শার্ট। রং পাকা ও টেকসই ফেব্রিক।',
                'fabric_details': '220 GSM 100% Compact Combed Cotton',
                'fabric_details_bn': '২২০ জিএসএম বায়ো-ওয়াশড খাঁটি সুতি',
                'price': Decimal('890.00'),
                'discount_price': Decimal('690.00'),
                'image_url': 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80',
                'badge': 'TRENDING',
                'is_featured': True,
                'is_new_arrival': True,
                'sizes': ['M', 'L', 'XL'],
                'colors': ['Jet Black', 'Forest Green', 'Charcoal Grey'],
                'gallery': [
                    'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80'
                ]
            },
            {
                'category': cat_objs['pants-trousers'],
                'name': 'Stretch Cotton Slim-Fit Chino Pants',
                'name_bn': 'স্ট্রেচ কটন স্লিম-ফিট চিনো প্যান্ট',
                'sku': 'WV-PNT-01',
                'description': '98% Cotton with 2% Elastane for superior ease of movement. YKK zipper, reinforced seams, and timeless finish.',
                'description_bn': '৯৮% কটন ও ২% এলাস্টেনযুক্ত অত্যন্ত আরামদায়ক স্ট্রেচ চিনো প্যান্ট। অফিস ও ক্যাজুয়াল উভয় পরিবেশেই মানানসই।',
                'fabric_details': '98% Cotton, 2% Spandex',
                'fabric_details_bn': '৯৮% সুতি, ২% স্ট্রেচ স্প্যানডেক্স',
                'price': Decimal('1850.00'),
                'discount_price': Decimal('1490.00'),
                'image_url': 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=800&q=80',
                'badge': 'HOT SALE',
                'is_featured': True,
                'is_new_arrival': False,
                'sizes': ['38', '40', '42', '44'],
                'colors': ['Beige / Khaki', 'Jet Black', 'Royal Navy'],
                'gallery': [
                    'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=800&q=80'
                ]
            },
            {
                'category': cat_objs['polo-shirts'],
                'name': 'Signature Pique Cotton Polo Shirt',
                'name_bn': 'সিগনেচার পিকু কটন পোলো শার্ট',
                'sku': 'WV-POL-01',
                'description': 'Double pique knit cotton with ribbed collar and cuffs. Tailored hem with side vents for athletic comfort.',
                'description_bn': 'ডাবল পিকু নিট খাঁটি সুতি পোলো শার্ট। টেকসই কলার ও কাফ, সাইড ভেন্টসহ আকর্ষণীয় ফিটিং।',
                'fabric_details': '100% Pique Knit Cotton',
                'fabric_details_bn': '১০০% ডাবল পিকু সুতি',
                'price': Decimal('1250.00'),
                'discount_price': Decimal('990.00'),
                'image_url': 'https://images.unsplash.com/photo-1625910513413-7e3e9d8e75e6?auto=format&fit=crop&w=800&q=80',
                'badge': 'NEW',
                'is_featured': True,
                'is_new_arrival': True,
                'sizes': ['M', 'L', 'XL', 'XXL'],
                'colors': ['Royal Navy', 'Maroon', 'Forest Green'],
                'gallery': [
                    'https://images.unsplash.com/photo-1625910513413-7e3e9d8e75e6?auto=format&fit=crop&w=800&q=80'
                ]
            },
        ]

        for pinfo in products_info:
            product = Product.objects.create(
                category=pinfo['category'],
                name=pinfo['name'],
                name_bn=pinfo['name_bn'],
                sku=pinfo['sku'],
                description=pinfo['description'],
                description_bn=pinfo['description_bn'],
                fabric_details=pinfo['fabric_details'],
                fabric_details_bn=pinfo['fabric_details_bn'],
                price=pinfo['price'],
                discount_price=pinfo['discount_price'],
                image_url=pinfo['image_url'],
                badge=pinfo['badge'],
                is_featured=pinfo['is_featured'],
                is_new_arrival=pinfo['is_new_arrival'],
                is_available=True,
                stock=50,
            )

            # Create Product Variants (Combinations of size & color)
            for s_name in pinfo['sizes']:
                size_obj = sizes_dict.get(s_name)
                for c_name in pinfo['colors']:
                    color_obj = colors_dict.get(c_name)
                    if size_obj and color_obj:
                        ProductVariant.objects.create(
                            product=product,
                            size=size_obj,
                            color=color_obj,
                            sku=f"{product.sku}-{size_obj.name}-{color_obj.name[:3].upper()}",
                            stock=15,
                            is_active=True
                        )

            # Create Gallery Images
            for idx, img_url in enumerate(pinfo['gallery'], start=1):
                ProductImage.objects.create(
                    product=product,
                    image_url=img_url,
                    alt_text=f"{product.name} view {idx}",
                    display_order=idx
                )

            # Create a sample customer review
            ProductReview.objects.create(
                product=product,
                customer_name="রাফি আহমেদ (Dhaka)",
                rating=5,
                title="চমৎকার কাপড় ও নিখুঁত ফিটিং",
                comment="কাপড় অত্যন্ত প্রিমিয়াম এবং আরামদায়ক। ছবির সাথে শতভাগ মিল রয়েছে এবং অর্ডার করার পরদিনই ডেলিভারি পেয়েছি। ধন্যবাদ উইভারেল!",
                is_verified_buyer=True,
                is_approved=True
            )

            self.stdout.write(f"Created product with variants: {product.name}")

        self.stdout.write(self.style.SUCCESS('Successfully seeded complete enterprise clothing data!'))
