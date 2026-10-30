"""Aggregate counts for the school dashboard (proposal 0004), with k-anonymity.

A school sees only counts for a group of children, never a child's level, insight or
identity. A group's numbers are shown only when enough children consented, so no single
child can be inferred. This module is pure: it takes the per-child levels and support flags
the service gathered and returns the counts that may leave, nothing that points to a child.
"""

from dataclasses import dataclass

from app.risk.schemas import Level

# A group's counts are shown only at this many consenting children; the more sensitive
# "needs support" count needs a larger group. Defaults from proposal 0004.
K_MIN = 5
SUPPORT_K_MIN = 10


@dataclass(frozen=True)
class GroupCounts:
    """Counts for one group (a class, or a whole school). When suppressed, no number is
    shown because the group is too small to stay anonymous."""

    total: int
    suppressed: bool
    by_level: dict[str, int] | None  # None when suppressed
    support: int | None  # None when suppressed or the group is below SUPPORT_K_MIN


def aggregate_group(
    levels: list[Level],
    support_flags: list[bool],
    *,
    k: int = K_MIN,
    support_k: int = SUPPORT_K_MIN,
) -> GroupCounts:
    """Counts per level for the consenting children in one group. Below `k` children the
    whole group is suppressed; the support count needs `support_k`."""
    total = len(levels)
    if total < k:
        return GroupCounts(total=total, suppressed=True, by_level=None, support=None)
    by_level = {lvl.value: 0 for lvl in Level}
    for lvl in levels:
        by_level[lvl.value] += 1
    support = sum(1 for s in support_flags if s) if total >= support_k else None
    return GroupCounts(total=total, suppressed=False, by_level=by_level, support=support)
