def estimate_total_tokens(text):
    """
    This function estimates the total tokens output of a text to translate.
    It assumes an average of 5 characters per token (this is a rough estimate and the actual number can vary).
    """
    return len(text) / 5
