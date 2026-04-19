"""
Security Utilities
==================
Functions for preventing prompt injection and other security issues.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

# Common prompt injection patterns
INJECTION_PATTERNS = [
    # Direct instruction overrides
    r'ignore\s+(?:previous|all|above|prior)\s+(?:instructions?|prompts?|rules?)',
    r'forget\s+(?:everything|all|previous|above)',
    r'disregard\s+(?:previous|all|above|prior)',
    
    # Role manipulation
    r'you\s+are\s+now\s+(?:a|an)\s+\w+',
    r'act\s+as\s+(?:a|an)\s+\w+',
    r'pretend\s+(?:to\s+be|you\s+are)',
    r'roleplay\s+as',
    r'simulate\s+(?:being|a|an)',
    
    # System message injection
    r'system\s*:',
    r'assistant\s*:',
    r'human\s*:',
    r'user\s*:',
    r'<\s*/?system\s*>',
    r'<\s*/?assistant\s*>',
    r'<\s*/?human\s*>',
    r'<\s*/?user\s*>',
    
    # Newline injection attempts
    r'\\n\\n(?:system|assistant|human|user)\s*:',
    r'\n\n(?:system|assistant|human|user)\s*:',
    
    # Jailbreak attempts
    r'jailbreak',
    r'break\s+out\s+of',
    r'escape\s+(?:your|the)\s+(?:constraints?|rules?)',
    
    # Developer mode attempts
    r'developer\s+mode',
    r'debug\s+mode',
    r'admin\s+mode',
    r'god\s+mode',
    
    # Prompt leaking
    r'show\s+(?:me\s+)?(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)',
    r'what\s+(?:are\s+)?(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)',
    r'repeat\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)',
]

def detect_injection(text: str) -> bool:
    """
    Detect potential prompt injection attempts.
    
    Args:
        text: User input to check
        
    Returns:
        True if injection patterns detected, False otherwise
    """
    if not text:
        return False
        
    text_lower = text.lower()
    
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
            logger.warning(f"Potential injection detected: {pattern}")
            return True
    
    return False

def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user input by removing potentially dangerous content.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
        
    Raises:
        ValueError: If input is invalid or contains injection attempts
    """
    if not text or not text.strip():
        raise ValueError("Input cannot be empty")
    
    text = text.strip()
    
    if len(text) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")
    
    if detect_injection(text):
        raise ValueError("Invalid input detected")
    
    # Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    
    return text

def validate_kb_name(kb_name: str) -> str:
    """
    Validate knowledge base name.
    
    Args:
        kb_name: Knowledge base name to validate
        
    Returns:
        Validated KB name
        
    Raises:
        ValueError: If KB name is invalid
    """
    if not kb_name:
        raise ValueError("Knowledge base name cannot be empty")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', kb_name):
        raise ValueError("Invalid knowledge base name format")
    
    if len(kb_name) > 50:
        raise ValueError("Knowledge base name too long")
    
    return kb_name

def rate_limit_key(user_id: str, endpoint: str) -> str:
    """Generate rate limiting key for user and endpoint."""
    return f"rate_limit:{user_id}:{endpoint}"

# Security headers for responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
}