"""Ask dcAI: a parent asks in their own words, Muse Spark answers from the parent's own
dashboard data through function tools.

- The tools are the dashboard queries, scoped to the signed-in guardian. The assistant
  can never see more than the dashboard shows, and there is no message text to see.
- Children are aliases ("Anak A") in everything the model receives, including the
  parent's question; names are put back only in the answer shown to the parent.
- Tool arguments are validated here; the final text is cleaned and checked (no links, no
  phone-like numbers, no surveillance wording). A failure gives a fixed summary built by
  code from the same data.
- Nothing of the question, history or answer is stored or logged.
"""

import json
import logging
import re
import string
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.consent.service import active_scopes
from app.dashboard import queries
from app.db.base import utcnow
from app.db.models import ChildProfile, Guardian
from app.llm import LLMError, Usage
from app.privacy.mask import mask
from app.text import ModelText, no_contacts

log = logging.getLogger("dcai.ask")

MAX_TOOL_ROUNDS = 4
MAX_TOOL_RESULT_CHARS = 12_000
MAX_ANSWER_CHARS = 1800

SYSTEM = """\
Role: "Tanya dcAI", a calm assistant that helps a parent understand what dcAI noticed for \
their children. Answer in {language}.

Facts you must respect:
- You only know what the tools return: levels, behaviour patterns, events, insight and \
the state of the child's phone. dcAI never stores message text, so neither you nor the \
parent can read conversations. If asked for messages, say so kindly and offer what you can \
show instead.
- Children appear as aliases such as "Anak A". Use the alias exactly as given.
- Never invent events, dates, numbers or patterns. If the tools show \
nothing, say that nothing was recorded.
- Every assessment is an estimate and can be wrong.
- Today is {today} (UTC). Times in tool results are UTC. Write dates as words, such as \
"27 Oktober", and say "today" or "yesterday" only when the date shows it.

How to answer:
- Short: at most six sentences, or a short list with "- ". Plain text, no headings, no \
emoji, no long dashes.
- Supportive and practical: what was seen, why it matters, one or two next steps. Prefer \
the conversation starters and advice already in the insight.
- Never advise punishment, taking the phone away or reading the child's chats in secret.
- Never write a phone number, a website or an app to install. For danger, say to keep \
evidence, report through the platform and contact local authorities, and point to the \
help channels shown in the dashboard.
- For anything outside dcAI and healthy digital habits, say briefly that you can only help with \
dcAI insight."""


class AskTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: Annotated[str, StringConstraints(min_length=1, max_length=2000)]


class AskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=800)]
    # Earlier turns of this chat, kept by the browser only. The server stores nothing.
    history: list[AskTurn] = Field(default_factory=list, max_length=8)


# Dates and times are not phone numbers; they are set aside before the contact check.
_DATE_OR_TIME = re.compile(
    r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?)?"
    r"|\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{1,2}[.:]\d{2}\b"
)


def _no_contacts_except_dates(text: str) -> str:
    no_contacts(_DATE_OR_TIME.sub(" ", text))
    return text


class AskAnswer(BaseModel):
    answer: Annotated[
        ModelText,
        AfterValidator(_no_contacts_except_dates),
        StringConstraints(max_length=MAX_ANSWER_CHARS),
    ]


class AskOut(BaseModel):
    answer: str
    source: Literal["model", "fallback"]
    tools_used: list[str]
    is_estimate: bool = True


# ---------------------------------------------------------------- tools

Alias = Annotated[str, StringConstraints(pattern=r"^Anak [A-Z]$")]


class ChildArg(BaseModel):
    model_config = ConfigDict(extra="forbid")
    child: Alias


class ChildDaysArg(ChildArg):
    days: int = Field(default=7, ge=1, le=90)


class ChildLimitArg(ChildArg):
    limit: int = Field(default=5, ge=1, le=10)


class NoArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


HOW_DCAI_WORKS = {
    "on_the_phone": [
        "Screen text is read and masked on the child's phone; only flagged messages are sent.",
        "Images judged sensitive are fully blurred on the phone and never sent.",
        "The child sees a persistent notification; there is no hidden mode.",
    ],
    "stored": [
        "risk score and level",
        "pattern types",
        "events",
        "insight and advice",
        "the app name where a chat happened",
        "image labels, never images",
    ],
    "never_stored": ["message text", "images", "voice recordings", "browsing history"],
    "levels": {"aman": "0-29", "perhatian": "30-59", "waspada": "60-84", "mendesak": "85-100"},
    "models": "Muse Spark (Meta) assesses patterns and writes advice; Llama labels messages.",
    "parent_controls": ["withdraw any consent scope", "revoke the phone", "delete all data"],
}


