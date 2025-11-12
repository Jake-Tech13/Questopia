# file: game_data/weapons.py
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Dict, Set, List, Mapping, Optional, Tuple

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.i18n import *
from utils.logger import Logger, get_logger
from managed.addons import *

log: Logger = get_logger(name=__name__, context="Weapons")

@dataclass
class LocalizedKeys:
    """Clés i18n; séparation nette entre data et textes."""
    cat_name_s: str = "dummy_category_name_s"  # category (singular) "weapons.missing_loc.category.dummy_name_s"
    cat_name_p: Optional[str] = "dummy_category_name_p"  # category (plural) "weapons.missing_loc.category.dummy_name_p"
    w_name: str = "dummy_weapon_name" # "weapons.missing_loc.weapon.dummy_name"
    w_description: Optional[str] = "dummy_weapon_description" # "weapons.missing_loc.weapon.dummy_description"

@dataclass
class Special:
    spec_gauge_amp: int
    spec_dmg: int
    
    def __post_init__(self) -> None:
        if self.spec_gauge_amp < 0:
            raise ValueError("spec_gauge_amp must be >= 0")
        if self.spec_dmg < 0:
            raise ValueError("spec_dmg must be >= 0")

@dataclass
class Elemental:
    element: str
    element_dmg: int
    round_duration: int
    element_dmg_amp_by_round: int
    
    def __post_init__(self) -> None:
        if self.element_dmg < 0:
            raise ValueError("element_dmg must be >= 0")
        if self.round_duration < 1:
            raise ValueError("round_duration must be >= 1")
        if self.element_dmg_amp_by_round < 0:
            raise ValueError("element_dmg_amp_by_round must be >= 0")

@dataclass
class Properties:
    rarity: Rarity = Rarity.COMMON
    price: int = 0
    special: Optional[Special] | None = None
    elemental: Optional[Elemental] | None = None
    
    def __post_init__(self) -> None:
        if self.price < 0:
            log.log_warning("WPN_PROPERTIES_WRN: weapon price must be >= 0. Defaulting value to 0.")
            self.price = 0
    
    # setters contrôlés (pour mutations runtime sûres)
    @property
    def price_value(self) -> int:
        return self.price
    
    @price_value.setter
    def price_value(self, value: int) -> None:
        if value < 0:
            raise ValueError("price must be >= 0")
        self.price = value
    
    def set_elemental(self, elemental: Optional[Elemental]) -> None:
        # why: atomique, valide l'objet passé
        self.elemental = elemental
    
    def set_special(self, special: Optional[Special]) -> None:
        self.special = special

@dataclass
class Stats:
    """
    Dataclass representing the stats of an `Weapon` object.
    
    Attributes:
        damage (int): The base amount of damage the weapon inflicts per attack. Defaults to 1 and cannot be negative. *Note: A value of 0 will therefore inflict no additional damage when calculating the total damage of an attack (excluding special modifiers that artificially add damage to the weapon).*
        defense (int): The base amount of damage the weapon can block per attack. Defaults to 1 and cannot be negative. *Note: A value of 0 will therefore block no additional damage when calculating the total damage sustained by an attack (excluding special modifiers that artificially add defense to the weapon).*
        speed (int): The base amount of speed the weapon adds/deducts from its host. The `speed` factor helps determine the attack order of combatants. Defaults to 0 and can be negative.
    """
    damage: int = 1
    """The base amount of damage the weapon inflicts per attack. Defaults to 1 and cannot be negative.\n
    *Note: A value of 0 will therefore inflict no additional damage when calculating the total damage of an attack (excluding special modifiers that artificially add damage to the weapon).
    """
    defense: int = 1
    """The base amount of damage the weapon can block per attack. Defaults to 1 and cannot be negative.\n
    *Note: A value of 0 will therefore block no additional damage when calculating the total damage sustained by an attack (excluding special modifiers that artificially add defense to the weapon).*
    """
    speed: int = 0
    """The base amount of speed the weapon adds/deducts from its host. Defaults to 0 and can be negative.\n
    The `speed` factor helps determine the attack order of combatants.
    """
    
    def __post_init__(self) -> None:
        if self.damage < 0:
            log.log_warning("WEAPON_STATS_ERROR: weapon damage must be >= 0")
        if self.defense < 0:
            log.log_warning("WEAPON_STATS_ERROR: weapon defense must be >= 0")
    
    def update(self, *, damage: Optional[int] = None, defense: Optional[int] = None, speed: Optional[int] = None) -> None:
        dmg = self.damage if damage is None else damage
        dfs = self.defense if defense is None else defense
        spd = self.speed if speed is None else speed
        if dmg < 0 or dfs < 0 or spd < 0:
            raise ValueError("stats must be >= 0")
        self.damage, self.defense, self.speed = dmg, dfs, spd

