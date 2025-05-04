# File: utils.py - Utility functions
# Author: Adam Valík <xvalik05@stud.fit.vut.cz>

color_codes = {
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
}

def color_print(message: str, color: str = "green", additional_text: str = ""):
    print("\033[" + color_codes[color] + "m" + message + "\033[0m" + additional_text)
