from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str):
    hashed = password_hash.hash(password)


def encode_jwt():
    pass


def verify_password():
    pass


def decode_jwt():
    pass
