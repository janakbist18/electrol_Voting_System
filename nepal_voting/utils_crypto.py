from __future__ import annotations

from dataclasses import dataclass
from cryptography.fernet import Fernet

@dataclass(frozen=True)
class CryptoBox:
    fernet: Fernet

    def encrypt_text(self, s: str) -> str:
        return self.fernet.encrypt(s.encode("utf-8")).decode("utf-8")

    def decrypt_text(self, token: str) -> str:
        return self.fernet.decrypt(token.encode("utf-8")).decode("utf-8")