@dataclass
class Weapon:
    """Unité métier principale, indépendante du format JSON."""
    category: str = ""
    id: str = ""
    locales: LocalizedKeys = field(default_factory=LocalizedKeys)
    properties: Properties = field(default_factory=Properties)
    stats: Stats = field(default_factory=Stats)
    modifiers: Mapping[str, float] = field(default_factory=dict)
    hidden_mods: Set[str] = field(default_factory=set)
        
    def name(self, default: Optional[str] = None) -> str:
        return get_loc(self.locales.w_name, default=default or self.id)

    def description(self, default: str = "") -> str:
        return get_loc(self.locales.w_description, default=default)

w = Weapon()
CategoryLocales = Dict[str, LocalizedKeys]

class WeaponDB:
    """
    Easily access to weapons by their attributes, with loading and validation helpers.
    Structure interne: Dict[category, Dict[name, Weapon]]
    """
    def __init__(self) -> None:
        self._by_cat: Dict[str, Dict[str, Weapon]] = {}
    
    @staticmethod
    def validate_weapon(weapon: Weapon) -> Weapon:
        path = f"{weapon.category}.{weapon.id}"
        
        # Locales presence
        if not weapon.locales:
            log.log_warning(f"{path}: missing '$locales'. Parsing dummy implementation.")
            loc = LocalizedKeys
            loc.cat_name_p = "dummy_category"
            weapon.locales = LocalizedKeys()
        else:
            if not weapon.locales.w_name:
                log.log_warning(f"{path}: missing $locales.w_name")
            if not weapon.locales.w_description:
                log.log_warning(f"{path}: missing $locales.w_description")
        
        # Rarity
        if not weapon.properties.rarity in Rarity:
            log.log_error(f"{path}: invalid rarity '{weapon.properties.rarity}' (allowed: {sorted(Rarity)})")
        
        # Price
        if weapon.properties.price < 0:
            log.log_error(f"{path}: price must be >= 0 (got {weapon.properties.price})")
        
        # Stats
        if weapon.stats.damage < 0:
            log.log_error(f"{path}: stats.damage must be >= 0 (got {weapon.stats.damage})")
        if weapon.stats.defense < 0:
            log.log_error(f"{path}: stats.defense must be >= 0 (got {weapon.stats.defense})")
        if weapon.stats.speed < 0:
            log.log_error(f"{path}: stats.speed must be >= 0 (got {weapon.stats.speed})")
        
        # Special
        if weapon.properties.special:
            sp = weapon.properties.special
            if sp.spec_gauge_amp < 0:
                log.log_error(f"{path}: special.spec_gauge_amp must be >= 0 (got {sp.spec_gauge_amp})")
            if sp.spec_dmg < 0:
                log.log_error(f"{path}: special.spec_dmg must be >= 0 (got {sp.spec_dmg})")
        
        # Elemental
        if weapon.properties.elemental:
            el = weapon.properties.elemental
            if not el.element in Element:
                log.log_error(f"{path}: elemental.element '{el.element}' not in {sorted(Element)}")
            if el.element_dmg < 0:
                log.log_error(f"{path}: elemental.element_dmg must be >= 0 (got {el.element_dmg})")
            if el.round_duration < 1:
                log.log_error(f"{path}: elemental.round_duration must be >= 1 (got {el.round_duration})")
            if el.element_dmg_amp_by_round < 0:
                log.log_error(f"{path}: elemental.element_dmg_amp_by_round must be >= 0 (got {el.element_dmg_amp_by_round})")
        
        # Modifiers
        for k, v in weapon.modifiers.items():
            if not isinstance(v, float):
                log.log_error(f"{path}: modifier '{k}' must be a number (got {type(v).__name__})")
            if k.endswith("_rate_bonus") and not (0.0 <= v <= 1.0):
                log.log_warning(f"{path}: '{k}' is a rate; expected [0,1], got {v}")
            if k.endswith("_multiplier_bonus") and v < 0.0:
                log.log_warning(f"{path}: '{k}' negative multiplier? got {v}")
        
        # Hidden mods subset
        unknown_hidden = weapon.hidden_mods.difference(weapon.modifiers.keys())
        if unknown_hidden:
            log.log_warning(f"{path}: hidden_mods not present in modifiers: {sorted(unknown_hidden)}")
        
        return weapon
    
    @staticmethod
    def validate_categories_locales(categories: CategoryLocales) -> None:
        for cat, loc in categories.items():
            if not loc.cat_name_s:
                log.log_warning(f"{cat}: missing category $locales.cat_name_s")
            if not loc.cat_name_p:
                log.log_warning(f"{cat}: missing category $locales.cat_name_p")
    
    # =========================
    # Parsing/Loading depuis JSON (tolérant + messages)
    # =========================
    
    def load_weapons_tree(self, tree: Mapping[str, Any]) -> Tuple[List[Weapon], CategoryLocales]:
        """
        Convertit l'arbre JSON → objets Weapon + locales de catégories.
        - Ignore les armes invalides (champ requis manquant/type invalide).
        """
        weapons: List[Weapon] = []
        categories: CategoryLocales = {}
        
        for category, cat_obj in tree.items():
            if not isinstance(cat_obj, Mapping):
                log.log_error(f"{category}: category entry must be an object.")
                continue
            
            cat_loc = self._parse_category_locales(cat_obj.get("$locales"))
            categories[category] = cat_loc
            
            for wid, wobj in cat_obj.items():
                if wid == "$locales":
                    continue
                if not isinstance(wobj, Mapping):
                    log.log_error(f"{category}.{wid}: weapon entry must be an object.")
                    continue
                weapon = self._try_parse_weapon(category, wid, wobj)
                if weapon:
                    weapons.append(weapon)
        
        self.validate_categories_locales(categories)
        for w in weapons:
            self.validate_weapon(w)
        
        return weapons, categories
    
    def _try_parse_weapon(self, category: str, wid: str, wobj: Mapping[str, Any]) -> Optional[Weapon]:
        def fail(msg: str) -> None:
            log.log_error(f"{category}.{wid}: {msg}")
        
        wloc = self._parse_weapon_locales(wobj.get("$locales"))
        props_obj = wobj.get("properties") or {}
        stats_obj = wobj.get("stats") or {}
        mods_obj = wobj.get("modifiers") or {}
        hidden = self._coalesce_hidden_mods(wobj)
        
        if not isinstance(props_obj, Mapping):
            fail("properties must be an object.")
            return None
        if not isinstance(stats_obj, Mapping):
            fail("stats must be an object.")
            return None
        if not isinstance(mods_obj, Mapping):
            log.log_warning(f"{category}.{wid}: modifiers not an object; defaulting to empty.")
            mods_obj = {}
        
        rarity = Rarity(self._get_str(props_obj, "rarity", f"{category}.{wid}.properties.rarity").upper())
        price = self._get_int(props_obj, "price", f"{category}.{wid}.properties.price")
        if rarity is None or price is None:
            return None
        
        special = self._parse_special(props_obj.get("special"), f"{category}.{wid}.properties.special")
        elemental = self._parse_elemental(props_obj.get("elemental"), f"{category}.{wid}.properties.elemental")
        
        damage = self._get_int(stats_obj, "damage", f"{category}.{wid}.stats.damage")
        defense = self._get_int(stats_obj, "defense", f"{category}.{wid}.stats.defense")
        speed = self._get_int(stats_obj, "speed", f"{category}.{wid}.stats.speed")
        if damage is None or defense is None or speed is None:
            return None
        
        modifiers = self._parse_modifiers(mods_obj, f"{category}.{wid}.modifiers")
        
        return Weapon(
            category=category,
            id=wid,
            locales=wloc,
            properties=Properties(rarity=rarity, price=price, special=special, elemental=elemental),
            stats=Stats(damage=damage, defense=defense, speed=speed),
            modifiers=modifiers,
            hidden_mods=hidden,
        )
    
    def _parse_category_locales(self, obj: Any) -> LocalizedKeys:
        if not isinstance(obj, Mapping):
            return LocalizedKeys()
        return LocalizedKeys(
            cat_name_s=self._get_str_safe(obj, "cat_name_s"),
            cat_name_p=self._get_str_safe(obj, "cat_name_p"),
        )
    
    def _parse_weapon_locales(self, obj: Any) -> LocalizedKeys:
        if not isinstance(obj, Mapping):
            return LocalizedKeys()
        return LocalizedKeys(
            w_name=self._get_str_safe(obj, "w_name"),
            w_description=self._get_str_safe(obj, "w_description"),
        )
    
    def _parse_special(self, obj: Any, path: str) -> Optional[Special]:
        if obj is None:
            log.log_info(f"{path}: special was declared as null.")
            return None
        if not isinstance(obj, Mapping):
            log.log_exception(f"{path}: special must be a dictionary or null.")
            raise Exception(TypeError)
        amp = self._get_int(obj, "spec_gauge_amp", f"{path}.spec_gauge_amp")
        dmg = self._get_int(obj, "spec_dmg", f"{path}.spec_dmg")
        if amp is None:
            log.log_warning(f"{path}: special is not null but special.spec_gauge_amp was declared as null. Defaulting value to 0.")
            amp = 0
        if dmg is None:
            log.log_warning(f"{path}: special is not null but special.spec_dmg was declared as null. Defaulting value to 0.")
            dmg = 0
        log.log_info(f"")
        return Special(spec_gauge_amp=amp, spec_dmg=dmg)
    
    def _parse_elemental(self, obj: Any, path: str) -> Optional[Elemental]:
        if obj is None:
            log.log_info(f"{path}: elemental was declared as null.")
            return None
        if not isinstance(obj, Mapping):
            log.log_error(f"{path}: elemental must be a dictionary or null.")
            raise Exception(TypeError)
        element = self._get_str(obj, "element", f"{path}.element")
        element_dmg = self._get_int(obj, "element_dmg", f"{path}.element_dmg")
        round_duration = self._get_int(obj, "round_duration", f"{path}.round_duration")
        amp_by_round = self._get_int(obj, "element_dmg_amp_by_round", f"{path}.element_dmg_amp_by_round")
        if element is None:
            log.log_warning(f"{path}: elemental.element was declared as an empty string. Defaulting value to 0.")
            element = ""
        return Elemental(
            element=element,
            element_dmg=element_dmg,
            round_duration=round_duration,
            element_dmg_amp_by_round=amp_by_round,
        )
    
    @staticmethod
    def _parse_modifiers(obj: Mapping[str, Any], path: str) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for k, v in obj.items():
            if isinstance(v, (int, float)):
                out[k] = float(v)
            else:
                log.log_error(f"{path}.{k}: modifier value must be number (got {type(v).__name__})")
        return out
    
    @staticmethod
    def _coalesce_hidden_mods(wobj: Mapping[str, Any]) -> Set[str]:
        raw = wobj.get("hiden_mods", wobj.get("hidden_mods", []))
        if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
            return set()
        return {str(x) for x in raw}
    
    @staticmethod
    def _get_str(obj: Mapping[str, Any], key: str, path: str) -> str:
        val = obj.get(key)
        if isinstance(val, str):
            return val
        log.log_error(f"{path}: expected string, got {type(val).__name__}")
        raise Exception(TypeError)
    
    @staticmethod
    def _get_int(obj: Mapping[str, Any], key: str, path: str) -> int:
        val = obj.get(key)
        if isinstance(val, int):
            return val
        log.log_error(f"{path}: expected int, got {type(val).__name__}")
        raise Exception(TypeError)
    
    @staticmethod
    def _get_str_safe(obj: Mapping[str, Any], key: str) -> str:
        """Return the string value from the given key (if found) based on the mapping provided."""
        if key not in obj:
            raise KeyError(f"Key '{key}' not found in mapping.")
        
        val = obj[key]
        if val is None:
            raise ValueError(f"Value for key '{key}' cannot be None.")
        if not isinstance(val, str):
            raise TypeError(f"Expected str for key '{key}', got {type(val).__name__}.")        
        return val
    