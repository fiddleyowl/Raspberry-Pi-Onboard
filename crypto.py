from OpenSSL.crypto import FILETYPE_PEM, load_certificate, X509Store, X509StoreContext
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256

store = X509Store()

ca_certificate_bytes = open("Door_Lock_CA.crt", "rb")
ca_certificate = load_certificate(FILETYPE_PEM, ca_certificate_bytes.read())
store.add_cert(ca_certificate)


def verify_client_certificate(client_certificate_text):
    client_certificate_text = str(client_certificate_text)
    print(client_certificate_text)
    client_certificate_bytes = client_certificate_text.encode('utf-8')
    client_certificate = load_certificate(FILETYPE_PEM, client_certificate_bytes)
    store.add_cert(client_certificate)
    store_context = X509StoreContext(store, client_certificate)
    if store_context.verify_certificate() is None:
        return True
    else:
        return False


def verify_signature(message, signature, certificate):
    message = bytearray(message, "utf8")
    public_key = RSA.import_key(certificate)
    verifier = PKCS115_SigScheme(public_key)
    calculated_hash = SHA256.new(message)
    try:
        verifier.verify(calculated_hash, signature)
        return True
    except:
        return False


