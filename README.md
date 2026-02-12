# Mini E-Commerce Backend (Django + DRF)
A robust backend for a mini e-commerce platform.

## Features
- JWT/Token based Authentication.
- Product Management with Stock Validation.
- Coupon System (Percentage/Flat, Expiry, Min Value).
- Order Management with Guest Checkout.
- Custom Admin Dashboard using Jinja Templates.

## Tech Stack
- Python, Django, Django Rest Framework.
- PostgreSQL (Configured) / SQLite.
- Gunicorn & Nginx (Config Files Included).
- Hosted on: PythonAnywhere.

## API Documentation
- `GET /api/products/` - List all products.
- `POST /api/login/` - User Login.
- `POST /api/register/` - User Registration.
- `POST /api/place-order/` - Place order (Guest/Auth).
- `GET /api/dashboard/` - Admin Dashboard.
