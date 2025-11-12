# path: game_data/managed/addons.py

from enum import Enum

class Rarity(str, Enum):
    """Contains all the different rarities of items (weapons, armors, items,...).
    
    Attributes:
        value (constant): The constant representing the level of rarity.
        names (str): The color of the rarity. Follows the styling syntax of `InquirerPyStyle`.
    """
    COMMON = "bg:#ffd700 fg:white" # grey + white
    UNCOMMON = "bg:#32cd32 fg:white" # green + white
    RARE = "bg:#1338be fg:white" # blue + white
    EXCEPTIONAL = "bg:#8b008b fg:white" # purple + white
    LEGENDARY = "bg:#ffd700 fg:white" # gold + white
    MYTHIC = "bg:#81d9f1 fg:white" # cyan + white

class Element(str, Enum):
    FIRE = "fire"
    WATER = "water"
    ICE = "ice"
    EARTH = "earth"
    WIND = "wind"
    LIGHTNING = "lightning"
    LIGHT = "light"
    DARK = "dark"