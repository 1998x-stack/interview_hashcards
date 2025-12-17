"""
Card Hasher - Content-addressable card identification
Cards are identified by their content hash, not arbitrary IDs
"""

import hashlib


class CardHasher:
    """
    Implements content-addressable card identification
    
    Design principle: Cards are identified by what they are, not where they are
    This enables:
    - Automatic deduplication
    - Safe editing (hash changes = new card)
    - Git-friendly tracking
    """
    
    @staticmethod
    def hash_card(content: str) -> str:
        """
        Generate a hash for card content
        
        Args:
            content: Raw card text (Q: ... A: ... or C: ...)
            
        Returns:
            SHA-256 hash as hex string (first 16 chars for brevity)
        """
        # Normalize whitespace to make hashing robust
        normalized = ' '.join(content.split())
        
        # Use SHA-256 for cryptographic quality
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        
        # Return first 16 characters (64 bits) - sufficient for collision resistance
        return hash_obj.hexdigest()[:16]
    
    @staticmethod
    def hash_file(filepath: str) -> str:
        """
        Generate hash for entire file
        Useful for detecting deck changes
        """
        with open(filepath, 'rb') as f:
            file_hash = hashlib.sha256(f.read())
        return file_hash.hexdigest()[:16]