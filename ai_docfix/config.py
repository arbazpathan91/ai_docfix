import os

_api_key = None

def set_api_key(key):
    """Set the API key programmatically."""
    global _api_key
    _api_key = key

def get_api_key():
    """Get the API key from environment or programmatic setting."""
    global _api_key
    
    if _api_key:
        return _api_key
    
    return os.getenv('GOOGLE_API_KEY')
