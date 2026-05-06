# Payment Webhooks Documentation

**Date:** 2026-05-06  
**Payment Systems:** Payme, Click

---

## Overview

This document describes the payment webhook endpoints for Payme and Click payment systems. These endpoints are called by the payment providers, not by the frontend.

---

## Payme Webhook

### Endpoint
```
POST https://textile.okach-admin.uz/api/payme
```

### Protocol
JSON-RPC 2.0

### Authentication
Basic Auth with:
- **Username:** `PAYME_MERCHANT_ID` (from config)
- **Password:** `PAYME_SECRET_KEY` (from config)

### Supported Methods

#### 1. CheckPerformTransaction
Check if transaction can be performed

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 15000000,
    "account": {
      "order_id": 1
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "allow": true
  }
}
```

#### 2. CreateTransaction
Create a new transaction

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "CreateTransaction",
  "params": {
    "id": "payme_transaction_id",
    "time": 1620000000000,
    "amount": 15000000,
    "account": {
      "order_id": 1
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "create_time": 1620000000000,
    "transaction": "1",
    "state": 0
  }
}
```

#### 3. PerformTransaction
Perform (complete) the transaction

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "PerformTransaction",
  "params": {
    "id": "payme_transaction_id"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "transaction": "1",
    "perform_time": 1620000100000,
    "state": 1
  }
}
```

**Actions on Perform:**
- Deduct stock from warehouse
- Update order status to `PAID`
- Send Telegram notification

#### 4. CancelTransaction
Cancel a transaction

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "CancelTransaction",
  "params": {
    "id": "payme_transaction_id",
    "reason": 1
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "transaction": "1",
    "cancel_time": 1620000200000,
    "state": -1
  }
}
```

#### 5. CheckTransaction
Check transaction status

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "CheckTransaction",
  "params": {
    "id": "payme_transaction_id"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "create_time": 1620000000000,
    "perform_time": 1620000100000,
    "cancel_time": 0,
    "transaction": "1",
    "state": 1,
    "reason": null
  }
}
```

#### 6. GetStatement
Get transactions for a time period

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "GetStatement",
  "params": {
    "from": 1620000000000,
    "to": 1620086400000
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "transactions": [
      {
        "id": "payme_transaction_id",
        "time": 1620000000000,
        "amount": 15000000,
        "account": {
          "order_id": 1
        },
        "create_time": 1620000000000,
        "perform_time": 1620000100000,
        "cancel_time": 0,
        "transaction": "1",
        "state": 1,
        "reason": null
      }
    ]
  }
}
```

### Transaction States
- `0` - Created (waiting for perform)
- `1` - Performed (completed)
- `-1` - Cancelled after perform
- `-2` - Cancelled before perform

### Error Codes
- `-32400` - Internal error
- `-32504` - Insufficient privilege
- `-32600` - Invalid JSON-RPC
- `-32601` - Method not found
- `-31001` - Invalid amount
- `-31003` - Transaction not found
- `-31050` - Invalid account (order not found)
- `-31008` - Could not perform
- `-31007` - Could not cancel

---

## Click Webhook

### Endpoints

#### 1. Prepare
```
POST https://textile.okach-admin.uz/api/click/prepare
```

#### 2. Complete
```
POST https://textile.okach-admin.uz/api/click/complete
```

### Authentication
MD5 signature verification

### Prepare Request

**Request:**
```json
{
  "click_trans_id": 123456789,
  "service_id": 12345,
  "click_paydoc_id": 987654321,
  "merchant_trans_id": "1",
  "amount": 150000.00,
  "action": 0,
  "error": 0,
  "error_note": "Success",
  "sign_time": "2026-05-06 10:00:00",
  "sign_string": "md5_hash_here"
}
```

**Response (Success):**
```json
{
  "click_trans_id": 123456789,
  "merchant_trans_id": "1",
  "merchant_prepare_id": 1,
  "error": 0,
  "error_note": "Success"
}
```

**Response (Error):**
```json
{
  "click_trans_id": 123456789,
  "merchant_trans_id": "1",
  "merchant_prepare_id": 0,
  "error": -5,
  "error_note": "Order not found"
}
```

### Complete Request

**Request:**
```json
{
  "click_trans_id": 123456789,
  "service_id": 12345,
  "click_paydoc_id": 987654321,
  "merchant_trans_id": "1",
  "merchant_prepare_id": 1,
  "amount": 150000.00,
  "action": 1,
  "error": 0,
  "error_note": "Success",
  "sign_time": "2026-05-06 10:01:00",
  "sign_string": "md5_hash_here"
}
```

**Response (Success):**
```json
{
  "click_trans_id": 123456789,
  "merchant_trans_id": "1",
  "merchant_confirm_id": 1,
  "error": 0,
  "error_note": "Success"
}
```

**Actions on Complete:**
- Deduct stock from warehouse
- Update order status to `PAID`
- Send Telegram notification

### Click Error Codes
- `0` - Success
- `-1` - Sign check failed
- `-3` - Action not found
- `-4` - Already paid
- `-5` - Order not found / Invalid parameters
- `-6` - Transaction not found
- `-9` - Internal error / Transaction cancelled

### Signature Verification