@dataclass
class Context:
    db: Session
    guardian: Guardian
    aliases: dict[str, ChildProfile] = field(default_factory=dict)  # "Anak A" -> child

    @classmethod
    def load(cls, db: Session, guardian: Guardian) -> Context:
        children = db.scalars(
            select(ChildProfile)
            .where(ChildProfile.guardian_id == guardian.id)
            .order_by(ChildProfile.created_at, ChildProfile.id)
        ).all()
        letters = string.ascii_uppercase
        return cls(db, guardian, {f"Anak {letters[i]}": c for i, c in enumerate(children[:26])})

    def child(self, alias: str) -> ChildProfile | None:
        return self.aliases.get(alias)

    def names_to_alias(self, text: str) -> str:
        for alias, c in self.aliases.items():
            text = re.sub(rf"\b{re.escape(c.nickname)}\b", alias, text, flags=re.I)
        return text

    def to_alias(self, text: str) -> str:
        """Child names in the parent's text become aliases; other personal data is masked."""
        return mask(self.names_to_alias(text)).text

    def to_names(self, text: str) -> str:
        for alias, c in self.aliases.items():
            text = re.sub(rf"\b{re.escape(alias)}\b", c.nickname, text)
        return text


def _scrub(data: Any, ctx: Context) -> Any:
    """Tool output for the model: child ids, nicknames and names inside any text replaced
    by the alias."""
    by_id = {str(c.id): a for a, c in ctx.aliases.items()}
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if k == "child_id":
                out["child"] = by_id.get(str(v), "unknown")
            elif k == "nickname":
                continue
            else:
                out[k] = _scrub(v, ctx)
        return out
    if isinstance(data, list):
        return [_scrub(v, ctx) for v in data]
    if isinstance(data, str):
        # Names also hide in free text, such as a phone called "Ponsel Kit".
        return ctx.names_to_alias(data)
    return data


def _dump(models) -> Any:
    if isinstance(models, list):
        return [m.model_dump(mode="json") for m in models]
    return models.model_dump(mode="json")


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args: type[BaseModel]
    run: Callable[[Context, Any], Any]

    def spec(self) -> dict:
        schema = self.args.model_json_schema()
        schema.pop("title", None)
        return {
            "type": "function",
            "function": {"name": self.name, "description": self.description, "parameters": schema},
        }


def _with_child(fn):
    def run(ctx: Context, args):
        child = ctx.child(args.child)
        if child is None:
            return {"error": f"unknown child {args.child}", "children": list(ctx.aliases)}
        return fn(ctx, child, args)

    return run


TOOLS = [
    Tool(
        "list_children",
        "The parent's children: alias, age range and active consent scopes.",
        NoArgs,
        lambda ctx, _: [
            {
                "child": a,
                "age_range": c.age_range,
                "consent_scopes": sorted(active_scopes(ctx.db, c.id)),
            }
            for a, c in ctx.aliases.items()
        ],
    ),
    Tool(
        "get_overview",
        "Current level, counts of events by kind, phone protection state and the latest "
        "insight for one child over the last N days.",
        ChildDaysArg,
        _with_child(
            lambda ctx, c, a: _dump(queries.overview(ctx.db, c, a.days, ctx.guardian.language))
        ),
    ),
    Tool(
        "list_conversations",
        "Conversations with an assessment in the last N days: app, level, patterns, "
        "confidence and the explanation for the parent. Never message text.",
        ChildDaysArg,
        _with_child(lambda ctx, c, a: _dump(queries.conversations(ctx.db, c, a.days))),
    ),
    Tool(
        "list_events",
        "Events in the last N days, newest first, with level and time.",
        ChildDaysArg,
        _with_child(lambda ctx, c, a: _dump(queries.events(ctx.db, c, a.days, 50))),
    ),
    Tool(
        "list_insights",
        "Latest insight: what was seen, why it matters, conversation starters, do and "
        "don't, the nudge the child received and a one-minute lesson.",
        ChildLimitArg,
        _with_child(
            lambda ctx, c, a: _dump(queries.insights(ctx.db, c, a.limit, ctx.guardian.language))
        ),
    ),
    Tool(
        "how_dcai_works",
        "What dcAI does on the phone, what it stores and never stores, the levels, and the "
        "parent's controls.",
        NoArgs,
        lambda ctx, _: HOW_DCAI_WORKS,
    ),
]
_BY_NAME = {t.name: t for t in TOOLS}


