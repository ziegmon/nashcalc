"""Static Street Fighter 6 reference data used to populate scenario context.

These are plain labels for the scenario-context dropdowns/radios; they have no
effect on the Nash calculation. Edit SF6_CHARACTERS when the roster changes.
"""

# Roster: base 18 + Year 1 + Year 2 + Year 3 DLC. Kept alphabetical.
SF6_CHARACTERS = [
    "A.K.I.",
    "Akuma",
    "Alex",
    "Blanka",
    "C. Viper",
    "Cammy",
    "Chun-Li",
    "Dee Jay",
    "Dhalsim",
    "E. Honda",
    "Ed",
    "Elena",
    "Guile",
    "Ingrid",
    "Jamie",
    "JP",
    "Juri",
    "Ken",
    "Kimberly",
    "Lily",
    "Luke",
    "M. Bison",
    "Mai",
    "Manon",
    "Marisa",
    "Rashid",
    "Ryu",
    "Sagat",
    "Terry",
    "Zangief",
]

# SF6 Drive Gauge has 6 bars; the Super Art gauge has 3 bars.
DRIVE_MAX = 6
SUPER_MAX = 3

POSITIONS = ["Midscreen", "Corner"]

# Jamie's Drink Level (0-4) is a character-specific resource, only shown when the
# selected character is Jamie.
JAMIE = "Jamie"
DRINK_MAX = 4
