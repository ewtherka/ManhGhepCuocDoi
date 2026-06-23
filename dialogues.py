DIALOG_LINES = {
    #fate — {"quote", "speaker", "effect"}
    "fate_philosopher": {"quote": "When we give someone our time, we actually give a portion of our life that we will never take back.", "speaker": "Alexander the Great",  "effect": "Time shall stand still for two turns hence."},
    "fate_seer":        {"quote": "Will the future bring your wisdom to me?",                                                           "speaker": "Michel de Nostredame", "effect": "All Chance blocks upon the board are gathered unto thee."},
    "fate_sage":        {"quote": "As you cannot do what you want, want what you can do.",                                              "speaker": "Leonardo da Vinci",    "effect": "Thy craft yields double reward for two turns."},
    "fate_thief":       {"quote": "No one should be discouraged who can make constant progress, even though it be slow.",               "speaker": "Plato",                "effect": "Five tokens of thy craft are taken from thee."},
    "fate_brute":       {"quote": "Ich liebe den Verrat, aber ich hasse den Verraeter.",                                               "speaker": "Gaius Julius Caesar",  "effect": "Five tokens of fortune are struck from thy count."},
    "fate_prisoner":    {"quote": "Time crumbles things; everything grows old and is forgotten through the lapse of Time.",             "speaker": "Aristoteles",          "effect": "Time flows twofold in thy favour for two turns."},

    #0=handicraft, 1=military, 2=forge — {"lines"}
    "hobby_state_1": {
        0: {"lines": ["A fondness for cloth and thread hath taken root within thy heart."]},
        1: {"lines": ["A love of mock battle and war-play hath stirred within thy breast."]},
        2: {"lines": ["A delight in gathering stones of the earth hath blossomed within thee."]},
    },
    "hobby_state_2": {
        0: {"lines": ["Thou hast resolved to become a craftsman of great skill and renown."]},
        1: {"lines": ["Thou hast sworn to walk the path of a valiant soldier."]},
        2: {"lines": ["Thou hast set thy will upon becoming a master of the forge."]},
    },
    "hobby_state_3": {
        0: {"lines": ["Alas. Thy hands are fit only for the work of a nameless apprentice."]},
        1: {"lines": ["So it must be. Thou shalt serve as a footman rather than a warrior."]},
        2: {"lines": ["The forge's door is shut to thee. Thou art naught but a bellows-hand."]},
    },

    #0=love, 1=religious, 2=mastermind — {"lines"}
    "chance_state_1": {
        0: {"lines": ["Thou hast met the love of thy life — the daughter of a wealthy merchant in the land. Whither shall this affair lead thee?"]},
        1: {"lines": ["Knock, knock. A stranger appeareth at thy door, calling himself a cleric from the East, seeking thy aid in gathering new followers to his cause."]},
        2: {"lines": ["By fortune's hand, thou didst save the King from an assassin's blade, and wast duly appointed as his Royal Chamberlain."]},
    },

    #age — {"lines"}
    "stage_1": {"lines": ["Thou hast grown into a lively and restless child."]},
    "stage_2": {"lines": ["Wonder stirs within thee — thou art now a curious and keen-eyed youth."]},
    "stage_3": {"lines": ["A new chapter of life openeth before thee, full of ambition and hope."]},
    "stage_4": {"lines": ["Thou enterest the years of middle age. The final road doth beckon."]},

    # ── ENDINGS — integer keys khớp với hàm endings() ─────────────── #

    # call_type=0: DIALOG_LINES[0][hobby_state][hobby_type]
    0: {
        2: {  # hobby_state=2 (thắng lần đầu)
            0: {"header": "A master is born.", "lines": ["Thy nimble fingers hath shaped wonders beyond measure. The finest craftsman in all the land — that is what thou hast become."]},
            1: {"header": "Steel and glory.", "lines": ["Steel in thy heart, fire in thy eyes — thou hast risen to become a warrior of great renown."]},
            2: {"header": "The forge singeth thy name.", "lines": ["Master of iron and flame — none can match the craft of thy hands. The forge doth bear thy legend."]},
        },
        3: {  # hobby_state=3 (thắng sau khi thất bại)
            0: {"header": "Hard-won glory.", "lines": ["Though the road was not without stumble, thy hands hath found their calling. A craftsman of respectable skill and honest toil."]},
            1: {"header": "A soldier forged in hardship.", "lines": ["Thou hast earned thy place among the soldiers, though not without struggle. A loyal fighter, true to the last."]},
            2: {"header": "Soot and pride.", "lines": ["Through sweat and soot, thou hast forged not only metal, but a life worthy of pride."]},
        },
    },

    # call_type=1: DIALOG_LINES[1][random_wheel_result][chance_type]
    1: {
        "copper": {
            0: {"header": "A love torn apart.", "lines": ["Her family never approved. The door was shut in your face, and the heartbreak never healed. You spent the rest of your days drinking and gambling away what little was left."]},
            1: {"header": "The offering.", "lines": ["The cleric smiled as the villagers gathered around you. Too late, you understood — you were not a helper. You were the sacrifice."]},
            2: {"header": "Executed at dawn.", "lines": ["You joined the uprising, believing in the cause. When it failed, the King showed no mercy. You were the first name on the list."]},
        },
        "gold": {
            0: {"header": "A life well lived.", "lines": ["You married her and never looked back. Years passed in quiet happiness — a warm home, a full heart, and someone always beside you until the very end."]},
            1: {"header": "Leader of the flock.", "lines": ["The congregation grew, and in time you became their leader. A small village, a humble life — but every soul there called you their shepherd."]},
            2: {"header": "The King's most trusted.", "lines": ["Of all the King's men, none stood closer than you. You whispered in his ear, shaped his decisions, and lived in comfort and honor to a ripe old age."]},
        },
    },

    # call_type=2: DIALOG_LINES[2][hobby_type or chance_type or 4]
    2: {
        0: {"header": "A life chasing a dream.", "lines": ["You never stopped trying. Not even when the money ran out. Some days you ate, some days you didn't — but the dream was always there, just out of reach."]},
        1: {"header": "Always one step behind.", "lines": ["You kept reaching back for a life that had already moved on. No matter how far you ran, the past was faster. You never truly lived in the present."]},
        2: {"header": "A flame that never caught.", "lines": ["You chased power and purpose all your life, never settling, never arriving. The fire inside you burned bright — but it burned alone."]},
        4: {"header": "Lost in the middle of it all.", "lines": ["No calling. No stroke of luck. Just one ordinary day after another. You lived, and that was all — a quiet life that left no mark and asked for none."]},
    },
}

ABOUT_TEXT = (
    "MATCH3PY",
    "Based on Tomas Gonzalez Aragon's MATCH3PY project.\nInspired by QuickTurtle's LIFE CRUSH STORY.\n Instructor: MSc.Pham Nguyen Truong An\nTeam member:\n-Trinh Nguyen Cat Tuong (25522036)\n-Nguyen Khanh Van (25522051)\n-Do Hai Yen (25522133)"
)
