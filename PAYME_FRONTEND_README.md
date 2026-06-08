# Payme — frontend integratsiya qo‘llanmasi

Bu hujjat frontend dasturchisi uchun: **qaysi API ga ulanish**, **qanday ketma-ketlikda chaqirish** va **Payme to‘lovi qanday yakunlanishi**.

> Backend webhook (`POST /api/payme`) ni **frontend chaqirmaydi** — uni faqat Payme serveri chaqiradi.

---

## 1. Qisqa sxema

```
Frontend                    Backend API                 Payme
   |                            |                        |
   |-- GET /api/payments/list ->|                        |
   |<- payme status: true ------|                        |
   |                            |                        |
   |-- POST /api/order -------->|  buyurtma yaratiladi   |
   |   (to'lov turi yo'q)       |  (status: yangi)       |
   |<- order_id: 42 ------------|                        |
   |                            |                        |
   |-- POST /api/order/pay ---->|  payment: payme        |
   |   { order_id, payment }    |                        |
   |<- payment_url -------------|                        |
   |                            |                        |
   |========= window.location = payment_url =============>|
   |                            |                        |
   |                            |<-- POST /api/payme ----|  (JSON-RPC webhook)
   |                            |    PerformTransaction   |
   |                            |    status -> to'landi   |
   |<========= redirect success page =====================|
```

**Frontend vazifasi:** to‘lov usulini ko‘rsatish → buyurtma yaratish → `payment_url` ga yo‘naltirish → success sahifasini ko‘rsatish.

**Backend vazifasi:** Payme serveridan kelgan webhook orqali to‘lovni tasdiqlash, stock kamaytirish, buyurtma holatini yangilash.

---

## 2. Frontend ulaydigan API lar

| # | Method | Endpoint | Auth | Vazifa |
|---|--------|----------|------|--------|
| 1 | `GET` | `/api/payments/list` | Yo‘q | Checkoutda qaysi to‘lov usullari ko‘rinsin |
| 2 | `POST` | `/api/order` | Yo‘q | Buyurtma yaratish (`order_id` qaytadi) |
| 3 | `POST` | `/api/order/pay` | Yo‘q | **`order_id` + `payment`** → `payment_url` |
| 4 | `GET` | `/api/payment-url/{order_id}/payme` | Yo‘q | (Ixtiyoriy) GET orqali havola olish |
| 5 | `GET` | `/api/payment-url/{order_id}/payment-info` | Yo‘q | (Ixtiyoriy) buyurtma + summa |

### Frontend ULAMAYDI

| Method | Endpoint | Kim chaqiradi |
|--------|----------|---------------|
| `POST` | `/api/payme` | Faqat **Payme serveri** (Merchant API webhook) |

---

## 3. Qadam-baqadam integratsiya

### Qadam 1 — To‘lov usullarini olish

Checkout sahifasi ochilganda:

```http
GET /api/payments/list
```

**Javob:**

```json
{
  "ok": true,
  "data": [
    {
      "method": "payme",
      "icon": "https://textile.okach-admin.uz/static/payments/payme.svg",
      "status": true
    },
    {
      "method": "click",
      "icon": "https://textile.okach-admin.uz/static/payments/click.svg",
      "status": false
    },
    {
      "method": "cash",
      "icon": "https://textile.okach-admin.uz/static/payments/cash.svg",
      "status": true
    }
  ],
  "meta": {},
  "error": null
}
```

**Frontend qoidasi:**

- Faqat `status: true` bo‘lgan usullarni ko‘rsating.
- `method` qiymati `POST /api/order` dagi `payment` maydoniga aynan shunday yuboriladi: `"payme"`, `"click"`, `"cash"`.

```javascript
const API = "https://textile.okach-admin.uz/api";

async function loadPaymentMethods() {
  const res = await fetch(`${API}/payments/list`);
  const { data } = await res.json();
  return data.filter((p) => p.status);
}
```

---

### Qadam 2 — Buyurtma yaratish

Foydalanuvchi «Buyurtma berish» tugmasini bosganda (**to‘lov turi yuborilmaydi**):

```http
POST /api/order
Content-Type: application/json
```

**Body:**

```json
{
  "first_name": "Ali",
  "last_name": "Valiyev",
  "country": "UZ",
  "address": "Chilonzor 12-uy",
  "town_city": "Toshkent",
  "contact": "+998901234567",
  "postcode_zip": 100000,
  "items": [
    {
      "product_id": 1,
      "product_item_id": 5,
      "count": 2
    }
  ]
}
```

**Javob:**

