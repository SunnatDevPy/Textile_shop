"""Admin parol hash qilish utility."""
import bcrypt
import sys


def hash_password(password: str) -> str:
    """Parolni bcrypt bilan hash qilish."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Parolni tekshirish."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def main():
    print("=" * 60)
    print("Admin Parol Hash Generator")
    print("=" * 60)
    print()

    # Parol kiritish
    password = input("Yangi admin parolni kiriting: ").strip()

    if len(password) < 8:
        print("❌ Xato: Parol kamida 8 ta belgidan iborat bo'lishi kerak!")
        sys.exit(1)

    # Tasdiqlash
    confirm = input("Parolni qayta kiriting: ").strip()

    if password != confirm:
        print("❌ Xato: Parollar mos kelmadi!")
        sys.exit(1)

    # Hash qilish
    print("\n⏳ Parol hash qilinmoqda...")
    hashed = hash_password(password)

    print("\n✅ Parol muvaffaqiyatli hash qilindi!")
    print("\n" + "=" * 60)
    print("BCRYPT HASH:")
    print("=" * 60)
    print(hashed)
    print("=" * 60)

    # Tekshirish
    print("\n🔍 Hash tekshirilmoqda...")
    if verify_password(password, hashed):
        print("✅ Hash to'g'ri ishlayapti!")
    else:
        print("❌ Xato: Hash noto'g'ri!")
        sys.exit(1)

    # .env ga qo'yish uchun ko'rsatma
    print("\n" + "=" * 60)
    print("KEYINGI QADAM:")
    print("=" * 60)
    print("1. Yuqoridagi hash ni nusxalang")
    print("2. .env faylini oching")
    print("3. ADMIN_PASS qiymatini yangilang:")
    print(f"\n   ADMIN_PASS={hashed}")
    print("\n4. Serverni qayta ishga tushiring")
    print("=" * 60)


if __name__ == "__main__":
    main()
