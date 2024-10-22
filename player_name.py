def is_valid_player_name(text):
    """Check if the detected text is a valid player name."""
    # Strip leading and trailing whitespaces
    text = text.strip()

    # Exclude names that are digits or contain only symbols/numbers
    if text.isdigit() or any(char in text for char in '+0123456789'):
        return False

    # Require that the name has at least two characters
    if len(text) < 2:
        return False

    # Define allowed non-alphabetic characters in names
    allowed_chars = {"'", "-", "."}

    # Check that each character is either alphabetic, a space, or in the allowed set
    if not all(char.isalpha() or char.isspace() or char in allowed_chars for char in text):
        return False

    # Ensure no two special characters are next to each other (e.g., `O'-Connor` or `Dr..`)
    if any(text[i] in allowed_chars and text[i + 1] in allowed_chars for i in range(len(text) - 1)):
        return False

    return text  # Return the cleaned player name if valid