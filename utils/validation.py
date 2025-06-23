import re
import html

def sanitize_input(input_string):
    """
    Sanitize input to prevent potential injection or XSS
    """
    if not input_string:
        return ""

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>&\'"()]', '', input_string)

    # HTML escape for additional safety
    sanitized = html.escape(sanitized)

    return sanitized.strip()