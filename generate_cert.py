from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime

# Générer la clé privée
key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)

# Générer le certificat auto-signé
subject = issuer = x509.Name(
    [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Senegal"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Dakar"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MonEntreprise"),
        x509.NameAttribute(NameOID.COMMON_NAME, "192.168.43.160"),  # Ton IP locale
    ]
)

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([x509.DNSName("192.168.43.160")]),
        critical=False,
    )
    .sign(key, hashes.SHA256(), default_backend())
)

# Écrire key et cert
with open("key.pem", "wb") as f:
    f.write(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("Certificat cert.pem et clé key.pem générés !")
