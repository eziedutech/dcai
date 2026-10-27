"""Consent text shown to the guardian. A consent record stores the version it agreed to,
so a published version is never edited: change the text by adding a new version.

Draft for the hackathon prototype. Final legal text needs review by counsel (spec 10).
"""

from dataclasses import dataclass
from enum import StrEnum


class Scope(StrEnum):
    PERCAKAPAN = "percakapan"  # screen text read on the phone; flagged messages, masked
    KEYBOARD = "keyboard"  # tone check of masked keyboard text on the server
    GAMBAR = "gambar"  # images judged on the phone; only labels are stored
    DOMAIN = "domain"  # sites matched on the phone; only the category of a flagged site
    SUARA = "suara"  # voice notes in risky chats transcribed, masked, then assessed


@dataclass(frozen=True)
class ConsentText:
    version: str
    id: str
    en: str
    # The scopes this text explains. A grant may only name these.
    scopes: tuple[Scope, ...]


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

_V2_ID = """Saya adalah orang tua atau wali sah dari anak ini. Saya memasang dcAI Guardian di ponselnya dan setuju dcAI mendampinginya.

Yang dilakukan dcAI, per ruang lingkup:
- Percakapan: teks di layar ponsel anak diproses di ponsel itu. Hanya pesan yang ditandai berisiko yang dikirim ke server, setelah nama, nomor, alamat, dan data pribadi lain disamarkan. Server menilai polanya; teks diproses di memori dan tidak disimpan. Yang disimpan adalah skor, level, jenis pola, nama aplikasi tempat percakapan terjadi, dan insight.
- Gambar: gambar dinilai di ponsel. Gambar yang terdeteksi sensitif dikaburkan penuh dan tidak pernah dikirim. Gambar lain yang perlu dinilai lebih jauh dikirim dalam ukuran kecil setelah wajah dan teks pribadi dikaburkan. Yang disimpan hanya labelnya.
- Situs: situs yang dibuka dicocokkan dengan daftar di ponsel. Yang dikirim hanya kategori situs yang ditandai, bukan riwayat penjelajahan.
- Suara: pesan suara di percakapan berisiko diubah menjadi teks, disamarkan, lalu dinilai seperti pesan lain. Rekaman suara tidak disimpan.
- Papan ketik (opsional): nada teks yang diketik diperiksa setelah disamarkan.

Penilaian memakai model AI dari Meta yang dijalankan oleh penyedia inferensi. Yang dikirim ke model selalu sudah disamarkan.

Untuk level mendesak, kutipan yang sudah disamarkan disimpan terenkripsi agar orang tua bisa bertindak, lalu dihapus otomatis setelah 14 hari.

Anak selalu tahu dcAI aktif: ada notifikasi tetap di ponsel dan halaman yang menjelaskan apa yang dibantu AI dan kapan orang tua diberi tahu. Tidak ada mode tersembunyi. Orang tua menerima insight dan saran, bukan isi percakapan atau gambar. Bila perlindungan dimatikan di ponsel, orang tua diberi tahu.

Penilaian AI adalah perkiraan dan bisa salah. Setiap ruang lingkup dapat ditarik kapan saja, dan ponsel berhenti memakainya. Semua data anak dapat dihapus lewat Pengaturan.

Ruang lingkup yang saya setujui tercatat bersama versi teks ini dan waktu persetujuan.
"""

_V2_EN = """I am this child's parent or legal guardian. I am installing dcAI Guardian on their phone and I agree that dcAI may guide them.

What dcAI does, per scope:
- Conversations: text on the child's screen is processed on the phone. Only messages flagged as risky are sent to the server, after names, numbers, addresses and other personal data are masked. The server assesses the pattern; text is processed in memory and not stored. What is stored is the score, level, pattern types, the name of the app where the chat happened, and insight.
- Images: images are judged on the phone. An image detected as sensitive is fully blurred and never sent. Other images that need a closer look are sent at a small size after faces and personal text are blurred. Only the label is stored.
- Sites: sites that are opened are matched against a list on the phone. Only the category of a flagged site is sent, not the browsing history.
- Voice: voice notes in risky chats are turned into text, masked, then assessed like other messages. Recordings are not stored.
- Keyboard (optional): the tone of typed text is checked after masking.

Assessments use AI models from Meta run by inference providers. What is sent to a model is always masked first.

For the urgent level, masked excerpts are stored encrypted so a parent can act, and are deleted automatically after 14 days.

The child always knows dcAI is on: a persistent notification on the phone and a page that explains what the AI helps with and when parents are told. There is no hidden mode. Parents receive insight and suggestions, not conversation content or images. If protection is turned off on the phone, the parent is told.

AI assessments are estimates and can be wrong. Each scope can be withdrawn at any time, and the phone stops using it. All of the child's data can be deleted from Settings.

The scopes I agree to are recorded with this text version and the time of consent.
"""

V1 = ConsentText(
    version="2026-10-26.1",
    id=_V1_ID,
    en=_V1_EN,
    scopes=(Scope.PERCAKAPAN, Scope.KEYBOARD),
)
CURRENT = ConsentText(version="2026-10-28.1", id=_V2_ID, en=_V2_EN, scopes=tuple(Scope))
VERSIONS: dict[str, ConsentText] = {t.version: t for t in (V1, CURRENT)}
