"""Training data storage management."""
import logging
import pickle
import os
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)

# Conditional imports for encryption
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    logger.warning("cryptography package not installed. Install with: pip install cryptography")


class TrainingDataStorage:
    """Manages storage and retrieval of face encodings with optional encryption."""
    
    def __init__(self, encryption_key: Optional[bytes] = None, enable_encryption: bool = False):
        """Initialize storage.
        
        Args:
            encryption_key: Encryption key for securing face encodings
            enable_encryption: Whether to encrypt stored encodings
        """
        self.known_encodings: Dict[str, any] = {}  # Dictionary: student_id -> encoding
        self.known_ids: List[str] = []  # List of student IDs for backward compatibility
        self.enable_encryption = enable_encryption and HAS_CRYPTOGRAPHY
        
        if self.enable_encryption:
            if encryption_key is None:
                # Generate a new key if none provided
                self.encryption_key = Fernet.generate_key()
                logger.warning("Generated new encryption key. Store this securely!")
                logger.info(f"Encryption key: {self.encryption_key.decode()}")
            else:
                self.encryption_key = encryption_key
            
            self.cipher = Fernet(self.encryption_key)
            logger.info("Encryption enabled for face encodings")
        else:
            self.cipher = None
            if enable_encryption and not HAS_CRYPTOGRAPHY:
                logger.warning("Encryption requested but cryptography package not available")
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data if encryption is enabled.
        
        Args:
            data: Raw data bytes
            
        Returns:
            Encrypted data or original data if encryption disabled
        """
        if self.cipher:
            return self.cipher.encrypt(data)
        return data
    
    def _decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data if encryption is enabled.
        
        Args:
            data: Encrypted data bytes
            
        Returns:
            Decrypted data or original data if encryption disabled
        """
        if self.cipher:
            try:
                return self.cipher.decrypt(data)
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                raise
        return data
    
    def add_encoding(self, student_id: str, encoding) -> None:
        """Add or update face encoding for a student."""
        self.known_encodings[student_id] = encoding
        if student_id not in self.known_ids:
            self.known_ids.append(student_id)
    
    def get_encoding(self, student_id: str) -> Optional[any]:
        """Get face encoding for a student."""
        return self.known_encodings.get(student_id)
    
    def remove_encoding(self, student_id: str) -> bool:
        """Remove face encoding for a student."""
        if student_id in self.known_encodings:
            del self.known_encodings[student_id]
            if student_id in self.known_ids:
                self.known_ids.remove(student_id)
            return True
        return False
    
    def get_all_encodings(self) -> Dict[str, any]:
        """Get all stored encodings."""
        return self.known_encodings.copy()
    
    def get_all_ids(self) -> List[str]:
        """Get all stored student IDs."""
        return self.known_ids.copy()
    
    def clear(self) -> None:
        """Clear all stored encodings."""
        self.known_encodings.clear()
        self.known_ids.clear()
    
    def count(self) -> int:
        """Get count of stored encodings."""
        return len(self.known_encodings)
    
    def load_from_file(self, path: str) -> bool:
        """Load training data from file.
        
        Args:
            path: Path to training data file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    file_data = f.read()
                    
                    # Decrypt if encryption is enabled
                    decrypted_data = self._decrypt_data(file_data)
                    
                    # Unpickle the data
                    data = pickle.loads(decrypted_data)
                    
                    self.known_encodings = data.get('encodings', {})
                    self.known_ids = data.get('ids', list(self.known_encodings.keys()))
                    
                logger.info(f"Loaded {len(self.known_ids)} face encodings from {path}")
                return True
            else:
                logger.warning(f"Training data file not found: {path}")
                return False
        except Exception as e:
            logger.warning(f"Could not load training data: {e}")
            self.known_encodings = {}
            self.known_ids = []
            return False
    
    def save_to_file(self, path: str) -> bool:
        """Save training data to file.
        
        Args:
            path: Path to save training data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Pickle the data
            data = {
                'encodings': self.known_encodings,
                'ids': self.known_ids
            }
            pickled_data = pickle.dumps(data)
            
            # Encrypt if encryption is enabled
            encrypted_data = self._encrypt_data(pickled_data)
            
            # Write to file
            with open(path, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info(f"Saved {len(self.known_ids)} face encodings to {path}")
            return True
        except Exception as e:
            logger.error(f"Could not save training data: {e}")
            return False
    
    def get_encryption_key(self) -> Optional[bytes]:
        """Get the encryption key used by this storage.
        
        Returns:
            Encryption key bytes or None if encryption not enabled
        """
        if self.enable_encryption:
            return self.encryption_key
        return None
    
    def set_encryption_key(self, key: bytes) -> bool:
        """Set a new encryption key.
        
        Args:
            key: New encryption key
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_CRYPTOGRAPHY:
            logger.error("Cannot set encryption key: cryptography package not installed")
            return False
        
        try:
            self.encryption_key = key
            self.cipher = Fernet(key)
            self.enable_encryption = True
            logger.info("Encryption key updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to set encryption key: {e}")
            return False
