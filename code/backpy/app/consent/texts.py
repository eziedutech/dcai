"""Consent text shown to the guardian. A consent record stores the version it agreed to,
so a published version is never edited: change the text by adding a new version.

Draft for the hackathon MVP. Final legal text needs review by counsel (spec 10).
"""

from dataclasses import dataclass
from enum import StrEnum


class Scope(StrEnum):
    PERCAKAPAN = "percakapan"  # screen text read on the phone; flagged messages, masked
    KEYBOARD = "keyboard"  # tone check of masked keyboard text on the server
    GAMBAR = "gambar"  # images judged on the phone; only labels are stored
    DOMAIN = "domain"  # sites matched on the phone; only the category of a flagged site
    SUARA = "suara"  # voice notes in risky chats transcribed, masked, then assessed
    WAKTU = "waktu"  # minutes per app category per day, counted on the phone; limits, bedtime
    LAYAR = "layar"  # screen text read across any app on the phone (accessibility); masked
    # Child counted in a class aggregate (proposal 0004). Offered from a later consent
    # version once the school flow ships; not in any published version's scopes yet.
    SEKOLAH = "sekolah"


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
- Suara: pesan suara di percakapan yang sudah berisiko dikirim ke layanan transkripsi Meta untuk diubah menjadi teks, lalu teksnya disamarkan dan dinilai seperti pesan lain. Rekaman suara diproses di memori dan tidak disimpan.
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
- Voice: a voice note in a chat that is already risky is sent to Meta's transcription service to be turned into text; the text is then masked and assessed like other messages. Recordings are processed in memory and not stored.
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
_V2_SCOPES = (Scope.PERCAKAPAN, Scope.KEYBOARD, Scope.GAMBAR, Scope.DOMAIN, Scope.SUARA)
V2 = ConsentText(version="2026-10-28.1", id=_V2_ID, en=_V2_EN, scopes=_V2_SCOPES)

# V3 states what the build does: text comes from chat apps with the dcAI SDK and from the
# dcAI keyboard, and images never leave the phone.
_V3_ID = _V2_ID.replace(
    "- Percakapan: teks di layar ponsel anak diproses di ponsel itu.",
    "- Percakapan: pesan di aplikasi chat yang memasang dcAI dan teks yang diketik dengan papan ketik dcAI diproses di ponsel anak.",
).replace(
    "- Gambar: gambar dinilai di ponsel. Gambar yang terdeteksi sensitif dikaburkan penuh dan tidak pernah dikirim. Gambar lain yang perlu dinilai lebih jauh dikirim dalam ukuran kecil setelah wajah dan teks pribadi dikaburkan. Yang disimpan hanya labelnya.",
    "- Gambar: gambar dinilai di ponsel dan tidak pernah dikirim. Gambar sensitif dikaburkan penuh. Wajah dan data pribadi pada gambar yang akan dibagikan anak dikaburkan. Teks pada gambar yang diterima di percakapan berisiko disamarkan lalu dinilai seperti pesan. Yang disimpan hanya labelnya. Bila dcAI salah mengaburkan, orang tua meninjaunya di ponsel anak dengan PIN; yang dikirim hanya catatan salah deteksi tanpa gambar.",
)
_V3_EN = _V2_EN.replace(
    "- Conversations: text on the child's screen is processed on the phone.",
    "- Conversations: messages in chat apps that integrate dcAI and text typed with the dcAI keyboard are processed on the child's phone.",
).replace(
    "- Images: images are judged on the phone. An image detected as sensitive is fully blurred and never sent. Other images that need a closer look are sent at a small size after faces and personal text are blurred. Only the label is stored.",
    "- Images: images are judged on the phone and never sent. A sensitive image is fully blurred. Faces and personal data in an image the child is about to share are blurred. Text in an image received in a risky chat is masked, then assessed like a message. Only the label is stored. If dcAI blurs by mistake, the parent reviews it on the child's phone with a PIN; only a note of the false detection is sent, without the image.",
)
V3 = ConsentText(version="2026-10-28.2", id=_V3_ID, en=_V3_EN, scopes=_V2_SCOPES)

