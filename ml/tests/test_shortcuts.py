from records import make

from unstuk_ml.shortcuts import giveaways, profiles


def test_profiles_count_lines_words_and_first_words() -> None:
    records = [make("a", "hey no net"), make("b", "hey nothing loads")]

    [profile] = profiles(records)

    assert (profile.label, profile.count, profile.mean_words) == ("no_internet", 2, 3.0)
    assert profile.top_first_words == [("hey", 1.0)]


def test_finds_a_token_used_almost_only_under_one_label() -> None:
    records = [make(f"a{n}", "kindly fix the net") for n in range(20)]
    records += [make(f"b{n}", "fix the screen", "screen_too_dim") for n in range(20)]

    tokens = {(g.token, g.label) for g in giveaways(records)}

    assert ("kindly", "no_internet") in tokens
    assert ("fix",) not in {(t,) for t, _ in tokens}
