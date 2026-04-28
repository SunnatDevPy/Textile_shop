# OpenAPI client generator (frontend)

Frontendda API typelarni avtomatik olish uchun OpenAPI JSON'dan client generate qiling.

## 1) OpenAPI schema URL

- Lokal: `http://localhost:8000/openapi.json`
- Prod: `https://textile.okach-admin.uz/openapi.json`

## 2) TypeScript typelar generate qilish

```bash
npx openapi-typescript https://textile.okach-admin.uz/openapi.json -o src/api/types.ts
```

## 3) Fetch client generate qilish (ixtiyoriy)

```bash
npx @hey-api/openapi-ts -i https://textile.okach-admin.uz/openapi.json -o src/api/client
```

## 4) Tavsiya

- CI/CD pipeline’da schema o'zgarganda clientni qayta generate qiling.
- `types.ts` ni frontend repository'ga commit qiling.
