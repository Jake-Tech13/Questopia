class CustomText:
    """Allow to use custom text colors and formatting in strings."""
    # text colors
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    DARK_BLUE = '\033[34m'
    GREEN = '\033[92m'
    DARK_GREEN = '\033[32m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    DARK_RED = '\033[31m'
    MAGENTA = '\033[35m'
    ORANGE = '\033[38;5;208m'
    BLACK = '\033[30m'
    WHITE = '\033[37m'
    GREY = '\033[90m'
    DARK_GREY = '\033[38;5;240m'
    
    # special colors
    GOLD = '\033[38;5;220m'
    SILVER = '\033[38;5;250m'
    BRONZE = '\033[38;5;136m'
    
    # background colors
    BLACK_BG = '\033[40m'
    WHITE_BG = '\033[47m'
    
    # text formatting
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    REVERSED = '\033[7m'
    STRIKETHROUGH = '\033[9m'
    BLINK = '\033[5m'
    DIM = '\033[2m'
    HIDDEN = '\033[8m'
    
    # combinations of formatting
    BOLD_UNDERLINE = '\033[1;4m'
    BOLD_ITALIC = '\033[1;3m'
    BOLD_REVERSED = '\033[1;7m'
    BOLD_STRIKETHROUGH = '\033[1;9m'
    BOLD_BLINK = '\033[1;5m'
    BOLD_DIM = '\033[1;2m'
    BOLD_HIDDEN = '\033[1;8m'
    UNDERLINE_ITALIC = '\033[4;3m'
    UNDERLINE_REVERSED = '\033[4;7m'
    UNDERLINE_STRIKETHROUGH = '\033[4;9m'
    UNDERLINE_BLINK = '\033[4;5m'
    UNDERLINE_DIM = '\033[4;2m'
    UNDERLINE_HIDDEN = '\033[4;8m'
    ITALIC_REVERSED = '\033[3;7m'
    ITALIC_STRIKETHROUGH = '\033[3;9m'
    ITALIC_BLINK = '\033[3;5m'
    ITALIC_DIM = '\033[3;2m'
    ITALIC_HIDDEN = '\033[3;8m'
    REVERSED_STRIKETHROUGH = '\033[7;9m'
    REVERSED_BLINK = '\033[7;5m'
    REVERSED_DIM = '\033[7;2m'
    REVERSED_HIDDEN = '\033[7;8m'
    STRIKETHROUGH_BLINK = '\033[9;5m'
    STRIKETHROUGH_DIM = '\033[9;2m'
    STRIKETHROUGH_HIDDEN = '\033[9;8m'
    BLINK_DIM = '\033[5;2m'
    BLINK_HIDDEN = '\033[5;8m'
    BLINK_INVISIBLE = '\033[5;8m'
    DIM_HIDDEN = '\033[2;8m'
    
    # reset codes for formatting
    RESET_BOLD = '\033[22m'
    RESET_UNDERLINE = '\033[24m'
    RESET_ITALIC = '\033[23m'
    RESET_REVERSED = '\033[27m'
    RESET_STRIKETHROUGH = '\033[29m'
    RESET_BLINK = '\033[25m'
    RESET_DIM = '\033[22;2m'
    RESET_HIDDEN = '\033[28m'
    
    # reset codes for formatting combinations
    RESET_BOLD_UNDERLINE = '\033[22;24m'
    RESET_BOLD_ITALIC = '\033[22;23m'
    RESET_BOLD_REVERSED = '\033[22;27m'
    RESET_BOLD_STRIKETHROUGH = '\033[22;29m'
    RESET_BOLD_BLINK = '\033[22;25m'
    RESET_BOLD_DIM = '\033[22;22;2m'
    RESET_BOLD_HIDDEN = '\033[22;28m'
    RESET_UNDERLINE_ITALIC = '\033[24;23m'
    RESET_UNDERLINE_REVERSED = '\033[24;27m'
    RESET_UNDERLINE_STRIKETHROUGH = '\033[24;29m'
    RESET_UNDERLINE_BLINK = '\033[24;25m'
    RESET_UNDERLINE_DIM = '\033[24;22;2m'
    RESET_UNDERLINE_HIDDEN = '\033[24;28m'
    RESET_ITALIC_REVERSED = '\033[23;27m'
    RESET_ITALIC_STRIKETHROUGH = '\033[23;29m'
    RESET_ITALIC_BLINK = '\033[23;25m'
    RESET_ITALIC_DIM = '\033[23;22;2m'
    RESET_ITALIC_HIDDEN = '\033[23;28m'
    RESET_REVERSED_STRIKETHROUGH = '\033[27;29m'
    RESET_REVERSED_BLINK = '\033[27;25m'
    RESET_REVERSED_DIM = '\033[27;22;2m'
    RESET_REVERSED_HIDDEN = '\033[27;28m'
    RESET_STRIKETHROUGH_BLINK = '\033[29;25m'
    RESET_STRIKETHROUGH_DIM = '\033[29;22;2m'
    RESET_STRIKETHROUGH_HIDDEN = '\033[29;28m'
    RESET_BLINK_DIM = '\033[25;22;2m'
    RESET_BLINK_HIDDEN = '\033[25;28m'
    RESET_DIM_HIDDEN = '\033[22;2;28m'    
    
    # reset all formatting
    RESET = '\033[0m'
    """Reset all text formatting to default."""
    
    def format_money(self, amount: int, show_sign: bool = False) -> str:
        """
        Formats an amount with dots every 3 digits (e.g., 1.000.000).
        Adds a '+' in front if 'show_sign' is True and the amount is positive.

        Example:
            format_money(2500000)        → '2.500.000'
            format_money(2500000, True)  → '+2.500.000'
            format_money(-10000, True)   → '-10.000'
        """
        formatted = f"{amount:,}".replace(",", ".")
        if show_sign and amount >= 0:
            formatted = f"+{formatted}"
        return formatted