def run_tool(ctx: Context, name: str, raw_args: str | None) -> Any:
    tool = _BY_NAME.get(name)
    if tool is None:
        return {"error": f"unknown tool {name}"}
    try:
        args = tool.args.model_validate(json.loads(raw_args or "{}"))
    except json.JSONDecodeError, ValidationError:
        return {"error": "invalid arguments", "expected": tool.args.model_json_schema()}
    return _scrub(tool.run(ctx, args), ctx)


# ---------------------------------------------------------------- the loop


@dataclass
class AskResult:
    out: AskOut
    usage: list[Usage]


async def ask(client, db: Session, guardian: Guardian, body: AskIn) -> AskResult:
    ctx = Context.load(db, guardian)
    language = "Indonesian" if guardian.language == "id" else "English"
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": SYSTEM.format(language=language, today=utcnow().date().isoformat()),
        },
        *({"role": t.role, "content": ctx.to_alias(t.content)} for t in body.history),
        {"role": "user", "content": ctx.to_alias(body.question)},
    ]
    specs = [t.spec() for t in TOOLS]
    used: list[str] = []
    usage: list[Usage] = []
    try:
        for _ in range(MAX_TOOL_ROUNDS + 1):
            raw, u = await client.chat_tools(
                purpose="ask", messages=messages, tools=specs, max_tokens=2000, timeout=45.0
            )
            usage.append(u)
            if not raw.tool_calls:
                answer = AskAnswer.model_validate({"answer": raw.content or ""}).answer
                log.info("ask_answered rounds=%d tools=%s", len(usage), ",".join(used) or "-")
                return AskResult(
                    AskOut(answer=ctx.to_names(answer), source="model", tools_used=used), usage
                )
            messages.append(
                {"role": "assistant", "content": raw.content, "tool_calls": list(raw.tool_calls)}
            )
            for call in raw.tool_calls:
                fn = call.get("function") or {}
                name = str(fn.get("name", ""))
                used.append(name)
                result = json.dumps(run_tool(ctx, name, fn.get("arguments")), ensure_ascii=False)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "content": result[:MAX_TOOL_RESULT_CHARS],
                    }
                )
        log.warning("ask_fallback reason=too_many_rounds")
    except ValidationError as exc:
        kinds = ",".join(sorted({e["type"] for e in exc.errors(include_input=False)}))
        log.warning("ask_fallback reason=invalid_answer problem=%s", kinds)
    except LLMError as exc:
        log.warning("ask_fallback reason=model_unavailable error=%s", type(exc).__name__)
    return AskResult(AskOut(answer=fallback(ctx), source="fallback", tools_used=used), usage)


_LEVEL_TEXT = {
    "id": {
        "aman": "aman",
        "perhatian": "perlu perhatian",
        "waspada": "waspada",
        "mendesak": "mendesak",
    },
    "en": {
        "aman": "safe",
        "perhatian": "needs attention",
        "waspada": "alert",
        "mendesak": "urgent",
    },
}


def fallback(ctx: Context) -> str:
    """A fixed summary from the dashboard data, used when the model cannot answer."""
    lang = "id" if ctx.guardian.language == "id" else "en"
    levels = _LEVEL_TEXT[lang]
    if not ctx.aliases:
        return (
            "Belum ada anak yang ditambahkan." if lang == "id" else "No child has been added yet."
        )
    lines = [
        "Tanya dcAI sedang tidak bisa menjawab. Ringkasan 7 hari terakhir:"
        if lang == "id"
        else "Ask dcAI cannot answer right now. Summary of the last 7 days:"
    ]
    for child in ctx.aliases.values():
        ov = queries.overview(ctx.db, child, 7, lang)
        events = sum(ov.events_by_kind.values())
        if lang == "id":
            lines.append(
                f"- {child.nickname}: level {levels[ov.level]}, {events} peristiwa, "
                f"{ov.conversations_needing_attention} percakapan perlu didampingi."
            )
        else:
            lines.append(
                f"- {child.nickname}: level {levels[ov.level]}, {events} events, "
                f"{ov.conversations_needing_attention} conversations need support."
            )
    return "\n".join(lines)
