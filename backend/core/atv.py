# atv.py (refactored for RSA signatures)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey


def load_private_key(path: str, passphrase: str = None) -> RSAPrivateKey:
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=passphrase.encode() if passphrase else None,
        )


def load_public_key(path: str) -> RSAPublicKey:
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def sign_request(message: str, private_key: RSAPrivateKey) -> bytes:
    return private_key.sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def verify_signature(message: str, signature: bytes, public_key: RSAPublicKey) -> bool:
    try:
        public_key.verify(
            signature,
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False