# V4 adds time online: limits, bedtime and short-video breaks set by the parent.
_V4_ID = _V3_ID.replace(
    "- Papan ketik (opsional): nada teks yang diketik diperiksa setelah disamarkan.",
    "- Papan ketik (opsional): nada teks yang diketik diperiksa setelah disamarkan.\n"
    "- Waktu online: lama pemakaian aplikasi dihitung di ponsel per kategori (video, game, sosial, lainnya). "
    "Yang dikirim hanya total menit per kategori per hari, menit di jam tidur, dan sesi terpanjang; daftar aplikasi tetap di ponsel. "
    "Batas harian, jam tidur, dan jeda dari video pendek diatur orang tua, dan anak selalu melihat sisa waktunya. "
    "Anak dapat meminta tambahan waktu dengan alasan singkat yang disamarkan lalu dikirim ke orang tua.",
).replace(
    "Penilaian memakai model AI dari Meta yang dijalankan oleh penyedia inferensi. Yang dikirim ke model selalu sudah disamarkan.",
    "Penilaian memakai model AI dari Meta yang dijalankan oleh penyedia inferensi. Yang dikirim ke model selalu sudah disamarkan. "
    "Ringkasan mingguan, saran untuk permintaan waktu, dan usulan batas dibuat model AI dari angka agregat dan alasan yang sudah disamarkan; keputusan tetap di tangan orang tua.",
)
_V4_EN = _V3_EN.replace(
    "- Keyboard (optional): the tone of typed text is checked after masking.",
    "- Keyboard (optional): the tone of typed text is checked after masking.\n"
    "- Time online: app use is counted on the phone per category (video, games, social, other). "
    "Only the total minutes per category per day, minutes during bedtime and the longest session are sent; the list of apps stays on the phone. "
    "Daily limits, bedtime and breaks from short video are set by the parent, and the child always sees the time left. "
    "The child can ask for more time with a short reason, masked, then sent to the parent.",
).replace(
    "Assessments use AI models from Meta run by inference providers. What is sent to a model is always masked first.",
    "Assessments use AI models from Meta run by inference providers. What is sent to a model is always masked first. "
    "The weekly summary, advice on time requests and suggested limits are written by an AI model from aggregate numbers and masked reasons; the parent decides.",
)
_V4_SCOPES = (*_V2_SCOPES, Scope.WAKTU)
V4 = ConsentText(version="2026-10-28.3", id=_V4_ID, en=_V4_EN, scopes=_V4_SCOPES)

# V5 restores the screen-reading scope agreed in proposal 0002: dcAI reads screen text
# across any app (accessibility) and assesses a screenshot of a risky chat on the phone.
# The keyboard and chat-notification paths stay as complements, not the only sources.
_V5_ID = _V4_ID.replace(
    "- Percakapan: pesan di aplikasi chat yang memasang dcAI dan teks yang diketik dengan papan ketik dcAI diproses di ponsel anak.",
    "- Percakapan: pesan yang dilihat dcAI di ponsel anak diproses di ponsel itu: dari papan ketik dcAI, dari notifikasi aplikasi chat, dan, bila pembacaan teks layar diaktifkan, dari teks yang tampil di layar aplikasi apa pun.\n"
    "- Layar (semua aplikasi): bila diaktifkan orang tua, dcAI membaca teks yang tampil di layar aplikasi apa pun untuk mengenali pola berisiko, selalu dengan notifikasi tetap dan tanpa mode tersembunyi. Teks disamarkan di ponsel dan hanya pesan yang ditandai yang dikirim. Pada percakapan yang sudah berisiko, dcAI mengambil tangkapan layar dan menilainya di ponsel; tangkapan layar tidak pernah dikirim.",
)
_V5_EN = _V4_EN.replace(
    "- Conversations: messages in chat apps that integrate dcAI and text typed with the dcAI keyboard are processed on the child's phone.",
    "- Conversations: messages dcAI sees on the child's phone are processed on the phone: from the dcAI keyboard, from chat apps' notifications, and, when screen reading is on, from the text shown on screen in any app.\n"
    "- Screen (all apps): when the parent turns it on, dcAI reads the text shown on screen in any app to recognise risky patterns, always with the persistent notification and no hidden mode. Text is masked on the phone and only flagged messages are sent. In a chat that is already risky, dcAI takes a screenshot and assesses it on the phone; the screenshot is never sent.",
)
_V5_SCOPES = (*_V2_SCOPES, Scope.WAKTU, Scope.LAYAR)  # pinned: predates the sekolah scope
V5 = ConsentText(version="2026-10-30.1", id=_V5_ID, en=_V5_EN, scopes=_V5_SCOPES)

# V6 removes voice notes. The phone cannot capture a voice note from other apps, so the
# scope was never functional; the Suara paragraph is dropped and SUARA leaves the offered
# scopes. Older versions keep it for records already granted.
_V6_ID = _V5_ID.replace(
    "- Suara: pesan suara di percakapan yang sudah berisiko dikirim ke layanan transkripsi "
    "Meta untuk diubah menjadi teks, lalu teksnya disamarkan dan dinilai seperti pesan lain. "
    "Rekaman suara diproses di memori dan tidak disimpan.\n",
    "",
)
_V6_EN = _V5_EN.replace(
    "- Voice: a voice note in a chat that is already risky is sent to Meta's transcription "
    "service to be turned into text; the text is then masked and assessed like other "
    "messages. Recordings are processed in memory and not stored.\n",
    "",
)
CURRENT = ConsentText(
    version="2026-10-30.2",
    id=_V6_ID,
    en=_V6_EN,
    scopes=tuple(s for s in _V5_SCOPES if s != Scope.SUARA),
)
VERSIONS: dict[str, ConsentText] = {t.version: t for t in (V1, V2, V3, V4, V5, CURRENT)}
