from InquirerPy.prompts.checkbox import CheckboxPrompt as Iq_checkbox
from InquirerPy.prompts.confirm import ConfirmPrompt as Iq_confirm
from InquirerPy.prompts.expand import ExpandPrompt as Iq_expand
from InquirerPy.prompts.filepath import FilePathPrompt as Iq_filepath
from InquirerPy.prompts.fuzzy import FuzzyPrompt as Iq_fuzzy
from InquirerPy.prompts.input import InputPrompt as Iq_text
from InquirerPy.prompts.list import ListPrompt as Iq_select
from InquirerPy.prompts.number import NumberPrompt as Iq_number
from InquirerPy.prompts.rawlist import RawlistPrompt as Iq_rawlist
from InquirerPy.prompts.secret import SecretPrompt as Iq_secret
import InquirerPy.utils as Iq_utils

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.customText import CustomText as ct

from typing import Iterable, List, Optional, Tuple, Union, Dict, Any, Callable
from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import StyleAndTextTuples, to_formatted_text
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Frame

Choice = Union[
    Tuple[str, Any, str],    # (label, value, rarity)
    Dict[str, Any],          # {"name": str, "value": Any, "rarity": str}
]

RARITY_STYLES = {
    "legendary": "bg:yellow fg:black",
    "epic":      "bg:magenta fg:white",
    "rare":      "bg:ansiblue fg:white",
    "uncommon":  "bg:ansigreen fg:black",
    "common":    "bg:#444444 fg:white",
}

def _normalize_choices(choices: Iterable[Choice]) -> List[Tuple[str, Any, str]]:
    norm: List[Tuple[str, Any, str]] = []
    for ch in choices:
        if isinstance(ch, dict):
            name = ch.get("name")
            value = ch.get("value", name)
            rarity = ch.get("rarity", "common").lower()
        else:
            # tuple
            if len(ch) == 2:
                name, value = ch # type: ignore
                rarity = "common"
            else:
                name, value, rarity = ch
                rarity = (rarity or "common").lower()
        if rarity not in RARITY_STYLES:
            rarity = "common"
        norm.append((str(name), value, rarity))
    return norm

def select_with_dynamic_pointer(
    message: str,
    choices: Iterable[Choice],
    pointer: str = "❯",   # look Inquirer
    pointer_pad: int = 1, # espace après le pointer
    hint: Optional[str] = None,  # ex: "(↑/↓ pour naviguer, Entrée pour valider)"
) -> Any:
    """
    UI façon Inquirer (pointer ❯), rendu prompt_toolkit.
    Couleur de la ligne sélectionnée = dépend de la 'rarity' du choix.
    Retourne la 'value' du choix, ou None si échappé.
    """
    items = _normalize_choices(choices)
    if not items:
        return None
    
    index = 0
    result_container = {"value": None}
    
    # Style global (bordures sobres)
    base_style = Style.from_dict({
        "frame.border": "fg:#666666",
        "frame.label": "fg:#aaaaaa",
        # couleurs par défaut pour le texte “non sélectionné”
        "item": "fg:#dddddd",
        "hint": "fg:#888888 italic",
    })
    
    # Construction du contenu formaté (rafraîchi à chaque rendu)
    def build_lines() -> StyleAndTextTuples:
        lines: StyleAndTextTuples = []
        if message:
            lines.append(("class:item", message))
            lines.append(("", "\n"))
        if hint:
            lines.append(("class:hint", hint))
            lines.append(("", "\n\n"))
        
        for i, (label, _value, rarity) in enumerate(items):
            is_sel = (i == index)
            if is_sel:
                # ligne survolée: pointer + style de rareté
                style = RARITY_STYLES[rarity]
                lines.append((style, f"{pointer}{' ' * pointer_pad}{label}"))
            else:
                # ligne normale: pas de pointer, léger indent
                lines.append(("class:item", f"{' ' * (len(pointer)+pointer_pad)}{label}"))
            lines.append(("", "\n"))
        # enlever le dernier \n pour l'esthétique
        if lines and lines[-1][1].endswith("\n"):
            lines[-1] = (lines[-1][0], lines[-1][1][:-1])
        return lines
    
    control = FormattedTextControl(
        text=lambda: to_formatted_text(build_lines()),
        focusable=True
    )
    window = Window(content=control, dont_extend_height=False)
    root = Frame(
        title="Sélection",
        body=Box(HSplit([window]), padding=0)
    )
    
    kb = KeyBindings()
    
    @kb.add("up")
    def _(event):
        nonlocal index
        index = (index - 1) % len(items)
        get_app().invalidate()
    
    @kb.add("down")
    def _(event):
        nonlocal index
        index = (index + 1) % len(items)
        get_app().invalidate()
    
    @kb.add("enter")
    def _(event):
        # Valider: retourner la value de l'item sélectionné
        result_container["value"] = items[index][1]
        event.app.exit()
    
    @kb.add("escape")
    def _(event):
        # Annuler
        result_container["value"] = None
        event.app.exit()
    
    app = Application(
        layout=Layout(root, focused_element=window),
        key_bindings=kb,
        mouse_support=False,
        full_screen=True,
        erase_when_done=True,
        style=base_style,
    )
    app.run()
    return result_container["value"]

def menu_inventaire():
    objets = [
        ("Épée du Phénix", "epee", "legendary"),
        ("Bouclier Azur", "bouclier", "rare"),
        ("Potion", "potion", "common"),
        ("Retour", "retour", "common"),
    ]
    choix = select_with_dynamic_pointer(
        message="Inventaire :",
        choices=objets,
        hint="↑/↓ naviguer — Entrée valider — Échap annuler",
    )
    print("Choix:", choix)

# ---------------------------
# EXEMPLE D'UTILISATION
# ---------------------------
if __name__ == "__main__":
    menu_inventaire()
    print("Après (l’écran principal n’a pas été sali).")