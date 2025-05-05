class TextUtils:
    @staticmethod
    def truncate_by_complete_lines(text: str, max_length: int) -> str:
        """
        Truncate text to a maximum length while ensuring we don't cut in the middle of a line.
        
        Args:
            text: The input text to truncate
            max_length: Maximum length of the truncated text
            
        Returns:
            Truncated text ending with a complete line
        """
        if len(text) <= max_length:
            return text
            
        # First truncate to max_length
        truncated = text[:max_length]
        # Find the last newline
        last_newline = truncated.rfind('\n')
        
        # If no newline found, return the truncated text as is
        if last_newline == -1:
            return truncated
            
        # Return text up to the last complete line
        return truncated[:last_newline + 1]
