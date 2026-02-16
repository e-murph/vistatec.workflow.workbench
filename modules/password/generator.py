import string
import secrets

def generate_passwords(amount, length, use_numbers, use_symbols):
    """
    Generates a list of secure passwords based on user constraints.
    Ensures at least one uppercase and one lowercase letter are always present.
    """
    passwords = []
    
    # 1. Define Character Sets
    letters_upper = string.ascii_uppercase
    letters_lower = string.ascii_lowercase
    digits = string.digits
    symbols = string.punctuation

    # 2. Build the Pool based on selection
    # We always include letters
    pool = letters_upper + letters_lower
    
    if use_numbers:
        pool += digits
    if use_symbols:
        pool += symbols

    for _ in range(amount):
        # A. Mandate Requirements (1 Upper + 1 Lower)
        pwd_chars = [
            secrets.choice(letters_upper),
            secrets.choice(letters_lower)
        ]

        # B. If user asked for numbers/symbols, should we force at least one?
        # The prompt implies strictly "Include" as an option for the pool, 
        # but let's just fill the rest randomly from the chosen pool.
        
        # Fill the remaining slots
        remaining_length = length - len(pwd_chars)
        
        for _ in range(remaining_length):
            pwd_chars.append(secrets.choice(pool))

        # C. Shuffle to avoid "Upper, Lower, ..." predictable pattern
        secrets.SystemRandom().shuffle(pwd_chars)
        
        # Join into string
        passwords.append("".join(pwd_chars))

    return passwords