# 🧵 Weaverel — Production Clothing E-Commerce Platform (Bangladesh Market)

An enterprise-ready, production-grade clothing e-commerce platform built specifically for the Bangladesh market using **Django**, **Tailwind CSS**, **Vanilla JavaScript**, **HTMX**, and **PostgreSQL/SQLite**.

The system features real BDT (৳) pricing, 100% Cash on Delivery (COD) nationwide, bilingual localization (বাংলা / English), server-side inventory locking (`select_for_update`) to prevent overselling, variant management (sizes & colors), promotional coupon engine, customer account management, wishlist, and executive admin reporting.

---

## 🚀 Key Features

1. **Bilingual Localization (Bangla & English):**
   - Seamless language switcher in the header and footer (`bn` ⇋ `en`).
   - Dynamic product fields in Bangla & English (`name_bn`, `description_bn`, `fabric_details_bn`).
   - Form validation messages and localized dates/numbers.

2. **Tailored for Bangladesh Market (BDT ৳):**
   - Authentic clothing categories: **Panjabi (পাঞ্জাবি)**, **Jubba & Thobe (জুব্বা ও থোব)**, **Pajama (পায়জামা)**, **Shirts (শার্ট)**, **T-Shirts (টি-শার্ট)**, **Pants & Trousers (প্যান্ট)**, and **Polo Shirts (পোলো)**.
   - Standard Bangladesh mobile number validation (e.g. `017XXXXXXXX`, `018...`, `019...` with automatic `+880` prefix normalization).
   - Configurable delivery zones:
     - **Inside Dhaka (ঢাকা মেট্রো):** ৳ 70 (24–48 hours)
     - **Dhaka Suburbs (সাভার / গাজীপুর / নারায়ণগঞ্জ):** ৳ 100 (2–3 days)
     - **Outside Dhaka (সমগ্র বাংলাদেশ):** ৳ 130 (3–5 days)
     - **Free Delivery:** On all orders reaching the configurable threshold (default: ৳ 2,500).

3. **Product Catalog & Variant Management:**
   - Multi-variant combinations: Size (`38`, `40`, `42`, `44`, `46`, `S`, `M`, `L`, `XL`, `XXL`) and Color (Royal Navy, Pearl White, Jet Black, Forest Green, Maroon, Sky Blue, Charcoal Grey).
   - Dedicated SKU per variant, price override support, and real-time variant stock checking via HTMX endpoint (`/variant-info/<id>/`).
   - Multi-photo product gallery with interactive thumbnails and zoom preview.
   - Size Guide modal with Bangladesh body measurement charts.

4. **Shopping Cart & Authentication-Gated Checkout:**
   - **Shopping Cart System:** Persistent guest carts and authenticated customer carts.
   - **Mandatory Account to Order:** Prevents spam and ensures order accountability; guests must sign in to complete checkout.
   - **Automatic 1-Click Google / Gmail Login:** Instant Google OAuth 2.0 / Gmail sign-in option on checkout and cart drawer that transfers all shopping cart items and forwards directly to order placement.
   - **Automatic Cart Merge:** Seamlessly transfers guest session items into the customer account upon login.
   - **Slide-over Cart Drawer:** Instant interactive cart drawer powered by HTMX partials without full page reloads.
   - **Concurrency Safety:** Uses database transactions (`transaction.atomic()`) and row locking (`select_for_update()`) to guarantee zero overselling even during flash sales.
   - **Authoritative Calculations:** Server recalculates all subtotal, discount, shipping, and total amounts; browser submissions are never trusted.

5. **Payment Method & Delivery Fulfillment:**
   - **Cash on Delivery (COD) Nationwide:** The platform operates exclusively on trusted Cash on Delivery for all 64 districts in Bangladesh.
   - **Customer Protection:** Customers inspect fabric and sizing upon delivery before paying the courier representative.
   - **Instant Order Confirmation:** Orders are immediately confirmed and queued for packing without third-party gateway friction, redirects, or gateway processing fee overhead.
   - **Printable Tax Invoices:** Instant generation of professional print invoices with order number, itemized snapshot prices, shipping breakdown, and delivery address.

6. **Order Lifecycle & Audit Tracking:**
   - Strict state transitions: `PENDING` → `CONFIRMED` → `PROCESSING` → `PACKED` → `SHIPPED` → `DELIVERED` (or `CANCELLED`).
   - Every status transition is timestamped and recorded in `OrderStatusHistory` for full auditability.
   - Customer self-cancellation allowed only while in `PENDING` state (restores inventory automatically).
   - Live parcel tracking by Order Number or Phone Number (`/track-order/`).
   - Official printable invoice slip (`@media print` clean layout).

7. **Promotions & Coupons:**
   - Percentage (e.g. `10%`) and Fixed (e.g. `৳ 100`) discounts.
   - Minimum purchase threshold enforcement and maximum discount caps.
   - Global usage limits and per-customer usage restrictions.
   - Instant live coupon application via HTMX (`/cart/apply-coupon/`).
   - Demo coupons included: `EID2026` (10% off, min ৳ 1,500) and `WEAVEREL100` (৳ 100 off, min ৳ 1,000).

8. **Customer Accounts & Wishlist:**
   - User registration, login, logout, and profile management.
   - Address book: save multiple delivery addresses with default selection.
   - Order history with item breakdown and invoice viewing.
   - Wishlist system with HTMX heart icon toggle for both guest sessions and logged-in customers.

9. **Customer Reviews & Ratings:**
   - 1 to 5 star ratings with verified buyer badges.
   - Duplicate review prevention for authenticated users.
   - Admin moderation controls.

