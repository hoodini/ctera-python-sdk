"""Unit tests for the crypto module"""
import unittest
import os
import tempfile
from unittest import mock

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.hazmat.primitives import hashes

from cterasdk.lib.crypto import (
    RSAKeyPair, CryptoServices, PrivateKey, X509Certificate,
    create_certificate_chain, compare_certificates
)
from cterasdk.exceptions import CTERAException


class TestRSAKeyPair(unittest.TestCase):
    """Test cases for RSAKeyPair class"""

    def setUp(self):
        """Set up test fixtures"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        self.key_pair = RSAKeyPair(self.private_key, self.public_key)

    def test_public_key_property(self):
        """Test public key property returns bytes"""
        public_key_bytes = self.key_pair.public_key
        self.assertIsInstance(public_key_bytes, bytes)
        self.assertTrue(public_key_bytes.startswith(b'ssh-rsa'))

    def test_private_key_property(self):
        """Test private key property returns bytes"""
        private_key_bytes = self.key_pair.private_key
        self.assertIsInstance(private_key_bytes, bytes)
        self.assertTrue(private_key_bytes.startswith(b'-----BEGIN OPENSSH PRIVATE KEY-----'))

    def test_save_key_pair(self):
        """Test saving key pair to files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_filename = 'test_key'
            
            with mock.patch('cterasdk.lib.crypto.synfs.write') as mock_write:
                mock_write.side_effect = [
                    os.path.join(tmpdir, f'{key_filename}.pem'),
                    os.path.join(tmpdir, f'{key_filename}.pub')
                ]
                
                with mock.patch('os.chmod'):
                    self.key_pair.save(tmpdir, key_filename)
                
                self.assertEqual(mock_write.call_count, 2)
                # Check private key write
                self.assertEqual(mock_write.call_args_list[0][0][0], tmpdir)
                self.assertEqual(mock_write.call_args_list[0][0][1], f'{key_filename}.pem')
                # Check public key write
                self.assertEqual(mock_write.call_args_list[1][0][0], tmpdir)
                self.assertEqual(mock_write.call_args_list[1][0][1], f'{key_filename}.pub')


class TestCryptoServices(unittest.TestCase):
    """Test cases for CryptoServices class"""

    def test_generate_rsa_key_pair_default_params(self):
        """Test generating RSA key pair with default parameters"""
        key_pair = CryptoServices.generate_rsa_key_pair()
        
        self.assertIsInstance(key_pair, RSAKeyPair)
        self.assertIsNotNone(key_pair.public_key)
        self.assertIsNotNone(key_pair.private_key)

    def test_generate_rsa_key_pair_custom_size(self):
        """Test generating RSA key pair with custom key size"""
        key_pair = CryptoServices.generate_rsa_key_pair(key_size=4096)
        
        self.assertIsInstance(key_pair, RSAKeyPair)
        # Verify key is generated (we can't easily check exact size without internals)
        self.assertIsNotNone(key_pair.private_key)

    def test_generate_rsa_key_pair_custom_exponent(self):
        """Test generating RSA key pair with custom exponent"""
        key_pair = CryptoServices.generate_rsa_key_pair(exponent=3)
        
        self.assertIsInstance(key_pair, RSAKeyPair)
        self.assertIsNotNone(key_pair.private_key)

    def test_generate_and_save_key_pair(self):
        """Test generating and saving key pair"""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_filename = 'test_key'
            
            with mock.patch('cterasdk.lib.crypto.synfs.write') as mock_write:
                mock_write.side_effect = [
                    os.path.join(tmpdir, f'{key_filename}.pem'),
                    os.path.join(tmpdir, f'{key_filename}.pub')
                ]
                
                with mock.patch('os.chmod'):
                    public_key = CryptoServices.generate_and_save_key_pair(
                        key_filename, dirpath=tmpdir
                    )
                
                self.assertIsInstance(public_key, str)
                self.assertTrue(public_key.startswith('ssh-rsa'))

    def test_generate_and_save_key_pair_default_dir(self):
        """Test generating and saving key pair with default directory"""
        key_filename = 'test_key'
        
        with mock.patch('cterasdk.lib.crypto.commonfs.downloads') as mock_downloads:
            mock_downloads.return_value = '/mock/downloads'
            
            with mock.patch('cterasdk.lib.crypto.synfs.write') as mock_write:
                mock_write.side_effect = [
                    f'/mock/downloads/{key_filename}.pem',
                    f'/mock/downloads/{key_filename}.pub'
                ]
                
                with mock.patch('os.chmod'):
                    public_key = CryptoServices.generate_and_save_key_pair(key_filename)
                
                self.assertIsInstance(public_key, str)
                mock_downloads.assert_called_once()


