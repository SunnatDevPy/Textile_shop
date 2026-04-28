import argparse
from pathlib import Path

import bcrypt


def check_single_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def check_passwords_from_file(file_path: str, password_hash: str) -> str | None:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    for line in path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if check_single_password(candidate, password_hash):
            return candidate
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check password(s) against bcrypt hash."
    )
    parser.add_argument(
        "--hash",
        required=True,
        help="Bcrypt hash, for example: $2b$12$...",
    )
    parser.add_argument(
        "--password",
        help="Single password candidate to test.",
    )
    parser.add_argument(
        "--wordlist",
        help="Path to file with candidate passwords (one per line).",
    )
    args = parser.parse_args()

    if not args.password and not args.wordlist:
        parser.error("Use --password or --wordlist.")

    if args.password:
        ok = check_single_password(args.password, args.hash)
        print("MATCH" if ok else "NO MATCH")
        return

    found = check_passwords_from_file(args.wordlist, args.hash)
    if found is None:
        print("NO MATCH IN WORDLIST")
    else:
        print(f"MATCH: {found}")


if __name__ == "__main__":
    main()