10. **Executive Admin Dashboard (`/admin/analytics/`):**
    - Gross orders and delivered orders count.
    - Paid revenue vs. pending COD revenue awaiting collection from couriers.
    - Low-stock inventory alert table (variants with stock ≤ 10).
    - Top selling products breakdown.
    - Promotional coupon usage metrics.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.13, Django 6.1.2 |
| **Database** | PostgreSQL (Production) / SQLite (Local development) |
| **Frontend** | Semantic HTML5, Tailwind CSS, Vanilla JS, HTMX |
| **Imaging** | Pillow 12.3.0 |
| **HTTP Client** | Requests 2.34.2 |
| **Environment** | python-dotenv |
| **Deployment** | Gunicorn, Nginx, Systemd |

---

## ⚙️ Quick Start (Local Development)

### 1. Clone & Enter Directory
```bash
cd /home/nurun-noby/Desktop/weaverel
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` settings will run SQLite out of the box.

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Seed Demo Clothing Products & Settings
```bash
python manage.py seed_demo_data
```
This sets up:
- Superuser credentials: `username="admin"`, `password="admin123"`
- 7 Categories: Panjabi, Jubba & Thobe, Pajama, Shirts, T-Shirts, Pants, Polo Shirts
- Realistic products in BDT with sizes, colors, and stock variants
- Shipping zones and active coupons (`EID2026`, `WEAVEREL100`)

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit:
- **Storefront:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Executive Analytics:** [http://127.0.0.1:8000/admin/analytics/](http://127.0.0.1:8000/admin/analytics/)
- **Health Check:** [http://127.0.0.1:8000/health/](http://127.0.0.1:8000/health/)

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
python manage.py test
```

### Test Coverage Highlights
- `accounts.tests`: BD phone validation (`017...`, `+880...`), user registration signals, address book default flag.
- `store.tests`: Categories, products, variant unique constraints, bilingual search (Bangla/English), filters, variant stock JSON endpoint, health check, robots.txt, sitemap.xml.
- `cart.tests`: Add to cart with variant, stock limit validation, server-side subtotal recalculation, guest cart merging upon login, order creation and stock deduction.
- `cart.tests_concurrency_and_journey`: Complete user journey (browse → detail → cart → coupon → checkout → inventory decrement → live tracking) + concurrency safety test ensuring zero overselling when stock is limited.
- `promotions.tests`: Percentage and fixed coupon discounts, minimum spend thresholds, max discount caps, per-customer usage limits.
- `shipping.tests`: Zone-based shipping calculations, free shipping threshold qualification.
- `orders.tests`: State machine transitions, audit history logging in `OrderStatusHistory`, illegal status transition rejection.

---

## 🌐 Production Deployment Guide

### 1. PostgreSQL Database Setup
In PostgreSQL:
```sql
CREATE DATABASE weaverel_db;
CREATE USER weaverel_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE weaverel_db TO weaverel_user;
```

Update your `.env` file:
```env
DEBUG=False
SECRET_KEY=generate-a-strong-random-50-char-secret-key
ALLOWED_HOSTS=weaverel.com,www.weaverel.com,your-server-ip

DB_ENGINE=postgresql
DB_NAME=weaverel_db
DB_USER=weaverel_user
DB_PASSWORD=your_strong_password
DB_HOST=127.0.0.1
DB_PORT=5432

SECURE_SSL_REDIRECT=True
```

### 2. Collect Static Files & Compile Translations
```bash
python manage.py collectstatic --noinput
python manage.py compilemessages
python manage.py migrate
```

### 3. Gunicorn Systemd Service
Create `/etc/systemd/system/weaverel.service`:
```ini
[Unit]
Description=Weaverel Gunicorn Daemon
After=network.target

[Service]
User=nurun-noby
Group=www-data
WorkingDirectory=/home/nurun-noby/Desktop/weaverel
ExecStart=/home/nurun-noby/Desktop/weaverel/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/nurun-noby/Desktop/weaverel/weaverel.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl start weaverel
sudo systemctl enable weaverel
```

### 4. Nginx Reverse Proxy Configuration
Create `/etc/nginx/sites-available/weaverel`:
```nginx
server {
    listen 80;
    server_name weaverel.com www.weaverel.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/nurun-noby/Desktop/weaverel/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /home/nurun-noby/Desktop/weaverel/media/;
        expires 30d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/nurun-noby/Desktop/weaverel/weaverel.sock;
    }
}
```
Enable site and obtain SSL via Let's Encrypt:
```bash
sudo ln -s /etc/nginx/sites-available/weaverel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d weaverel.com -d www.weaverel.com
```

### 5. Automated Database Backups
Schedule daily backups via cron:
```bash
crontab -e
# Daily backup at 2:00 AM
0 2 * * * pg_dump -U weaverel_user -d weaverel_db | gzip > /backups/weaverel_$(date +\%F).sql.gz
```

---

## 🔒 Security Best Practices Implemented
- **Server-Side Validation:** All prices, discounts, stock quantities, and permissions are enforced on the server.
- **Race Condition Protection:** Critical stock deductions use database transactions and row-level locks (`select_for_update()`).
- **Payment Idempotency:** Callback handlers verify status with the gateway server API and ensure transactions are never double-credited.
- **CSRF & XSS Protection:** CSRF tokens required on all mutating requests (including HTMX headers); HTML content auto-escaped.
- **User Data Isolation:** Orders, addresses, and profiles are scoped strictly to the authenticated user.
- **Production Headers:** HSTS, X-Content-Type-Options, X-Frame-Options (`DENY`), and Secure/HttpOnly session cookies enabled in production.
