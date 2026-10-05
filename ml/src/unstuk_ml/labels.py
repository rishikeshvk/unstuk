"""The label contract from docs/m3-labelling-guide.md, in code."""

# Unstuk can't help, so the reply is the polite decline (guide section 7).
OUT_OF_SCOPE = "out_of_scope"

# Kept out of seeds, training and dev data to measure zero-shot accuracy (guide section 10).
HELD_OUT = frozenset({"screen_wont_rotate", "wrong_time", "cant_hear_call"})

# The right reply is a clarifying question; scored by "not confident" (guide section 8).
VAGUE = "vague"

# Proxy test set slices (M3 spec section 5).
SLICES = frozenset(
    {
        "plain",
        "paraphrase",
        "typo",
        "collision",
        "negation",
        "oos_near",
        "long_story",
        "indian_english",
        "short_vague",
        "multi",
    }
)
