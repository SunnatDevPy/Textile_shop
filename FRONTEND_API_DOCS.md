# Frontend API Documentation

**Base URL:** `http://your-domain.com/api`  
**Authentication:** Basic Auth (username + password)  
**Date:** 2026-05-06

---

## Table of Contents

1. [Authentication](#authentication)
2. [Products](#products)
3. [Categories](#categories)
4. [Collections](#collections)
5. [Colors](#colors)
6. [Sizes](#sizes)
7. [Orders](#orders)
8. [Admin Users](#admin-users)
9. [Payments](#payments)
10. [Dashboard](#dashboard)
11. [Stock Movements](#stock-movements)
12. [Alerts](#alerts)
13. [System](#system)

---

## Authentication

All admin endpoints require **Basic Authentication**.

### Headers
```javascript
const headers = {
  'Authorization': 'Basic ' + btoa('username:password'),
  'Content-Type': 'application/json' // or 'multipart/form-data' for file uploads
};
```

### Axios Example
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://your-domain.com/api',
  auth: {
    username: 'SunnatDevPy',
    password: 'admin123'
  }
});
```

### User Roles
- **ADMIN** (Super Admin): Full access, can create operators
- **OPERATOR**: Can manage orders, view products

---

## Products

### GET `/api/products`
Get all products (public)

**Query Parameters:**
- `include_inactive` (bool, default: false) - Include inactive products
- `limit` (int, default: 100, max: 500) - Number of products

**Response:**
```json
[
  {
    "id": 1,
    "name_uz": "Ko'ylak",
    "name_ru": "Рубашка",
    "name_eng": "Shirt",
    "price": 150000,
    "description_uz": "Tavsif",
    "description_ru": "Описание",
    "description_eng": "Description",
    "category_id": 1,
    "collection_id": 2,
    "clothing_type": "erkak",
    "is_active": true,
    "created_at": "2026-05-06T10:00:00"
  }
]
```

### GET `/api/products/search`
Search products (public)

**Query Parameters:**
- `search` (string) - Search in name (uz/ru/eng)
- `category_id` (int) - Filter by category
- `include_inactive` (bool, default: false)
- `limit` (int, default: 100, max: 500)

**Response:**
```json
{
  "ok": true,
  "data": [...],
  "meta": {
    "count": 10
  }
}
```

### GET `/api/products/search/advanced`
Advanced product search (public)

**Query Parameters:**
- `search` (string) - Product name
- `category_id` (int)
- `collection_id` (int)
- `is_active` (bool)
- `min_price` (int)
- `max_price` (int)
- `clothing_type` (string) - "erkak", "ayol", "unisex"
- `color_id` (int)
- `size_id` (int)
- `in_stock` (bool)
- `sort_by` (string, default: "id") - "id", "name_uz", "price", "is_active", "clothing_type"
- `sort_dir` (string, default: "desc") - "asc", "desc"
- `limit` (int, default: 100, max: 500)

### GET `/api/products/{product_id}`
Get single product (public)

**Response:**
```json
{
  "id": 1,
  "name_uz": "Ko'ylak",
  "price": 150000,
  "category": {
    "id": 1,
    "name_uz": "Erkaklar kiyimi"
  },
  "photos": [
    {
      "id": 1,
      "photo_url": "/media/products/photo.jpg"
    }
  ],
  "items": [
    {
      "id": 1,
      "color_id": 1,
      "size_id": 2,
      "total_count": 50
    }
  ]
}
```

### POST `/api/products`
Create product (admin only)

**Auth Required:** Yes

**Form Data:**
- `name_uz` (string, required)
- `name_ru` (string, required)
- `name_eng` (string, required)
- `price` (int, required)
- `description_uz` (string, optional)
- `description_ru` (string, optional)
- `description_eng` (string, optional)
- `category_id` (int, required)
- `collection_id` (int, optional)
- `clothing_type` (string, required) - "erkak", "ayol", "unisex"
- `is_active` (bool, default: true)

**Example:**
```javascript
const formData = new FormData();
formData.append('name_uz', "Ko'ylak");
formData.append('name_ru', 'Рубашка');
formData.append('name_eng', 'Shirt');
formData.append('price', '150000');
formData.append('category_id', '1');
formData.append('clothing_type', 'erkak');

await api.post('/products', formData);
```

### PATCH `/api/products/{product_id}`
Update product (admin only)

**Auth Required:** Yes

**Form Data:** Same as POST (all fields optional)

### DELETE `/api/products/{product_id}`
Delete product (admin only)

**Auth Required:** Yes

### GET `/api/products/export/csv`
Export products to CSV (admin only)

**Auth Required:** Yes

**Query Parameters:**
- `include_inactive` (bool, default: false)

**Response:** CSV file download

---

## Product Photos

### POST `/api/products/{product_id}/photos`
Upload product photo (admin only)

**Auth Required:** Yes

**Form Data:**
- `photo` (file, required) - Image file

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": 1,
    "product_id": 1,
    "photo_url": "/media/products/photo.jpg"
  }
}
```

### DELETE `/api/products/{product_id}/photos/{photo_id}`
Delete product photo (admin only)

**Auth Required:** Yes

---

## Product Items (Variants)

### GET `/api/products/{product_id}/items`
Get product variants (public)

**Response:**
```json
[
  {
    "id": 1,
    "product_id": 1,
    "color_id": 1,
    "size_id": 2,
    "total_count": 50,
    "min_stock_level": 10,
    "color": {
      "id": 1,
      "name_uz": "Qora",
      "color_code": "#000000"
    },
    "size": {
      "id": 2,
      "name": "M"
    }
  }
]
```

### POST `/api/products/{product_id}/items`
Create product variant (admin only)

**Auth Required:** Yes

**Form Data:**
- `color_id` (int, required)
- `size_id` (int, required)
- `total_count` (int, required)
- `min_stock_level` (int, default: 10)

### PATCH `/api/products/{product_id}/items/{item_id}`
Update product variant (admin only)

**Auth Required:** Yes

**Form Data:**
- `color_id` (int, optional)
- `size_id` (int, optional)
- `total_count` (int, optional)
- `min_stock_level` (int, optional)

### DELETE `/api/products/{product_id}/items/{item_id}`
Delete product variant (admin only)

**Auth Required:** Yes

---

## Categories

### GET `/api/categories`
Get all categories (public, cached 10 min)

**Response:**
```json
[
  {
    "id": 1,
    "name_uz": "Erkaklar kiyimi",
    "name_ru": "Мужская одежда",
    "name_eng": "Men's clothing"
  }
]
```

### GET `/api/categories/{category_id}`
Get single category (public)

### POST `/api/categories`
Create category (admin only)

**Auth Required:** Yes

**Form Data:**
- `name_uz` (string, required)
- `name_ru` (string, required)
- `name_eng` (string, required)

### PATCH `/api/categories/{category_id}`
Update category (admin only)

**Auth Required:** Yes

**Form Data:** Same as POST (all optional)

### DELETE `/api/categories/{category_id}`
Delete category (admin only)

**Auth Required:** Yes

---

## Collections

### GET `/api/collections`
Get all collections (public, cached 10 min)

**Response:**
```json
[
  {
    "id": 1,
    "name_uz": "Yoz kolleksiyasi",
    "name_ru": "Летняя коллекция",
    "name_eng": "Summer collection"
  }
]
```

### GET `/api/collections/{collection_id}`
Get single collection (public)

### POST `/api/collections`
Create collection (admin only)

**Auth Required:** Yes

**Form Data:**
- `name_uz` (string, required)
- `name_ru` (string, required)
- `name_eng` (string, required)

### PATCH `/api/collections/{collection_id}`
Update collection (admin only)

**Auth Required:** Yes

### DELETE `/api/collections/{collection_id}`
Delete collection (admin only)

**Auth Required:** Yes

---

## Colors

### GET `/api/colors`
Get all colors (public, cached 10 min)

**Response:**
```json
[
  {
    "id": 1,
    "name_uz": "Qora",
    "name_ru": "Черный",
    "name_eng": "Black",
    "color_code": "#000000"
  }
]
```

### GET `/api/colors/{color_id}`
Get single color (public)

### POST `/api/colors`
Create color (admin only)

**Auth Required:** Yes

**Form Data:**
- `name_uz` (string, required)
- `name_ru` (string, required)
- `name_eng` (string, required)
- `color_code` (string, required) - Hex color code (e.g., "#FF0000")

### PATCH `/api/colors/{color_id}`
Update color (admin only)

**Auth Required:** Yes

### DELETE `/api/colors/{color_id}`
Delete color (admin only)

**Auth Required:** Yes

---

## Sizes

### GET `/api/sizes`
Get all sizes (public, cached 10 min)

**Response:**
```json
[
  {
    "id": 1,
    "name": "S"
  },
  {
    "id": 2,
    "name": "M"
  }
]
```

### GET `/api/sizes/{size_id}`
Get single size (public)

### POST `/api/sizes`
Create size (admin only)

**Auth Required:** Yes

**Form Data:**
- `name` (string, required) - Size name (e.g., "XL", "42", "L")

### PATCH `/api/sizes/{size_id}`
Update size (admin only)

**Auth Required:** Yes

### DELETE `/api/sizes/{size_id}`
Delete size (admin only)

**Auth Required:** Yes

---

## Orders

### GET `/api/order`
Get all orders (admin only)

**Auth Required:** Yes

**Query Parameters:**
- `status` (string) - Filter by status: "new", "paid", "is_process", "ready", "in_progress", "delivered", "cancelled", "vozvrat"
- `payment` (string) - Filter by payment method: "cash", "card", "payme", "click"
- `search` (string) - Search by customer name or phone
- `sort_by` (string, default: "id") - "id", "created_at", "status", "payment", "first_name"
- `sort_dir` (string, default: "desc") - "asc", "desc"
- `limit` (int, default: 100, max: 500)

**Response:**
```json
[
  {
    "id": 1,
    "first_name": "Alisher",
    "last_name": "Karimov",
    "phone_number": "+998901234567",
    "address": "Toshkent, Chilonzor",
    "status": "new",
    "payment": "cash",
    "total_price": 450000,
    "created_at": "2026-05-06T10:00:00",
    "items": [
      {
        "id": 1,
        "product_id": 1,
        "product_item_id": 1,
        "count": 2,
        "price": 150000
      }
    ]
  }
]
```

### GET `/api/order/{order_id}`
Get single order (admin only)

**Auth Required:** Yes

### POST `/api/order`
Create order (public)

**JSON Body:**
```json
{
  "first_name": "Alisher",
  "last_name": "Karimov",
  "phone_number": "+998901234567",
  "address": "Toshkent, Chilonzor",
  "payment": "cash",
  "items": [
    {
      "product_id": 1,
      "product_item_id": 1,
      "count": 2
    }
  ]
}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": 1,
    "status": "new",
    "total_price": 300000
  }
}
```

### PATCH `/api/order/{order_id}/status`
Update order status (admin only)

**Auth Required:** Yes

**Form Data:**
- `status` (string, required) - New status

**Status Flow:**
- `new` → `paid`, `is_process`, `cancelled`
- `paid` → `is_process`, `cancelled`
- `is_process` → `ready`, `cancelled`
- `ready` → `in_progress`, `cancelled`
- `in_progress` → `delivered`, `cancelled`
- `delivered` → `vozvrat` (returned)

### DELETE `/api/order/{order_id}`
Delete order (admin only)

**Auth Required:** Yes

### GET `/api/order/export/csv`
Export orders to CSV (admin only)

**Auth Required:** Yes

**Query Parameters:**
- `status` (string, optional)
- `payment` (string, optional)

**Response:** CSV file download

---

## Admin Users

### GET `/api/panel/me`
Get current user info (admin/operator)

**Auth Required:** Yes

**Response:**
```json
{
  "id": 1,
  "username": "SunnatDevPy",
  "status": "admin",
  "is_active": true
}
```

### GET `/api/panel/operators`
Get all operators (super admin only)

**Auth Required:** Yes (Super Admin)

**Response:**
```json
[
  {
    "id": 2,
    "username": "operator1",
    "status": "operator",
    "is_active": true
  }
]
```

### POST `/api/panel/operators`
Create operator (super admin only)

**Auth Required:** Yes (Super Admin)

**Form Data:**
- `username` (string, required)
- `operator_code` (string, required) - Password
- `status` (string, default: "operator") - "operator" or "admin"
- `is_active` (bool, default: true)

### PATCH `/api/panel/operators/{user_id}`
Update operator (super admin only)

**Auth Required:** Yes (Super Admin)

**Form Data:**
- `username` (string, optional)
- `operator_code` (string, optional) - New password
- `is_active` (bool, optional)

### DELETE `/api/panel/operators/{user_id}`
Delete operator (super admin only)

**Auth Required:** Yes (Super Admin)

---

## Payments

### POST `/api/payme`
Payme payment callback (webhook)

**Note:** This is called by Payme payment system, not by frontend

### POST `/api/click/prepare`
Click payment prepare (webhook)

**Note:** This is called by Click payment system

### POST `/api/click/complete`
Click payment complete (webhook)

**Note:** This is called by Click payment system

### GET `/api/payment-urls`
Get payment URLs for order (public)

**Query Parameters:**
- `order_id` (int, required)

**Response:**
```json
{
  "payme_url": "https://checkout.paycom.uz/...",
  "click_url": "https://my.click.uz/..."
}
```

---

## Dashboard

### GET `/api/dashboard/stats`
Get dashboard statistics (admin only)

**Auth Required:** Yes

**Response:**
```json
{
  "total_orders": 150,
  "total_revenue": 45000000,
  "pending_orders": 12,
  "low_stock_items": 5,
  "today_orders": 8,
  "today_revenue": 2400000
}
```

### GET `/api/dashboard/revenue`
Get revenue statistics (admin only)

**Auth Required:** Yes

**Query Parameters:**
- `period` (string, default: "month") - "week", "month", "year"

**Response:**
```json
{
  "period": "month",
  "data": [
    {
      "date": "2026-05-01",
      "revenue": 1500000,
      "orders": 15
    }
  ]
}
```

### GET `/api/dashboard/top-products`
Get top selling products (admin only)

**Auth Required:** Yes

**Query Parameters:**
- `limit` (int, default: 10)

**Response:**
```json
[
  {
    "product_id": 1,
    "product_name": "Ko'ylak",
    "total_sold": 45,
    "total_revenue": 6750000
  }
]
```

---

## Stock Movements

### GET `/api/stock-movements`
Get stock movement history (admin only)

**Auth Required:** Yes

**Query Parameters:**
- `product_item_id` (int, optional)
- `movement_type` (string, optional) - "in", "out", "adjustment"
- `limit` (int, default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "product_item_id": 1,
    "movement_type": "out",
    "quantity": 2,
    "reason": "Order #123",
    "created_at": "2026-05-06T10:00:00"
  }
]
```

### POST `/api/stock-movements`
Create stock movement (admin only)

**Auth Required:** Yes

**JSON Body:**
```json
{
  "product_item_id": 1,
  "movement_type": "in",
  "quantity": 50,
  "reason": "New stock arrival"
}
```

---

## Alerts

### GET `/api/alerts`
Get system alerts (admin only)

**Auth Required:** Yes

**Response:**
```json
[
  {
    "id": 1,
    "type": "low_stock",
    "message": "Product item #5 is low on stock (3 remaining)",
    "is_read": false,
    "created_at": "2026-05-06T10:00:00"
  }
]
```

### PATCH `/api/alerts/{alert_id}/read`
Mark alert as read (admin only)

**Auth Required:** Yes

---

## System

### GET `/api/system/health`
Health check (public)

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-05-06T10:00:00"
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message in Uzbek/Russian/English"
}
```

### Common HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Conflict (e.g., insufficient stock)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Rate Limiting

API has rate limiting enabled:
- **Per minute:** Check `RATE_LIMIT_PER_MINUTE` in config
- **Per hour:** 10x per minute limit

When rate limit is exceeded, you'll receive `429 Too Many Requests`.

---

## CORS

CORS is enabled for all origins (`*`). All HTTP methods are allowed.

---

## Notes for Frontend Developers

1. **Base URL:** Always use `/api` prefix for all API calls
2. **Authentication:** Store credentials securely, use axios interceptors
3. **File Uploads:** Use `FormData` with `multipart/form-data`
4. **Caching:** Categories, collections, colors, sizes are cached for 10 minutes
5. **Pagination:** Use `limit` parameter, max 500 items per request
6. **Search:** Use `/search/advanced` for complex filters
7. **Order Status:** Follow the status flow diagram when updating orders
8. **Stock Management:** Check stock before creating orders
9. **Error Handling:** Always handle 401/403 for auth errors
10. **Webhooks:** Payme/Click endpoints are for payment system callbacks only

---

## Example: Complete Order Flow

```javascript
// 1. Get products
const products = await api.get('/products?limit=10');

// 2. Get product details with variants
const product = await api.get('/products/1');

// 3. Create order (public, no auth)
const order = await axios.post('http://your-domain.com/api/order', {
  first_name: 'Alisher',
  last_name: 'Karimov',
  phone_number: '+998901234567',
  address: 'Toshkent',
  payment: 'payme',
  items: [
    {
      product_id: 1,
      product_item_id: 1,
      count: 2
    }
  ]
});

// 4. Get payment URL
const paymentUrls = await axios.get(`http://your-domain.com/api/payment-urls?order_id=${order.data.data.id}`);

// 5. Redirect to payment
window.location.href = paymentUrls.data.payme_url;

// 6. Admin updates order status (after payment)
await api.patch(`/order/${order.data.data.id}/status`, 
  new URLSearchParams({ status: 'paid' })
);
```

---

## Support

For issues or questions, contact the backend team or check:
- Swagger Docs: `http://your-domain.com/api/docs`
- ReDoc: `http://your-domain.com/api/redoc`
