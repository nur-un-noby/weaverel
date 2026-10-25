from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product


class Command(BaseCommand):
    help = 'Seeds enterprise clothing categories (Panjabi, Shirts, T-Shirts, etc.) with BDT pricing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting enterprise clothing demo seeding...'))

        # 1. Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@weaverel.local', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created superuser: username="admin", password="admin123"'))

        # 2. Categories tailored for Bangladesh / South Asian clothing store
        categories_data = [
            {
                'name': 'Panjabi (পাঞ্জাবি)',
                'slug': 'panjabi',
                'description': 'ঈদ ও উৎসবের জন্য এক্সক্লুসিভ কটন ও সেমি-ফিটেড পাঞ্জাবি কালেকশন।',
                'display_order': 1,
                'image_url': 'https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=400&q=80',
            },
            {
                'name': 'Shirts (শার্ট)',
                'slug': 'shirts',
                'description': 'অফিস ও ক্যাজুয়াল ব্যবহারের জন্য প্রিমিয়াম ১০০% সুতি ও লিনেন শার্ট।',
                'display_order': 2,
                'image_url': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=400&q=80',
            },
            {
                'name': 'T-Shirts (টি-শার্ট)',
                'slug': 't-shirts',
                'description': 'ড্রপ শোল্ডার ওভারসাইজড এবং আরামদায়ক রেগুলার ফিট টি-শার্ট।',
                'display_order': 3,
                'image_url': 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=400&q=80',
            },
            {
                'name': 'Polo Shirts (পোলো শার্ট)',
                'slug': 'polo-shirts',
                'description': 'ক্লাসিক পিকু কটন ফ্যাব্রিক পোলো শার্ট — ফরমাল ও ক্যাজুয়াল দুইভাবেই মানানসই।',
                'display_order': 4,
                'image_url': 'https://images.unsplash.com/photo-1625910513413-7e3e9d8e75e6?auto=format&fit=crop&w=400&q=80',
            },
            {
                'name': 'Pants & Pajama (প্যান্ট ও পায়জামা)',
                'slug': 'pants-pajama',
                'description': 'পাঞ্জাবির সাথে পরার জন্য কটন পায়জামা এবং স্টাইলিশ চিনো ট্রাউজার।',
                'display_order': 5,
                'image_url': 'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=400&q=80',
            },
            {
                'name': 'Winter & Hoodies (শীতের পোশাক)',
                'slug': 'winter-hoodies',
                'description': 'ভারী কটন ফ্লিস হুডি এবং উইন্ডপ্রুফ জ্যাকেট।',
                'display_order': 6,
                'image_url': 'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=400&q=80',
            },
        ]

        # Clear existing demo products to refresh with BDT products
        Product.objects.all().delete()
        Category.objects.all().delete()

        category_objs = {}
        for cat_info in categories_data:
            cat = Category.objects.create(
                name=cat_info['name'],
                slug=cat_info['slug'],
                description=cat_info['description'],
                display_order=cat_info['display_order'],
                image_url=cat_info['image_url'],
                is_active=True
            )
            category_objs[cat.slug] = cat
            self.stdout.write(f'Created Category: {cat.name}')

        # 3. Enterprise Products in BDT (৳)
        products_data = [
            {
                'category': category_objs['panjabi'],
                'name': 'Royal Silk Cotton Semi-Fitted Panjabi',
                'sku': 'WV-PAN-01',
                'description': 'উচ্চমানের সিল্ক-কটন মিক্সড ফেব্রিকে তৈরি আকর্ষণীয় পাঞ্জাবি। আরামদায়ক সেমি-ফিট কাটিং, মেটাল বোতাম এবং নিখুঁত ফিনিশিং। ঈদ বা যেকোনো পারিবারিক অনুষ্ঠানের জন্য সেরা পছন্দ।',
                'fabric_details': 'Cotton Silk Blend / নরম আরামদায়ক সিল্ক সুতি',
                'price': 2450.00,
                'discount_price': 1950.00,
                'image_url': 'https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=800&q=80',
                'available_sizes': '38, 40, 42, 44',
                'color': 'Royal Navy Blue / নেভি ব্লু',
                'badge': 'EID SPECIAL',
                'stock': 45,
                'is_featured': True,
            },
            {
                'category': category_objs['panjabi'],
                'name': 'Festive Embroidered White Kabli Panjabi Set',
                'sku': 'WV-PAN-02',
                'description': '১০০% পিউর প্রিমিয়াম কম্বড কটনে তৈরি কাবলি পাঞ্জাবি সেট (পায়জামা সহ)। কলার ও প্লাকেটে সূক্ষ্ম সূতার নিখুঁত এমব্রয়ডারি কাজ।',
                'fabric_details': '100% Pure Fine Cotton / ১০০% খাঁটি সুতি',
                'price': 2850.00,
                'discount_price': 2350.00,
                'image_url': 'https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=800&q=80',
                'available_sizes': '38, 40, 42, 44, 46',
                'color': 'Pearl White / মুক্তা সাদা',
                'badge': 'BESTSELLER',
                'stock': 35,
                'is_featured': True,
            },
            {
                'category': category_objs['shirts'],
                'name': 'Executive Oxford Solid Casual Shirt',
                'sku': 'WV-SH-01',
                'description': '১০০% দুই-প্লাই তুলা দিয়ে তৈরি প্রিমিয়াম অক্সফোর্ড শার্ট। সফট রোল কলার এবং বক্রাকার হেম। অফিসে বা বন্ধুদের আড্ডায় সারাদিন পরার জন্য অত্যন্ত আরামদায়ক।',
                'fabric_details': 'Two-Ply 100% Oxford Cotton / প্রিমিয়াম সুতি',
                'price': 1650.00,
                'discount_price': 1350.00,
                'image_url': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=800&q=80',
                'available_sizes': 'M, L, XL, XXL',
                'color': 'Sky Blue / আকাশী নীল',
                'badge': 'POPULAR',
                'stock': 60,
                'is_featured': True,
            },
            {
                'category': category_objs['shirts'],
                'name': 'Breathable French Linen Casual Shirt',
                'sku': 'WV-SH-02',
                'description': 'প্রাকৃতিক ইউরোপিয়ান ফ্ল্যাক্স লিনেন ফ্যাব্রিক। গরমের দিনে শরীর ঠাণ্ডা ও ফ্রেশ রাখে। কাঠের বোতাম ও কিউবান কলারের স্টাইলিশ ডিজাইন।',
                'fabric_details': '100% Pure Natural Linen / খাঁটি লিনেন',
                'price': 1850.00,
                'discount_price': 1550.00,
                'image_url': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=80',
                'available_sizes': 'M, L, XL',
                'color': 'Sandstone Cream / বাদামী ক্রীম',
                'badge': 'SUMMER PICK',
                'stock': 30,
                'is_featured': True,
            },
            {
                'category': category_objs['t-shirts'],
                'name': 'Heavyweight Drop-Shoulder Oversized T-Shirt',
                'sku': 'WV-TEE-01',
                'description': '২৪০ জিএসএম ভারী কম্বড সুতির ড্রপ-শোল্ডার টি-শার্ট। কলার ধোয়ার পরেও ঢিলে বা নষ্ট হয় না। প্রি-শ্রাঙ্ক প্রিমিয়াম ফেব্রিক।',
                'fabric_details': '240 GSM Combed Cotton / ভারী নরম কটন',
                'price': 850.00,
                'discount_price': 690.00,
                'image_url': 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80',
                'available_sizes': 'M, L, XL, XXL',
                'color': 'Washed Charcoal / ছাই কালো',
                'badge': 'HOT SALE',
                'stock': 80,
                'is_featured': True,
            },
            {
                'category': category_objs['t-shirts'],
                'name': 'Everyday Solid Soft Cotton T-Shirt',
                'sku': 'WV-TEE-02',
                'description': 'প্রতিদিনের ব্যবহারের জন্য হালকা ও মসৃণ ১০০% সুতি টি-শার্ট। কোনো কৃত্রিম পলিয়েস্টার নেই, ঘাম চুষে নেয় দ্রুত।',
                'fabric_details': '190 GSM 100% Organic Cotton / ১০০% কটন',
                'price': 550.00,
                'discount_price': 450.00,
                'image_url': 'https://images.unsplash.com/photo-1581655353564-df123a1eb820?auto=format&fit=crop&w=800&q=80',
                'available_sizes': 'M, L, XL, XXL',
                'color': 'Olive Green / জলপাই সবুজ',
                'badge': '',
                'stock': 100,
                'is_featured': False,
            },
            {
                'category': category_objs['polo-shirts'],
                'name': 'Classic Pique Knit Honeycomb Polo Shirt',
                'sku': 'WV-POL-01',
                'description': '২২০ জিএসএম হানিকম্ব পিকু কটন পোলো। কলার কার্লিং হবে না, টেকসই এবং চমৎকার কালার ফাস্টনেস।',
                'fabric_details': '220 GSM Honeycomb Cotton / পিকু কটন',
                'price': 1250.00,
                'discount_price': 990.00,
                'image_url': 'https://images.unsplash.com/photo-1625910513413-7e3e9d8e75e6?auto=format&fit=crop&w=800&q=80',
                'available_sizes': 'M, L, XL, XXL',
                'color': 'Deep Maroon / খয়েরি',
                'badge': 'BEST VALUE',
                'stock': 50,
                'is_featured': True,
            },
            {
                'category': category_objs['pants-pajama'],
                'name': 'Premium Cotton Aligari Pajama (For Panjabi)',
                'sku': 'WV-PAJ-01',
                'description': 'পাঞ্জাবির সাথে পরার জন্য খাঁটি আলিগড়ি ডিজাইনের সুতি পায়জামা। ইলাস্টিক কোমর ও ড্রস্ট্রিং সুবিধা।',
                'fabric_details': '100% White Poplin Cotton / সাদা পপলিন সুতি',
                'price': 750.00,
                'discount_price': 590.00,
                'image_url': 'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=800&q=80',
                'available_sizes': '38, 40, 42, 44',
                'color': 'Classic White / সাদা',
                'badge': 'ESSENTIAL',
                'stock': 40,
                'is_featured': False,
            },
        ]

        for p_info in products_data:
            Product.objects.create(**p_info)
            self.stdout.write(f'Created Product: {p_info["name"]} (৳ {int(p_info["price"])})')

        self.stdout.write(self.style.SUCCESS(
            'Seeding completed! All products in BDT (৳) and categories (Panjabi, Shirts, T-Shirts, Polo) are loaded.'
        ))
