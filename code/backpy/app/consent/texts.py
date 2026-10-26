"""Consent text shown to the guardian. A consent record stores the version it agreed to,
so a published version is never edited: change the text by adding a new version.

Draft for the hackathon prototype. Final legal text needs review by counsel (spec 10).
"""

from dataclasses import dataclass
from enum import StrEnum


class Scope(StrEnum):
    PERCAKAPAN = "percakapan"  # conversation pattern analysis
    KEYBOARD = "keyboard"  # tone check of masked keyboard text on the server


@dataclass(frozen=True)
class ConsentText:
    version: str
    id: str
    en: str


_V1_ID = """\
Saya adalah orang tua atau wali sah dari anak ini, dan saya setuju dcAI mendampinginya.

Yang dilakukan dcAI:
- Pesan dinilai untuk mengenali pola yang berisiko. Data pribadi seperti nama, nomor, dan alamat disamarkan lebih dulu sebelum pesan dinilai model AI.
- Teks percakapan diproses di memori dan tidak disimpan. Yang disimpan adalah skor, level, jenis pola, dan insight.
- Untuk level mendesak, kutipan yang sudah disamarkan disimpan terenkripsi agar orang tua bisa bertindak, lalu dihapus otomatis setelah 14 hari.
- Anak menerima pengingat singkat dan penjelasan, dan dapat membaca halaman yang menjelaskan apa yang dibantu AI dan kapan orang tua diberi tahu.
- Orang tua menerima insight dan saran, bukan isi percakapan.

Penilaian AI adalah perkiraan dan bisa salah. Persetujuan dapat ditarik kapan saja, dan semua data anak dapat dihapus lewat Pengaturan.

Ruang lingkup yang saya setujui tercatat bersama versi teks ini dan waktu persetujuan.
"""

_V1_EN = """\
I am this child's parent or legal guardian, and I agree that dcAI may guide them.

What dcAI does:
- Messages are assessed to recognise risky patterns. Personal data such as names, numbers and addresses is masked before any AI model assesses a message.
- Conversation text is processed in memory and not stored. What is stored is the score, level, pattern types and insight.
- For the urgent level, masked excerpts are stored encrypted so a parent can act, and are deleted automatically after 14 days.
- The child receives short reminders with explanations, and can read a page that explains what the AI helps with and when parents are told.
- Parents receive insight and suggestions, not conversation content.

AI assessments are estimates and can be wrong. Consent can be withdrawn at any time, and all of the child's data can be deleted from Settings.

The scopes I agree to are recorded with this text version and the time of consent.
"""

CURRENT = ConsentText(version="2026-10-26.1", id=_V1_ID, en=_V1_EN)
VERSIONS: dict[str, ConsentText] = {CURRENT.version: CURRENT}
