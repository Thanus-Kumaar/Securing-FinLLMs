#!/usr/bin/env python3
import argparse
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_rsa_keypair(private_path, public_path, passphrase=None):
    os.makedirs(os.path.dirname(private_path), exist_ok=True)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    if passphrase:
        enc = serialization.BestAvailableEncryption(passphrase.encode())
    else:
        enc = serialization.NoEncryption()

    # Write private key
    with open(private_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=enc,
            )
        )

    # Write public key
    public_key = private_key.public_key()
    with open(public_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="keys")
    parser.add_argument("--passphrase", default=None)
    args = parser.parse_args()

    priv = os.path.join(args.outdir, "private_key.pem")
    pub = os.path.join(args.outdir, "public_key.pem")

    generate_rsa_keypair(priv, pub, args.passphrase)
    print(f"Generated keys: {priv}, {pub}")
