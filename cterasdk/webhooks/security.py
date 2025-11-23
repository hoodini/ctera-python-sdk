"""
Webhook security utilities for signature verification.
"""

import hmac
import hashlib
import time
from typing import Optional


class WebhookSignatureVerifier:
    """
    Verifies webhook signatures to ensure authenticity.
    """
    
    def __init__(self, secret: str, algorithm: str = 'sha256'):
        """
        Initialize signature verifier.
        
        :param str secret: Shared secret for HMAC signing
        :param str algorithm: Hash algorithm (sha256, sha512, etc.)
        """
        self.secret = secret.encode('utf-8')
        self.algorithm = algorithm
    
    def generate_signature(self, payload: str, timestamp: Optional[int] = None) -> str:
        """
        Generate HMAC signature for payload.
        
        :param str payload: Payload to sign
        :param int timestamp: Unix timestamp (defaults to current time)
        :return: Hexadecimal signature string
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        message = f"{timestamp}.{payload}".encode('utf-8')
        signature = hmac.new(self.secret, message, getattr(hashlib, self.algorithm))
        return signature.hexdigest()
    
    def verify_signature(
        self,
        payload: str,
        signature: str,
        timestamp: int,
        tolerance: int = 300
    ) -> bool:
        """
        Verify webhook signature.
        
        :param str payload: Received payload
        :param str signature: Received signature
        :param int timestamp: Timestamp from webhook
        :param int tolerance: Maximum age of webhook in seconds (default: 5 minutes)
        :return: True if signature is valid and timestamp is within tolerance
        """
        # Check timestamp tolerance to prevent replay attacks
        current_time = int(time.time())
        if abs(current_time - timestamp) > tolerance:
            return False
        
        # Verify signature
        expected_signature = self.generate_signature(payload, timestamp)
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """
        Generate a random secret for webhook signing.
        
        :param int length: Length of secret in bytes
        :return: Hexadecimal secret string
        """
        import secrets
        return secrets.token_hex(length)