class TestPrivateKey(unittest.TestCase):
    """Test cases for PrivateKey class"""

    def setUp(self):
        """Set up test fixtures"""
        self.rsa_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

    def test_pem_data_property(self):
        """Test PEM data property"""
        private_key = PrivateKey(self.rsa_key)
        pem_data = private_key.pem_data
        
        self.assertIsInstance(pem_data, bytes)
        self.assertTrue(pem_data.startswith(b'-----BEGIN RSA PRIVATE KEY-----'))

    def test_from_bytes(self):
        """Test loading private key from bytes"""
        # Use PEM format which is compatible with load_pem_private_key
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        pem_bytes = self.rsa_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.TraditionalOpenSSL,
            NoEncryption()
        )
        
        private_key = PrivateKey.from_bytes(pem_bytes)
        
        self.assertIsInstance(private_key, PrivateKey)
        self.assertIsNotNone(private_key.private_key)

    def test_from_string(self):
        """Test loading private key from string"""
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        pem_bytes = self.rsa_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.TraditionalOpenSSL,
            NoEncryption()
        )
        key_string = pem_bytes.decode('utf-8')
        
        private_key = PrivateKey.from_string(key_string)
        
        self.assertIsInstance(private_key, PrivateKey)
        self.assertIsNotNone(private_key.private_key)

    def test_load_private_key_from_bytes(self):
        """Test load_private_key with bytes"""
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        pem_bytes = self.rsa_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.TraditionalOpenSSL,
            NoEncryption()
        )
        
        private_key = PrivateKey.load_private_key(pem_bytes)
        
        self.assertIsInstance(private_key, PrivateKey)

    def test_load_private_key_from_string(self):
        """Test load_private_key with string"""
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        pem_bytes = self.rsa_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.TraditionalOpenSSL,
            NoEncryption()
        )
        key_string = pem_bytes.decode('utf-8')
        
        # Mock commonfs.exists to return False so it doesn't try to check if string is a file path
        with mock.patch('cterasdk.lib.crypto.commonfs.exists', return_value=False):
            private_key = PrivateKey.load_private_key(key_string)
        
        self.assertIsInstance(private_key, PrivateKey)

    def test_load_private_key_invalid(self):
        """Test load_private_key with invalid data"""
        with self.assertRaises(CTERAException) as context:
            PrivateKey.load_private_key('invalid key data')
        
        self.assertIn('Failed loading private key', str(context.exception))


class TestX509Certificate(unittest.TestCase):
    """Test cases for X509Certificate class"""

    def test_from_string(self):
        """Test loading certificate from string"""
        # Generate a real self-signed certificate for testing
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "testCA"),
        ])
        cert_obj = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        ).sign(key, hashes.SHA256())
        
        from cryptography.hazmat.primitives.serialization import Encoding
        cert_pem = cert_obj.public_bytes(Encoding.PEM).decode('utf-8')
        
        cert = X509Certificate.from_string(cert_pem)
        
        self.assertIsInstance(cert, X509Certificate)
        self.assertIsNotNone(cert.certificate)

    def test_load_certificate_invalid(self):
        """Test load_certificate with invalid data"""
        with self.assertRaises(CTERAException) as context:
            X509Certificate.load_certificate('invalid certificate data')
        
        self.assertIn('Failed loading certificate', str(context.exception))


class TestCertificateChain(unittest.TestCase):
    """Test cases for certificate chain functions"""

    def test_create_certificate_chain(self):
        """Test creating certificate chain"""
        # Create mock certificates
        cert1 = mock.MagicMock()
        cert1.subject = 'Subject1'
        cert1.issuer = 'Issuer1'
        
        cert2 = mock.MagicMock()
        cert2.subject = 'Issuer1'
        cert2.issuer = 'RootCA'
        
        # Test sorting
        result = create_certificate_chain(cert1, cert2)
        self.assertEqual(len(result), 2)

    def test_compare_certificates_child_parent(self):
        """Test comparing certificates where first is child of second"""
        cert_child = mock.MagicMock()
        cert_child.subject = 'Child'
        cert_child.issuer = 'Parent'
        
        cert_parent = mock.MagicMock()
        cert_parent.subject = 'Parent'
        cert_parent.issuer = 'Root'
        
        result = compare_certificates(cert_child, cert_parent)
        self.assertEqual(result, -1)

    def test_compare_certificates_parent_child(self):
        """Test comparing certificates where first is parent of second"""
        cert_parent = mock.MagicMock()
        cert_parent.subject = 'Parent'
        cert_parent.issuer = 'Root'
        
        cert_child = mock.MagicMock()
        cert_child.subject = 'Child'
        cert_child.issuer = 'Parent'
        
        result = compare_certificates(cert_parent, cert_child)
        self.assertEqual(result, 1)

    def test_compare_certificates_no_relation(self):
        """Test comparing certificates with no direct relation"""
        cert1 = mock.MagicMock()
        cert1.subject = 'Cert1'
        cert1.issuer = 'Root1'
        
        cert2 = mock.MagicMock()
        cert2.subject = 'Cert2'
        cert2.issuer = 'Root2'
        
        result = compare_certificates(cert1, cert2)
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()