Click signature formula:
```
MD5(click_trans_id + service_id + secret_key + merchant_trans_id + amount + action + sign_time)
```

Example (Python):
```python
import hashlib

data = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
signature = hashlib.md5(data.encode('utf-8')).hexdigest()
```

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Payme
PAYME_MERCHANT_ID=your_merchant_id
PAYME_SECRET_KEY=your_secret_key

# Click
CLICK_MERCHANT_ID=your_merchant_id
CLICK_SERVICE_ID=your_service_id
CLICK_SECRET_KEY=your_secret_key
```

### Nginx Configuration

Webhook endpoints have special timeout settings (120 seconds):

```nginx
location ~ ^/api/(payme|click)/ {
    proxy_pass http://localhost:8000;
    proxy_read_timeout 120;
    proxy_connect_timeout 120;
    proxy_send_timeout 120;
    proxy_buffering off;
}
```

---

## Testing

### Test Payme Webhook

```bash
curl -X POST https://textile.okach-admin.uz/api/payme \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'merchant_id:secret_key' | base64)" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "CheckPerformTransaction",
    "params": {
      "amount": 15000000,
      "account": {
        "order_id": 1
      }
    }
  }'
```

### Test Click Webhook

```bash
# Prepare
curl -X POST https://textile.okach-admin.uz/api/click/prepare \
  -H "Content-Type: application/json" \
  -d '{
    "click_trans_id": 123456789,
    "service_id": 12345,
    "click_paydoc_id": 987654321,
    "merchant_trans_id": "1",
    "amount": 150000.00,
    "action": 0,
    "error": 0,
    "error_note": "Success",
    "sign_time": "2026-05-06 10:00:00",
    "sign_string": "calculated_md5_hash"
  }'

# Complete
curl -X POST https://textile.okach-admin.uz/api/click/complete \
  -H "Content-Type: application/json" \
  -d '{
    "click_trans_id": 123456789,
    "service_id": 12345,
    "click_paydoc_id": 987654321,
    "merchant_trans_id": "1",
    "merchant_prepare_id": 1,
    "amount": 150000.00,
    "action": 1,
    "error": 0,
    "error_note": "Success",
    "sign_time": "2026-05-06 10:01:00",
    "sign_string": "calculated_md5_hash"
  }'
```

---

## Database Schema

### PaymentReceipt Table

```sql
CREATE TABLE payment_receipts (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    payment_system VARCHAR(20) NOT NULL, -- 'payme' or 'click'
    transaction_id VARCHAR(255) NOT NULL,
    amount BIGINT NOT NULL, -- Amount in tiyin/kopeykas
    state INTEGER NOT NULL, -- Transaction state
    create_time BIGINT, -- Unix timestamp in milliseconds
    perform_time BIGINT,
    cancel_time BIGINT,
    reason INTEGER,
    receipt_data TEXT -- JSON data from payment system
);
```

---

## Payment Flow

### Customer Side

1. Customer creates order via `/api/order` (POST)
2. Frontend gets payment URLs via `/api/payment-urls?order_id=1` (GET)
3. Customer redirected to Payme/Click payment page
4. Customer completes payment on payment provider's site

### Webhook Side (Automatic)

#### Payme Flow:
1. Payme calls `CheckPerformTransaction` - verify order exists and is NEW
2. Payme calls `CreateTransaction` - create payment receipt with state=0
3. Payme calls `PerformTransaction` - complete payment:
   - Update receipt state to 1
   - Deduct stock from warehouse
   - Update order status to PAID
   - Send Telegram notification

#### Click Flow:
1. Click calls `/prepare` - verify order and create receipt with state=0
2. Click calls `/complete` - complete payment:
   - Update receipt state to 1
   - Deduct stock from warehouse
   - Update order status to PAID
   - Send Telegram notification

---

## Security Notes

1. **Always verify signatures** - Both Payme and Click use authentication
2. **Check order status** - Only allow payment for NEW orders
3. **Idempotency** - Handle duplicate webhook calls gracefully
4. **Stock management** - Only deduct stock once on PerformTransaction/Complete
5. **Error handling** - Return proper error codes to payment systems
6. **Logging** - Log all webhook requests for debugging

---

## Troubleshooting

### Payme Issues

**Problem:** "SIGN CHECK FAILED"
- **Solution:** Check `PAYME_MERCHANT_ID` and `PAYME_SECRET_KEY` in `.env`

**Problem:** "Order not found"
- **Solution:** Verify order_id exists in database and status is NEW

**Problem:** "Could not perform"
- **Solution:** Check if order status is correct and stock is available

### Click Issues

**Problem:** "SIGN CHECK FAILED!"
- **Solution:** Check signature calculation and `CLICK_SECRET_KEY`

**Problem:** "Service ID is incorrect"
- **Solution:** Verify `CLICK_SERVICE_ID` matches the one from Click

**Problem:** "Transaction not found"
- **Solution:** Ensure prepare was called before complete

---

## Support

For payment integration issues:
- **Payme:** https://developer.help.paycom.uz/
- **Click:** https://docs.click.uz/

For backend issues, check:
- Application logs: `/var/log/nginx/textile-shop-error.log`
- FastAPI logs: Check console output or application logs
- Database: Check `payment_receipts` table for transaction states
