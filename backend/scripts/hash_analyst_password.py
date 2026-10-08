import base64
import getpass
import hashlib
import secrets


def main() -> None:
    password = getpass.getpass("Analyst password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12 or password != confirmation:
        raise SystemExit("Passwords must match and contain at least 12 characters.")
    salt = secrets.token_bytes(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    print(f"pbkdf2_sha256${iterations}${encode(salt)}${encode(digest)}")


if __name__ == "__main__":
    main()
