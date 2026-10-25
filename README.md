# 🧵 Weaverel — Enterprise Clothing Business Platform (BDT ৳)

An enterprise-ready e-commerce clothing business platform built with Django, tailored for the mass market with real BDT (৳) pricing, Cash on Delivery (COD), dynamic admin category management (Panjabi, Shirts, T-Shirts, Polo, etc.), and complete order processing.

---

## ⚡ 1. How to Run the Website

Open your terminal in `/home/nurun-noby/Desktop/weaverel` and run:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run the development server
python manage.py runserver
```

Then visit:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 👑 2. Enterprise Admin Access (Add/Change Categories & Clothes)

The categories (Panjabi, Shirts, T-Shirts, etc.) and all products are **100% dynamic**. When an admin adds, edits, or reorders a category, it updates instantly across the website's navbar, mobile menu, and filter pills.

- **Admin Login:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Username:** `admin`
- **Password:** `admin123`

### What You Can Do in Admin:
1. **Manage Categories:** Go to **Store → Categories**. You can rename existing categories, add new ones (e.g. *Kabli Set*, *Formal Shirts*, *Polo*), change their display order, or hide them.
2. **Manage Clothing Products:** Go to **Store → Products**. Update prices in BDT (৳), offer discounts, edit available sizes (38, 40, 42, 44, M, L, XL), track stock quantities, and assign SKUs.
3. **Manage Customer Orders:** Go to **Orders → Orders**. View customer names, mobile numbers, delivery addresses, purchased items, and change order status (*Pending* → *Confirmed* → *Shipped* → *Delivered*).

---

## 🇧🇩 3. Business Features for Bangladesh Market

- **All Pricing in BDT (৳):** Realistic clothing prices (e.g., Panjabi ৳ 1,950, Shirts ৳ 1,350, T-Shirts ৳ 690).
- **Cash on Delivery (ক্যাশ অন ডেলিভারি):** Full checkout flow where customers pay after receiving their package.
- **3 Delivery Zones:**
  - Inside Dhaka (ঢাকা মেট্রো): ৳ 70
  - Dhaka Suburbs (সাভার / গাজীপুর / নারায়ণগঞ্জ): ৳ 100
  - Outside Dhaka (সমগ্র বাংলাদেশ): ৳ 130
  - **Free Delivery:** On all orders over ৳ 2,500.
- **Simple, Mass-Market Friendly Language:** Clear terms, bilingual Bengali/English guidance, and straightforward single-page checkout without confusing jargon.

---

## 🔄 4. Resetting Demo Clothing Items

To reset or reload all categories and clothing products in BDT:

```bash
python manage.py seed_demo_data
```