```json
{
  "ok": true,
  "data": {
    "order_id": 42,
    "status": "yangi",
    "payment": "tanlanmagan",
    "total_sum": 110000
  }
}
```

---

### Qadam 3 — To‘lov turini tanlash va Payme ga yuborish

Mijoz **Payme** ni tanlagach, frontend `order_id` va `payment` yuboradi:

```http
POST /api/order/pay
Content-Type: application/json
```

**Body:**

```json
{
  "order_id": 42,
  "payment": "payme"
}
```

| `payment` | Qiymat |
|-----------|--------|
| Payme | `"payme"` |
| Click | `"click"` |
| Naqd | `"cash"` |

**Javob (payme):**

```json
{
  "ok": true,
  "data": {
    "order_id": 42,
    "payment": "payme",
    "total_sum": 110000,
    "amount_tiyin": 11000000,
    "payment_url": "https://checkout.test.paycom.uz/..."
  }
}
```

**Frontend kod:**

```javascript
// 1. Buyurtma yaratish
const orderRes = await fetch(`${API}/order`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ ...form, items: cart }),
});
const { order_id } = (await orderRes.json()).data;

// 2. To'lov turini tanlash (masalan payme)
const payRes = await fetch(`${API}/order/pay`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ order_id, payment: "payme" }),
});
const payData = (await payRes.json()).data;

// 3. Payme ga yo'naltirish
if (payData.payment_url) {
  window.location.href = payData.payment_url;
}
```

---

### Qadam 4 — Payme sahifasiga yo‘naltirish

`payment_url` ni brauzerda oching:

```javascript
window.location.href = payData.payment_url;
```

**Muhim:** Frontend Payme bilan to‘g‘ridan-to‘g‘ri ishlamaydi. Faqat backend bergan `payment_url` ga yo‘naltirasiz.

---

### Qadam 4 — To‘lovdan keyin qaytish (success sahifasi)

Payme to‘lovdan keyin foydalanuvchini `PUBLIC_BASE_URL` dagi manzilga qaytaradi:

```
https://sizning-frontend.uz/order/{order_id}/success
```

Bu URL ni frontendda route qiling. Masalan React:

```
/order/:orderId/success
```

Success sahifada:

1. «To‘lovingiz qabul qilindi» xabari
2. `order_id` ko‘rsatish
3. (Ixtiyoriy) operator paneli orqali holat tekshirish — mijoz uchun alohida endpoint yo‘q

> Payme webhook backendda ishlaydi. Success sahifaga kelganida to‘lov allaqachon tasdiqlangan bo‘lishi mumkin, lekin bir necha soniya kechikishi ham mumkin.

---

## 4. Ixtiyoriy API lar

### Havolani keyinroq olish

Agar `POST /api/order` dan `payment_url` olinmagan yoki foydalanuvchi sahifani yopib qayta kelsa:

```http
GET /api/payment-url/42/payme
```

**Javob:**

```json
{
  "payment_url": "https://checkout.test.paycom.uz/...",
  "order_id": 42,
  "amount": 11000000,
  "payment_system": "payme"
}
```

Shartlar:

- Buyurtma `status: "yangi"` bo‘lishi kerak
- Summa kamida 1 so‘m (100 tiyin)

### Buyurtma to‘lov ma’lumotlari

```http
GET /api/payment-url/42/payment-info
```

Buyurtma tafsilotlari + `payment_url` (agar Payme bo‘lsa).

---

## 5. Xatoliklar (frontend uchun)

| HTTP | `detail` misoli | Sabab / yechim |
|------|-----------------|----------------|
| `400` | `To'lov turi faqat 'click', 'payme' yoki 'cash'...` | `payment` noto‘g‘ri |
| `400` | `Mahsulot va variant mos emas` | `product_item_id` xato |
| `400` | `Buyurtma summasi Payme uchun juda kichik` | Jami < 1 so‘m |
| `400` | `Buyurtma allaqachon to'langan...` | `/payment-url/...` da status `yangi` emas |
| `503` | `Payme sozlamalari (.env) to'ldirilmagan` | Serverda Payme kalitlari yo‘q — `GET /payments/list` da `status: false` bo‘ladi |
| `422` | Validation errors | Majburiy maydonlar to‘ldirilmagan |

**422 format:**

```json
{
  "detail": [
    { "loc": ["body", "contact"], "msg": "Field required", "type": "missing" }
  ]
}
```

---

## 6. Naqd to‘lov (`cash`) farqi

`payment: "cash"` bo‘lsa:

- `payment_url` **qaytmaydi**
- Foydalanuvchini Payme ga yo‘naltirmaysiz
- Operator keyinroq admin panelda `POST /api/order/{id}/confirm-payment` bilan tasdiqlaydi

