"""Rules for any model-written text shown to people."""

import re
from typing import Annotated

from pydantic import AfterValidator

# No emdash anywhere (project rule). Model text is cleaned on the way out, the prompt also
# forbids it. En dash and horizontal bar are treated the same way.
_DASHES = re.compile("\\s*[\u2014\u2013\u2015]\\s*")
_SPACES = re.compile("[ \t\u00a0]+")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_URL = re.compile(r"(https?://|www\.|\b[a-z0-9-]+\.(com|id|org|net|go\.id|app)\b)", re.I)
_PHONE_LIKE = re.compile(r"\d[\d\s().-]{5,}\d")
# Surveillance framing is off-brand and off-mission (spec section 3).
_BANNED = re.compile(r"\b(memata-matai|surveilans|spyware|memonitor)\b", re.I)


# Indonesian reduplication is written with a hyphen ("hati-hati"). Models told to avoid
# dashes sometimes drop it ("hati hati"); a repeated word with a space is never right.
_REDUP = re.compile(r"\b([A-Za-z]{2,})( \1)\b", re.I)


def clean(text: str) -> str:
    text = _DASHES.sub(", ", text)
    text = _SPACES.sub(" ", text)
    text = _REDUP.sub(lambda m: f"{m.group(1)}-{m.group(2)[1:]}", text)
    return text.strip().replace(" ,", ",")


def sentence_count(text: str) -> int:
    return len([part for part in _SENTENCE_SPLIT.split(text.strip()) if part])


def _clean_and_check(text: str) -> str:
    text = clean(text)
    if not text:
        raise ValueError("empty text")
    if _BANNED.search(text):
        raise ValueError("surveillance wording")
    return text


def no_contacts(text: str) -> str:
    # Help lines and sites come from verified configuration, never from the model.
    if _URL.search(text):
        raise ValueError("model text must not contain links")
    if _PHONE_LIKE.search(text):
        raise ValueError("model text must not contain phone-like numbers")
    return text


ModelText = Annotated[str, AfterValidator(_clean_and_check)]
CoachText = Annotated[str, AfterValidator(_clean_and_check), AfterValidator(no_contacts)]
