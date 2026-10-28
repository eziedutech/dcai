"""Fixed Guide texts, used when the model is unavailable or breaks a rule. Every
situation, level and language combination is validated by the same schema as model output
(tests/test_guide.py), so a fallback can never show something the model would not be
allowed to show."""

from app.guide.guide import Situation
from app.guide.schemas import GuideOutput
from app.risk.schemas import Level

_T: dict[str, dict[Situation, dict]] = {
    "id": {
        Situation.APPROACH: {
            "child_nudge": "Kamu boleh berhenti membalas dan tidak wajib merahasiakan apa pun. Ceritakan obrolan ini ke orang dewasa yang kamu percaya.",
            "what_we_see": "Kontak dalam obrolan ini menunjukkan pola pendekatan yang perlu didampingi, misalnya membangun kedekatan dengan cepat atau meminta hal pribadi.",
            "why_it_matters": "Pola seperti ini sering berjalan bertahap. Anak yang merasa aman bercerita lebih mudah dilindungi sejak awal.",
            "starters": [
                "Akhir-akhir ini kamu kenal teman baru di internet? Seru nggak ngobrolnya?",
                "Kalau ada yang minta kamu merahasiakan sesuatu dari Ibu atau Ayah, menurutmu kenapa ya?",
                "Apa pun yang kamu ceritakan, kita cari jalan keluarnya bareng-bareng. Ada yang bikin kamu ragu?",
            ],
            "do": [
                "Dengarkan dulu dengan tenang dan ucapkan terima kasih karena anak mau bercerita.",
                "Sepakati bersama bahwa rahasia yang membuat tidak nyaman selalu boleh diceritakan.",
            ],
            "dont": [
                "Jangan langsung marah atau menyalahkan anak.",
                "Jangan menyita ponsel sebagai hukuman, karena anak bisa berhenti bercerita.",
            ],
            "lesson": (
                "Rahasia baik dan rahasia buruk",
                "Rahasia baik, seperti kejutan ulang tahun, akan segera dibuka dan membuat orang senang. Rahasia buruk membuatmu tidak nyaman atau takut. Rahasia buruk selalu boleh kamu ceritakan ke orang dewasa yang kamu percaya, dan kamu tidak akan disalahkan.",
            ),
        },
        Situation.DANGEROUS_INVITE: {
            "child_nudge": "Ajakan berkelahi, mencoba obat atau minuman keras, dan membawa senjata tajam selalu boleh kamu tolak, cukup bilang kamu sudah ditunggu di rumah lalu menjauh. Ceritakan ke orang dewasa yang kamu percaya, kamu tidak akan disalahkan.",
            "what_we_see": "Ada ajakan ke kegiatan berbahaya dalam obrolan, misalnya ikut berkelahi atau tawuran, mencoba obat terlarang atau minuman keras, atau membawa senjata tajam.",
            "why_it_matters": "Di usia ini tekanan dari teman terasa kuat dan menolak bisa terasa sulit. Anak yang tahu cara menolak dan tahu bisa bercerita ke orang tua lebih mudah menjauh dari bahaya.",
            "starters": [
                "Akhir-akhir ini teman-temanmu lagi sering ngajak ke mana aja?",
                "Kalau ada yang ngajak hal yang bikin kamu nggak enak hati, biasanya kamu jawab apa?",
                "Kamu boleh pakai alasan Ibu atau Ayah buat menolak, misalnya bilang sudah dijemput. Mau kita latih bareng?",
            ],
            "do": [
                "Dengarkan dengan tenang dan hargai kejujuran anak.",
                "Sepakati kalimat menolak dan kode singkat agar anak bisa minta dijemput kapan saja.",
                "Kenali teman-teman anak dan kegiatan mereka dengan rasa ingin tahu yang hangat.",
            ],
            "dont": [
                "Jangan langsung menghukum atau menyita ponsel, karena anak bisa berhenti bercerita.",
                "Jangan menginterogasi atau menuduh anak sebelum mendengar ceritanya.",
            ],
            "lesson": (
                "Berani bilang tidak",
                "Teman yang baik tidak memaksamu ikut berkelahi, mencoba obat, minum minuman keras, atau membawa senjata. Kamu boleh menolak dengan singkat, memakai alasan orang tuamu, lalu menjauh. Setelah itu ceritakan ke orang dewasa yang kamu percaya.",
            ),
        },
        Situation.BULLIED: {
            "child_nudge": "Kata-kata itu tidak pantas kamu terima dan itu bukan salahmu. Simpan tangkapan layarnya dan ceritakan ke orang dewasa yang kamu percaya.",
            "what_we_see": "Ada tanda perundungan atau ancaman yang ditujukan kepada anak dalam obrolan.",
            "why_it_matters": "Perundungan yang dibiarkan bisa mengganggu rasa aman dan semangat belajar anak. Dukungan orang tua membuat anak tidak merasa sendirian.",
            "starters": [
                "Gimana suasana di grup kelas akhir-akhir ini?",
                "Pernah ada yang bikin kamu sedih atau takut lewat chat?",
                "Kalau ada yang jahat ke kamu, kita hadapi bareng ya. Mau cerita?",
            ],
            "do": [
                "Yakinkan anak bahwa ini bukan salahnya.",
                "Bantu simpan bukti dan ajak bicara dengan wali kelas bila terjadi di lingkungan sekolah.",
            ],
            "dont": [
                "Jangan menyuruh anak membalas dengan kata kasar.",
                "Jangan menghubungi pelaku atau orang tuanya dengan emosi.",
            ],
            "lesson": (
                "Kamu tidak sendirian",
                "Kalau ada yang merendahkanmu di chat, kamu tidak harus membalas. Simpan buktinya, blokir bila perlu, lalu cerita ke orang yang kamu percaya. Meminta bantuan adalah tanda kamu kuat.",
            ),
        },
        Situation.BULLYING: {
            "child_nudge": "Coba baca lagi pesanmu dan bayangkan kalau kamu yang menerimanya. Kamu selalu bisa memilih kata yang lebih baik atau meminta maaf.",
            "what_we_see": "Beberapa pesan dari anak bernada merendahkan atau mengancam teman.",
            "why_it_matters": "Anak sedang belajar mengelola emosi di dunia digital. Dampingan yang hangat membantunya memahami dampak kata-katanya.",
            "starters": [
                "Tadi kayaknya ada yang bikin kamu kesal di chat. Ada apa?",
                "Menurutmu temanmu merasa gimana waktu baca pesan itu?",
                "Kalau mau memperbaiki, kira-kira apa yang bisa kamu lakukan?",
            ],
            "do": [
                "Tanyakan dulu apa yang membuat anak kesal.",
                "Bantu anak memikirkan cara memperbaiki, misalnya meminta maaf.",
            ],
            "dont": [
                "Jangan mempermalukan anak di depan orang lain.",
                "Jangan memberi hukuman tanpa mengajak anak memahami dampaknya.",
            ],
            "lesson": (
                "Berhenti sebentar sebelum kirim",
                "Saat kesal, tunggu sebentar sebelum menekan kirim. Tanyakan pada dirimu: apakah aku berani mengatakan ini langsung? Kata-kata di internet bisa dibaca berulang kali dan menyakiti lebih lama.",
            ),
        },
        Situation.SHARED_DATA: {
            "child_nudge": "Nomor, alamat, dan sekolahmu sebaiknya hanya untuk orang yang kamu kenal langsung. Kalau ragu, tanya orang tuamu dulu sebelum mengirim.",
            "what_we_see": "Anak membagikan data pribadi dalam obrolan.",
            "why_it_matters": "Data pribadi bisa dipakai orang lain untuk menemukan atau menghubungi anak. Kebiasaan menjaga data perlu dilatih sejak dini.",
            "starters": [
                "Kamu tahu nggak data apa saja yang sebaiknya nggak dibagikan di internet?",
                "Kalau ada yang minta nomor atau alamat, biasanya kamu gimana?",
                "Yuk kita bikin daftar orang yang boleh tahu nomor kamu.",
            ],
            "do": [
                "Ajak anak membuat daftar data yang boleh dan tidak boleh dibagikan.",
                "Periksa bersama pengaturan privasi aplikasi yang dipakai anak.",
            ],
            "dont": ["Jangan membuat anak merasa malu karena sudah terlanjur berbagi."],
            "lesson": (
                "Data pribadi itu milikmu",
                "Nama lengkap, nomor telepon, alamat rumah, dan nama sekolah adalah data pribadi. Bagikan hanya kepada orang yang kamu kenal di dunia nyata, dan tanya orang tuamu kalau ragu.",
            ),
        },
        Situation.DISTRESS: {
            "child_nudge": "Terima kasih sudah jujur tentang perasaanmu, kamu penting dan tidak sendirian. Coba cerita hari ini ke orang dewasa yang kamu percaya, atau lihat kanal bantuan di bawah.",
            "what_we_see": "Anak menyampaikan perasaan berat, misalnya merasa lelah dengan semuanya atau merasa menjadi beban.",
            "why_it_matters": "Perasaan seperti ini perlu didengar dengan hangat. Kehadiran orang tua yang tenang sangat membantu.",
            "starters": [
                "Ibu atau Ayah perhatikan kamu kelihatan capek akhir-akhir ini. Mau cerita?",
                "Apa pun yang kamu rasakan, kami ada di sini dan sayang sama kamu.",
                "Ada hal yang bikin hari-harimu terasa berat?",
            ],
            "do": [
                "Luangkan waktu untuk mendengarkan tanpa menghakimi.",
                "Bila perasaan berat berlanjut, cari dukungan tenaga profesional atau kanal bantuan di bawah.",
            ],
            "dont": [
                "Jangan meremehkan perasaan anak.",
                "Jangan menunda bila anak tampak sangat terpukul.",
            ],
            "lesson": (
                "Perasaan boleh dibagi",
                "Semua orang kadang merasa sedih atau lelah. Bercerita kepada orang yang kamu percaya bisa membuat beban terasa lebih ringan. Kamu tidak harus menghadapinya sendirian.",
            ),
        },
        Situation.GENERAL: {
            "child_nudge": "Kalau ada obrolan yang bikin kamu ragu, berhenti sebentar dan tanya orang dewasa yang kamu percaya.",
            "what_we_see": "Ada hal dalam obrolan yang perlu sedikit perhatian, tetapi belum terlihat pola yang jelas.",
            "why_it_matters": "Percakapan rutin tentang pengalaman digital membuat anak terbiasa bercerita.",
            "starters": [
                "Hari ini ada obrolan seru di game atau chat?",
                "Ada hal di internet yang bikin kamu bingung akhir-akhir ini?",
                "Kalau ada yang aneh di chat, kamu tahu harus cerita ke siapa?",
            ],
            "do": ["Jadikan obrolan tentang dunia digital sebagai kebiasaan santai."],
            "dont": ["Jangan menginterogasi anak."],
            "lesson": (
                "Berhenti, pikir, cerita",
                "Kalau ada pesan yang membuatmu ragu, berhenti sebentar, pikirkan apakah itu aman, lalu ceritakan ke orang yang kamu percaya.",
            ),
        },
    },
    "en": {
        Situation.APPROACH: {
            "child_nudge": "You can stop replying, and you never have to keep a secret like this. Tell an adult you trust about this chat.",
            "what_we_see": "The contact in this chat shows an approach pattern that needs your support, such as building closeness fast or asking for personal things.",
            "why_it_matters": "Patterns like this often unfold step by step. A child who feels safe to talk is easier to protect early.",
            "starters": [
                "Have you met anyone new online lately? What do you talk about?",
                "If someone asked you to keep a secret from us, why do you think they would?",
                "Whatever you tell me, we will figure it out together. Is anything bothering you?",
            ],
            "do": [
                "Listen calmly first and thank your child for telling you.",
                "Agree together that secrets that feel wrong can always be shared.",
            ],
            "dont": [
                "Do not get angry or blame your child.",
                "Do not take the phone away as a punishment; your child may stop telling you things.",
            ],
            "lesson": (
                "Good secrets and bad secrets",
                "Good secrets, like a birthday surprise, end soon and make people happy. Bad secrets make you feel uncomfortable or scared. You can always tell a trusted adult about a bad secret, and you will not be blamed.",
            ),
        },
        Situation.DANGEROUS_INVITE: {
            "child_nudge": "You can always say no to fights, drugs, alcohol or carrying a weapon; just say you are expected at home and walk away. Tell an adult you trust; you will not be blamed.",
            "what_we_see": "The chat contains an invitation to something dangerous, such as joining a fight, trying drugs or alcohol, or carrying a sharp weapon.",
            "why_it_matters": "At this age pressure from friends feels strong and saying no can be hard. A child who knows how to refuse and knows they can tell a parent finds it easier to stay away from harm.",
            "starters": [
                "What have your friends been inviting you to lately?",
                "When someone asks you to do something that feels wrong, what do you usually say?",
                "You can always use me as your excuse, for example by saying I am picking you up. Shall we practise it together?",
            ],
            "do": [
                "Listen calmly and value your child's honesty.",
                "Agree on a way to say no and a short code word your child can send to be picked up at any time.",
                "Get to know your child's friends and their activities with warm curiosity.",
            ],
            "dont": [
                "Do not punish or take the phone away straight away; your child may stop telling you things.",
                "Do not interrogate or accuse your child before hearing their story.",
            ],
            "lesson": (
                "Brave enough to say no",
                "A good friend does not push you to fight, try drugs, drink alcohol or carry a weapon. You can say no in a few words, use your parent as the excuse, and walk away. Then tell an adult you trust.",
            ),
        },
        Situation.BULLIED: {
            "child_nudge": "You do not deserve those words, and it is not your fault. Save a screenshot and tell an adult you trust.",
            "what_we_see": "There are signs of bullying or threats aimed at your child in the chat.",
            "why_it_matters": "Bullying that goes on can hurt a child's sense of safety. Your support helps them not feel alone.",
            "starters": [
                "How is the class group chat these days?",
                "Has anyone made you sad or scared in a chat?",
                "If someone is mean to you, we will deal with it together. Want to tell me?",
            ],
            "do": [
                "Reassure your child that this is not their fault.",
                "Help keep evidence and talk to the teacher if it involves school.",
            ],
            "dont": [
                "Do not tell your child to answer back with insults.",
                "Do not contact the other child or their parents in anger.",
            ],
            "lesson": (
                "You are not alone",
                "If someone puts you down in a chat, you do not have to reply. Save the proof, block if needed, and tell someone you trust. Asking for help is a strong thing to do.",
            ),
        },
        Situation.BULLYING: {
            "child_nudge": "Read your message again and imagine receiving it. You can always choose kinder words or say sorry.",
            "what_we_see": "Some of your child's messages put down or threaten a peer.",
            "why_it_matters": "Children are still learning to handle emotions online. Warm guidance helps them see the effect of their words.",
            "starters": [
                "Something in the chat seemed to upset you today. What happened?",
                "How do you think your friend felt reading that message?",
                "If you wanted to make it right, what could you do?",
            ],
            "do": [
                "Ask first what upset your child.",
                "Help your child think of a way to repair it, such as an apology.",
            ],
            "dont": [
                "Do not shame your child in front of others.",
                "Do not punish without helping your child understand the effect.",
            ],
            "lesson": (
                "Pause before you send",
                "When you are upset, wait a moment before pressing send. Ask yourself: would I say this face to face? Words online can be read again and again and hurt for longer.",
            ),
        },
        Situation.SHARED_DATA: {
            "child_nudge": "Your number, address and school are best kept for people you know in real life. If you are not sure, ask your parent before sending.",
            "what_we_see": "Your child shared personal data in a chat.",
            "why_it_matters": "Personal data can let others find or contact a child. Protecting it is a habit worth practising early.",
            "starters": [
                "Do you know which details are better not to share online?",
                "When someone asks for your number or address, what do you usually do?",
                "Shall we make a list of who is allowed to know your number?",
            ],
            "do": [
                "Make a list together of what can and cannot be shared.",
                "Check the privacy settings of your child's apps together.",
            ],
            "dont": ["Do not make your child feel ashamed for having shared."],
            "lesson": (
                "Your data belongs to you",
                "Your full name, phone number, home address and school are personal data. Share them only with people you know in real life, and ask a parent when unsure.",
            ),
        },
        Situation.DISTRESS: {
            "child_nudge": "Thank you for being honest about how you feel; you matter and you are not alone. Try talking to an adult you trust today, or see the help channels below.",
            "what_we_see": "Your child expressed heavy feelings, such as being tired of everything or feeling like a burden.",
            "why_it_matters": "Feelings like these need to be heard warmly. A calm, present parent helps a lot.",
            "starters": [
                "I have noticed you seem tired lately. Do you want to talk?",
                "Whatever you are feeling, we are here and we love you.",
                "Is anything making your days feel heavy?",
            ],
            "do": [
                "Make time to listen without judging.",
                "If the heavy feelings continue, seek support from a professional or the help channels below.",
            ],
            "dont": [
                "Do not brush off your child's feelings.",
                "Do not wait if your child seems deeply hurt.",
            ],
            "lesson": (
                "Feelings can be shared",
                "Everyone feels sad or tired sometimes. Talking to someone you trust can make it feel lighter. You do not have to face it alone.",
            ),
        },
        Situation.GENERAL: {
            "child_nudge": "If a chat makes you unsure, pause and ask an adult you trust.",
            "what_we_see": "Something in the chat needs a little attention, but no clear pattern shows yet.",
            "why_it_matters": "Regular, relaxed talks about online life make it natural for children to share.",
            "starters": [
                "Any fun chats in games or messages today?",
                "Has anything online confused you lately?",
                "If something in a chat feels odd, do you know who to tell?",
            ],
            "do": ["Make talking about online life a relaxed habit."],
            "dont": ["Do not interrogate your child."],
            "lesson": (
                "Stop, think, tell",
                "If a message makes you unsure, stop for a moment, think whether it is safe, and tell someone you trust.",
            ),
        },
    },
}

_URGENT_DO = {
    "id": "Simpan bukti berupa tangkapan layar, laporkan lewat fitur platform, dan hubungi pihak berwenang setempat bila perlu.",
    "en": "Keep evidence as screenshots, report it through the platform, and contact local authorities if needed.",
}
_URGENT_DONT = {
    "id": "Jangan menghadapi pihak lain secara langsung.",
    "en": "Do not confront the other person directly.",
}


def template(sit: Situation, level: Level, language: str) -> GuideOutput:
    lang = language if language in _T else "id"
    t = _T[lang][sit]
    do = list(t["do"])
    dont = list(t["dont"])
    if level == Level.MENDESAK:
        do = [_URGENT_DO[lang], *do][:4]
        dont = [_URGENT_DONT[lang], *dont][:4]
    lesson = None if level == Level.AMAN else {"title": t["lesson"][0], "body": t["lesson"][1]}
    return GuideOutput.model_validate(
        {
            "child_nudge": t["child_nudge"],
            "parent_insight": {
                "what_we_see": t["what_we_see"],
                "why_it_matters": t["why_it_matters"],
                "conversation_starters": t["starters"],
                "do": do,
                "dont": dont,
            },
            "micro_lesson": lesson,
        }
    )