```javascript
if (selectedPayment === "cash") {
  const order = await createOrder(form, cart, "cash");
  navigate(`/order/${order.order_id}/success?type=cash`);
  return;
}
```

---

## 7. To‘liq checkout misoli (React pseudo-kod)

```javascript
const API = import.meta.env.VITE_API_URL; // masalan: https://textile.okach-admin.uz/api

export function CheckoutPage() {
  const [methods, setMethods] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetch(`${API}/payments/list`)
      .then((r) => r.json())
      .then(({ data }) => setMethods(data.filter((m) => m.status)));
  }, []);

  async function handleSubmit(form, cart) {
    if (!selected) return;

    const res = await fetch(`${API}/order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        payment: selected,
        items: cart.map((c) => ({
          product_id: c.productId,
          product_item_id: c.variantId,
          count: c.qty,
        })),
      }),
    });

    const body = await res.json();
    if (!body.ok) throw new Error(body.detail || "Xato");

    const { order_id, payment_url } = body.data;

    if (selected === "payme" || selected === "click") {
      window.location.href = payment_url;
      return;
    }

    // cash
    window.location.href = `/order/${order_id}/success`;
  }

  return (
    <div>
      {methods.map((m) => (
        <button key={m.method} onClick={() => setSelected(m.method)}>
          <img src={m.icon} alt={m.method} />
          {m.method}
        </button>
      ))}
      <button onClick={() => handleSubmit(form, cart)}>Buyurtma berish</button>
    </div>
  );
}
```

---

## 8. Backend sozlamalari (frontend bilishi kerak bo‘lganlar)

Frontend `.env` o‘qimaydi, lekin quyidagilar ishlashiga ta’sir qiladi:

| O‘zgaruvchi | Ta’siri |
|-------------|---------|
| `PAYME_MERCHANT_ID` | Payme yoqilgan/yopilgan (`/payments/list` → `status`) |
| `PAYME_SECRET_KEY` | Payme yoqilgan/yopilgan |
| `PAYME_ENDPOINT` | Test: `https://checkout.test.paycom.uz`, prod: `https://checkout.paycom.uz` |
| `PUBLIC_BASE_URL` | To‘lovdan keyin qaytish URL prefiksi |

Payme **yoqilmagan** bo‘lsa:

- `GET /api/payments/list` → `payme.status = false`
- `POST /api/order` + `payment: "payme"` → `503` xato

---

## 9. Summa birliklari (muhim)

| Joy | Birlik | Misol |
|-----|--------|-------|
| `total_sum` (order javob) | so‘m | `110000` |
| `amount_tiyin` (order javob) | tiyin | `11000000` |
| `amount` (`/payment-url/.../payme`) | tiyin | `11000000` |

**Qoida:** 1 so‘m = 100 tiyin.

Frontend faqat `total_sum` ni foydalanuvchiga ko‘rsatadi. `amount_tiyin` ni ko‘rsatish shart emas — backend Payme havolasini o‘zi hisoblaydi.

---

## 10. Tekshirish ro‘yxati (checklist)

- [ ] `GET /api/payments/list` — faqat `status: true` usullar chiqyaptimi?
- [ ] `POST /api/order` — `payment: "payme"` bilan `payment_url` kelyaptimi?
- [ ] `window.location.href = payment_url` — Payme sahifasi ochilyaptimi?
- [ ] Success route: `/order/:id/success` mavjudmi?
- [ ] `product_item_id` to‘g‘ri variant ID si yuborilyaptimi?
- [ ] Payme yoqilmagan serverda payme tugmasi yashirinmi?

---

## 11. Swagger

Barcha endpointlarni jonli test qilish:

```
http://localhost:8000/api/docs
```

Qidirish: **Payments**, **Orders**, **Payment URLs**.

---

## 12. Qisqa xulosa

| Frontend nima qiladi | API |
|----------------------|-----|
| To‘lov tugmalarini ko‘rsatish | `GET /api/payments/list` |
| Buyurtma + Payme link olish | `POST /api/order` (`payment: "payme"`) |
| Payme ga yo‘naltirish | `data.payment_url` → `window.location` |
| Success sahifa | Frontend route (`/order/{id}/success`) |
| Havolani qayta olish | `GET /api/payment-url/{id}/payme` |

| Frontend nima qilmaydi | Sabab |
|------------------------|-------|
| `POST /api/payme` chaqirish | Bu Payme server webhook i |
| Payme secret key ishlatish | Xavfsizlik — faqat backendda |
| To‘lovni o‘zi tasdiqlash | Backend `PerformTransaction` da qiladi |
