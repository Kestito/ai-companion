import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: The name for the logger. If None, returns the root logger.
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if logger doesn't have any
    if not logger.handlers:
        # Configure logging format
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s [%(name)s] api_variant=local_dev'
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Set default level
        logger.setLevel(logging.INFO)
    
    return logger 