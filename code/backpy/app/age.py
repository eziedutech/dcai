"""Age ranges of the children dcAI Guardian is built for: upper primary to senior high.

A child profile stores a range, never a date of birth. The synthetic scenarios keep the
older ranges they were written with (app.scenarios.schema.AgeRange); prompts take the
range as plain text, so both work with the same models.
"""

from enum import StrEnum


class AgeRange(StrEnum):
    A10_12 = "10-12"
    A13_15 = "13-15"
    A16_17 = "16-17"
