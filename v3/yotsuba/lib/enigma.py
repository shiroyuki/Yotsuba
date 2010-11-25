import base64
from yotsuba.core import base

class CryptoException(Exception):
    pass

class CryptoIOException(Exception):
    pass

def encrypt(obj_ref):
    if not base.isString(obj_ref):
        raise CryptoIOException()
    return base64.b64encode(obj_ref)

def decrypt(obj_ref):
    if not base.isString(obj_ref):
        raise CryptoIOException()
    return base64.b64decode(obj_ref)