"""
Message templates for scheduled messages.

This module provides templates for commonly used scheduled messages
with placeholder support for personalization.
"""

import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

# Basic templates with placeholders
TEMPLATES = {
    "medication_reminder": {
        "en": "Hello {name}, this is a reminder to take your {medication} {dosage}.",
        "lt": "Sveiki {name}, primename išgerti {medication} {dosage}."
    },
    "appointment_reminder": {
        "en": "Hello {name}, reminder: your appointment is scheduled for {date} at {time}.",
        "lt": "Sveiki {name}, priminimas: jūsų vizitas numatytas {date} {time}."
    },
    "check_in": {
        "en": "Hello {name}, how are you feeling today? Any concerns or questions?",
        "lt": "Sveiki {name}, kaip šiandien jaučiatės? Ar turite kokių nors nusiskundimų ar klausimų?"
    },
    "follow_up": {
        "en": "Hello {name}, checking in after your recent visit. How are you doing?",
        "lt": "Sveiki {name}, teirauojamės po jūsų paskutinio vizito. Kaip jaučiatės?"
    }
}

def get_template(template_key: str, language: str = "en") -> Optional[str]:
    """
    Get a message template by its key.
    
    Args:
        template_key: The template identifier
        language: The language code (default: en)
        
    Returns:
        The template string or None if not found
    """
    if template_key not in TEMPLATES:
        logger.warning(f"Template not found: {template_key}")
        return None
    
    if language not in TEMPLATES[template_key]:
        # Fall back to English if requested language not available
        logger.warning(f"Language {language} not available for template {template_key}, using English")
        language = "en"
    
    return TEMPLATES[template_key][language]

def format_message(template: str, parameters: Dict[str, Any]) -> str:
    """
    Format a message template with the provided parameters.
    
    Args:
        template: The template string
        parameters: Dictionary of parameters to substitute
        
    Returns:
        The formatted message
    """
    # Simple placeholder substitution
    formatted = template
    
    for key, value in parameters.items():
        placeholder = f"{{{key}}}"
        formatted = formatted.replace(placeholder, str(value))
    
    # Check if any placeholders remain unfilled
    if re.search(r'\{[a-zA-Z0-9_]+\}', formatted):
        logger.warning(f"Some placeholders remain unfilled in message: {formatted}")
    
    return formatted

def get_formatted_message(template_key: str, parameters: Dict[str, Any], language: str = "en") -> str:
    """
    Get a formatted message using a template.
    
    Args:
        template_key: The template identifier
        parameters: Dictionary of parameters to substitute
        language: The language code (default: en)
        
    Returns:
        The formatted message
    """
    template = get_template(template_key, language)
    
    if not template:
        # Return a generic message if template not found
        return f"Reminder for {parameters.get('name', 'patient')}"
    
    return format_message(template, parameters) 