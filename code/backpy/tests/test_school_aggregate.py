"""k-anonymity for the school aggregate (proposal 0004): a group too small shows no
numbers, the support count needs a larger group, and only counts ever leave."""

from app.risk.schemas import Level
from app.school.aggregate import K_MIN, SUPPORT_K_MIN, aggregate_group


def _levels(n_aman=0, n_perhatian=0, n_waspada=0, n_mendesak=0):
    return (
        [Level.AMAN] * n_aman
        + [Level.PERHATIAN] * n_perhatian
        + [Level.WASPADA] * n_waspada
        + [Level.MENDESAK] * n_mendesak
    )


def test_group_below_k_is_suppressed():
    levels = _levels(n_aman=2, n_waspada=2)  # 4 < 5
    g = aggregate_group(levels, [False] * 4)
    assert g.suppressed and g.by_level is None and g.support is None
    assert g.total == 4


def test_group_at_k_shows_level_counts_but_not_support():
    levels = _levels(n_aman=3, n_perhatian=1, n_mendesak=1)  # 5 == K_MIN
    g = aggregate_group(levels, [True, False, False, False, True])
    assert not g.suppressed
    assert g.by_level == {"aman": 3, "perhatian": 1, "waspada": 0, "mendesak": 1}
    assert g.support is None  # below SUPPORT_K_MIN


def test_support_count_shows_at_support_k():
    levels = _levels(n_aman=8, n_waspada=2)  # 10 == SUPPORT_K_MIN
    flags = [False] * 7 + [True, True, True]
    g = aggregate_group(levels, flags)
    assert not g.suppressed
    assert g.support == 3
    assert g.by_level["waspada"] == 2


def test_counts_never_carry_identity():
    # The result is only ints and level names; nothing in it points to a child.
    g = aggregate_group(_levels(n_aman=K_MIN), [False] * K_MIN)
    assert isinstance(g.by_level, dict)
    assert all(isinstance(v, int) for v in g.by_level.values())
    assert set(g.by_level) == {"aman", "perhatian", "waspada", "mendesak"}


def test_thresholds_are_the_agreed_defaults():
    assert K_MIN == 5 and SUPPORT_K_MIN == 10
