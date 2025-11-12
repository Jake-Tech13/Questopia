### Vous trouverez ici un exemple de la structure JSON à employer pour définir de nouvelles armes afin de pouvoir les manipuler dans le jeu par la suite.

#### Une documentation détaillée expliquant le rôle des différents champs possibles est également disponible.

---

Voici un exemple complet de la définition d'une arme provenant directement du fichier de données `game_data/assets/weapons.json` :
```json
{
    "sword": {
        "$locales": {
            "name_s": "weapons.sword.name_s",
            "name_p": "weapons.sword.name_p"
        },

        "copper_sword": {
            "$locales": {
                "name": "weapons.sword.copper_sword.name",
                "description": "weapons.sword.copper_sword.description"
            },
            "properties": {                
                "rarity": "common",
                "element": null,
                "price": 300
            },
            "stats": {
                "damage": 12,
                "defense": 5,
                "magic_dmg": 0,
                "element_dmg": 0
            },
            "modifiers": {
                "crit_rate_bonus": 0.05,
                "crit_multiplier_bonus": 0.15,
                "health_bonus": 5
            }
        }
    }
}
```

### Explications des différents champs :

### `"sword": {...}`

> <u>**Rôle :**</u>
> **`Catégorie`** de l'arme (ici, il s'agit de la catégorie "sword", ou "épée" en français).<br>
> Ce champ contiendra (de préférence) toutes les définitions et futures définitions d'épées utilisables dans le jeu.
> 
> <u>**Définition :**</u>
> Ce champ a pour but de simplifier l'organisation des armes dans le fichier de données ainsi que leur utilisation dans le code.<br>
> Toute arme doit obligatoirement être définie dans une **`Catégorie`**, sans quoi elle ne sera pas reconnue ni comptabilisée par le jeu.
> 
> <u>**Remarque :**</u>
> Rien n'empêche de définir à l'intérieur d'une **`Catégorie`** une arme s'apparentant à un autre type d'arme (autre que l'épée dans le cas présent), telle qu'une "Hache celeste" ou un "Marteau nordique", mais il est fortement conseillé de respecter la cohérence structurelle et nominative déjà établie pour faciliter au maximum la logique et la lisibilité, et pour éviter les erreurs humaines pouvant ensuite découler de cette approche.
> 
> <u>**Utilisation :**</u>
> Une **`Catégorie`** d'arme est une clé (autrement appelé un "**champ**") portant comme valeur un dictionnaire contenant toutes les définitions des armes de cette catégorie.<br>
> 
> Par exemple, dans la paire clé/valeur `"sword": {...}`, `"sword"` est la clé, `{...}` est la valeur et `:` est le signe séparant la valeur de cette clé (on peut voir ça comme le signe `=` permettant l'association d'une valeur à une variable).<br>
> 
> Par conséquent, **cette paire clé/valeur doit toujours être définie dans le premier nesting level (niveau d'accolades) du fichier JSON**, sinon elle ne sera pas considéré comme une catégorie et des erreurs en pagaille surviendront.<br>
> 
> Plusieurs **`Catégories`** peuvent facilement être définies les unes après les autres en les séparant de cette manière :
> 
> ```
> {
>     "sword": { ... }, # ATTENTION: n'oubliez pas les virgules entre chaque catégorie !
>     "dagger": { ... }, 
>     "hammer": { ... }, # pour la toute dernière catégorie, la virgule n'est pas obligatoire
>     ...
> }
> ```
> 
> A noter qu'on préfère définir les catégories en minuscules, au singulier et en anglais afin de simplifier la gestion des données dans le code.
> Si le nom d'une catégorie est faite de plusieurs mots (ex: "long_sword"), l'underscore ( _ ) fera office de séparateur.<br>
> Par la suite lors de la lecture des données, le nom des catégories sera dans tous les cas converti en minuscules. Un message d'avertissement sera loggé (dans un fichier texte créé dans le dossier `logs` sous le format `log_hh-mm-ss_DD-MM-YYYY.txt`) si une catégorie ne suit pas ces conventions, mais l'exécution du code se poursuivra normalement.<br>
> Dans le cas où un doublon de catégorie est détecté (par exemple, "sword" est définie deux fois ou plus), tous les champs contenus dans les catégories seront fusionnés automatiquement dans la première définition de cette catégorie avant d'être mis en mémoire et un avertissement sera loggé.<br>
> En revanche, une exception sera levée si des accents et symboles sont présents dans le nom des catégories, et celles concernées seront entièrement ignorées.

### `"copper_sword": {...}`
> <u>**Rôle :**</u>
> ID de l'arme (utile pour la gestion en interne).<br>
> Ce champ doit être unique dans toute la base de données des armes.<br>
> C'est à l'intérieur de ce nesting qu'on définira les attributs de l'arme.
>
> <u>**Définition :**</u>
> 
> 
> Même convention syntaxique que pour le nom des catégories (en minuscules, au > singulier, en anglais, sans accents/symboles et underscore comme séparateur).
> Les mêmes avertissements et exceptions s'appliquent ici aussi en cas de non-respect des conventions.
> En cas de doublon d'ID, seule la première définition de l'arme sera comptabilisée, les suivantes seront ignorées et une exception sera levée.
> Une arme peut contenir deux champs obligatoires et un optionnel :
>     - "properties": {...} (obligatoire)
>     - "stats": {...} (obligatoire)
>     - "modifiers": {...} (optionnel)
> Si l'un des deux champs obligatoires est manquant, une exception sera levée lors du chargement des données et des valeurs par défaut seront > utilisées pour chacun des champs obligatoires de "properties" et "stats".
> Plusieurs armes peuvent facilement être définies les unes après les autres à la même manière que les catégories :
> {
>     "sword": {
>         "copper_sword": { ... },
>         "iron_sword": { ... },
>         "steel_sword": { ... },
>         ...
>     }
> }
> L'ID de l'arme est prévu pour être utilisé à la fois dans le code mais aussi dans les fichiers de langue afin de permettre au jeu d'afficher le nom > correct de l'arme dans la langue choisie par le joueur.
> Si aucun nom n'est défini pour l'arme dans le fichier de langue correspondant, l'ID sera affiché tel quel à la place.
> 