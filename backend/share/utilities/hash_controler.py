from argon2 import PasswordHasher

def hash_password(password):
    """
    Hash a password for storing.
    """
    ph = PasswordHasher(hash_len=32)
    return ph.hash(password)

def verify_password(hashed_password, password):
    """
    Verify a stored password against one provided by user
    """
    ph = PasswordHasher()
    try:
        ph.verify(hashed_password, password)
        return True
    except Exception as e:
        return False