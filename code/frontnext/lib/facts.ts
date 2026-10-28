// Research figures for /fakta. Each value and sentence follows its source; every item
// links to the page that was opened to check it (October 2026). Regional studies say
// their region. Indonesian government figures come through ANTARA, the state news agency,
// quoting the official on the record.

export type Bi = { id: string; en: string };
export type Fact = { v: Bi; text: Bi; src: string; date: string; url: string };
export type Topic = { key: string; title: Bi; dcai?: Bi; note?: Bi; facts: Fact[] };

const DH_ID = "https://safeonline.global/wp-content/uploads/2023/12/DH_Indonesia_ONLINE_ID_Nov22.pdf";
const DH_SRC = "ECPAT, INTERPOL, UNICEF, Disrupting Harm in Indonesia";
const UNICEF_2026 = "https://www.unicef.org/press-releases/1-5-children-across-21-countries-have-experienced-tech-facilitated-sexual";
const UNICEF_ID_2022 = "https://www.unicef.org/indonesia/id/siaran-pers/data-survei-baru-hingga-56-persen-insiden-eksploitasi-seksual-dan-perlakuan-yang-salah";
const EUKO = "https://www.lse.ac.uk/media-and-communications/assets/documents/research/eu-kids-online/reports/EU-Kids-Online-2020-March2020.pdf";
const HBSC_GAMES = "https://www.who.int/europe/news/item/25-09-2024-teens--screens-and-mental-health";

export const TOPICS: Topic[] = [
  {
    key: "grooming",
    title: { id: "Grooming dan eksploitasi seksual online", en: "Grooming and online sexual exploitation" },
    dcai: {
      id: "dcAI mengenali pola pendekatan bertahap di obrolan dan memberi anak pengingat pada saat itu juga.",
      en: "dcAI recognises step-by-step approach patterns in chats and reminds the child in the moment.",
    },
    facts: [
      {
        v: { id: "1 dari 5", en: "1 in 5" },
        text: {
          id: "anak pengguna internet usia 12 sampai 17 tahun di 21 negara, sekitar 20 juta anak, mengalami setidaknya satu bentuk eksploitasi dan kekerasan seksual berbasis teknologi dalam satu tahun.",
          en: "internet-using children aged 12 to 17 across 21 countries, some 20 million children, faced at least one form of technology-facilitated sexual exploitation and abuse in a single year.",
        },
        src: "UNICEF, Through Children's Eyes",
        date: "2026",
        url: UNICEF_2026,
      },
      {
        v: { id: "38%", en: "38%" },
        text: {
          id: "anak pertama kali bertemu pelaku secara online, sering lewat akun palsu dan pesan pribadi.",
          en: "of children first encountered the perpetrator online, often through fake accounts and private messaging.",
        },
        src: "UNICEF, Through Children's Eyes",
        date: "2026",
        url: UNICEF_2026,
      },
      {
        v: { id: "9 juta", en: "9 million" },
        text: {
          id: "anak diminta melakukan percakapan seksual atau mengirim gambar seksual di luar kemauan mereka.",
          en: "children were asked to engage in sexual conversations or share sexual images against their will.",
        },
        src: "UNICEF, Through Children's Eyes",
        date: "2026",
        url: UNICEF_2026,
      },
      {
        v: { id: "12,5%", en: "12.5%" },
        text: {
          id: "anak mengalami ajakan seksual online dalam setahun terakhir, rata-rata gabungan dari 123 studi di berbagai negara.",
          en: "of children faced online sexual solicitation in the past year, the pooled mean of 123 studies across countries.",
        },
        src: "Fry dkk., The Lancet Child & Adolescent Health",
        date: "2025",
        url: "https://doi.org/10.1016/S2352-4642(24)00329-8",
      },
      {
        v: { id: "500.000", en: "500,000" },
        text: {
          id: "anak di Indonesia (2% anak usia 12 sampai 17 tahun pengguna internet) menyatakan pernah menjadi korban eksploitasi seksual online dalam setahun terakhir.",
          en: "children in Indonesia (2% of internet-using 12 to 17 year olds) reported being victims of online sexual exploitation and abuse in the past year.",
        },
        src: "UNICEF Indonesia dan KemenPPPA, dari Disrupting Harm",
        date: "2022",
        url: UNICEF_ID_2022,
      },
      {
        v: { id: "56%", en: "56%" },
        text: {
          id: "anak di Indonesia yang mengalaminya tidak pernah menceritakan kejadian itu kepada siapa pun.",
          en: "of children in Indonesia who experienced it never told anyone.",
        },
        src: "UNICEF Indonesia dan KemenPPPA, dari Disrupting Harm",
        date: "2022",
        url: UNICEF_ID_2022,
      },
    ],
  },
  {
    key: "perundungan",
    title: { id: "Perundungan siber", en: "Cyberbullying" },
    dcai: {
      id: "dcAI mengenali perundungan, ancaman, dan kata kasar, baik yang diterima maupun yang ditulis anak.",
      en: "dcAI recognises bullying, threats and insults, whether the child receives or writes them.",
    },
    facts: [
      {
        v: { id: "1 dari 6", en: "1 in 6" },
        text: {
          id: "remaja usia 11, 13, dan 15 tahun (15%) pernah mengalami perundungan siber, di 44 negara dan wilayah Eropa, Asia Tengah, dan Kanada.",
          en: "adolescents aged 11, 13 and 15 (15%) have experienced cyberbullying, across 44 countries and regions in Europe, Central Asia and Canada.",
        },
        src: "WHO/Europe, studi HBSC",
        date: "2024",
        url: "https://www.who.int/europe/news/item/27-03-2024-one-in-six-school-aged-children-experiences-cyberbullying--finds-new-who-europe-study",
      },
      {
        v: { id: "1 dari 8", en: "1 in 8" },
        text: {
          id: "remaja (12%) mengaku pernah merundung orang lain secara online.",
          en: "adolescents (12%) report cyberbullying others.",
        },
        src: "WHO/Europe, studi HBSC",
        date: "2024",
        url: "https://www.who.int/europe/news/item/27-03-2024-one-in-six-school-aged-children-experiences-cyberbullying--finds-new-who-europe-study",
      },
      {
        v: { id: "45%", en: "45%" },
        text: {
          id: "dari 2.777 anak muda usia 14 sampai 24 tahun di Indonesia yang menjawab jajak pendapat U-Report mengatakan pernah mengalami perundungan siber.",
          en: "of 2,777 young people aged 14 to 24 in Indonesia who answered a U-Report poll said they had experienced cyberbullying.",
        },
        src: "UNICEF Indonesia, jajak pendapat U-Report",
        date: "2021",
        url: "https://www.unicef.org/indonesia/id/siaran-pers/indonesia-ratusan-anak-dan-remaja-menyerukan-kebaikan-dan-diakhirinya-perundungan",
      },
    ],
    note: {
      id: "Jajak pendapat U-Report diikuti secara sukarela, sehingga hasilnya tidak mewakili seluruh anak muda Indonesia.",
      en: "U-Report polls are opt-in, so the result does not represent all young people in Indonesia.",
    },
  },
  {
    key: "pornografi",
    title: { id: "Paparan pornografi", en: "Exposure to pornography" },
    dcai: { id: "dcAI menahan situs dewasa di ponsel anak.", en: "dcAI holds adult sites on the child's phone." },
    facts: [
      {
        v: { id: "22%", en: "22%" },
        text: {
          id: "anak usia 12 sampai 17 tahun pengguna internet di Indonesia menemukan konten seksual tanpa sengaja, lewat iklan, umpan media sosial, mesin pencari, dan aplikasi pesan.",
          en: "of internet-using children aged 12 to 17 in Indonesia came across sexual content unexpectedly, through ads, social media feeds, search engines and messaging apps.",
        },
        src: DH_SRC,
        date: "2022",
        url: DH_ID,
      },
      {
        v: { id: "13 tahun", en: "Age 13" },
        text: {
          id: "rata-rata usia anak pertama kali melihat pornografi di Inggris; 10% sudah melihatnya sebelum usia 9 tahun.",
          en: "is the average age at which children in England first see pornography; 10% had seen it by age 9.",
        },
        src: "Children's Commissioner for England",
        date: "2023",
        url: "https://www.childrenscommissioner.gov.uk/resource/a-lot-of-it-is-actually-just-abuse-young-people-and-pornography/",
      },
    ],
  },
  {
    key: "judi",
    title: { id: "Judi online", en: "Online gambling" },
    dcai: { id: "dcAI menahan situs judi di ponsel anak.", en: "dcAI holds gambling sites on the child's phone." },
    facts: [
      {
        v: { id: "197.054", en: "197,054" },
        text: {
          id: "anak usia di bawah 11 sampai 19 tahun di Indonesia melakukan deposit judi online senilai Rp293,4 miliar dalam 2,2 juta transaksi.",
          en: "children aged under 11 to 19 in Indonesia made online gambling deposits worth Rp293.4 billion in 2.2 million transactions.",
        },
        src: "PPATK, melalui ANTARA",
        date: "2024",
        url: "https://www.antaranews.com/berita/4218331/ppatk-sekitar-190-ribu-anak-usia-17-19-tahun-terlibat-judi-online",
      },
      {
        v: { id: "1.160", en: "1,160" },
        text: {
          id: "anak berusia di bawah 11 tahun melakukan 22 ribu transaksi judi online senilai sedikitnya Rp3 miliar.",
          en: "children under 11 made 22,000 online gambling transactions worth at least Rp3 billion.",
        },
        src: "PPATK, melalui ANTARA",
        date: "2024",
        url: "https://www.antaranews.com/berita/4218331/ppatk-sekitar-190-ribu-anak-usia-17-19-tahun-terlibat-judi-online",
      },
      {
        v: { id: "17,9%", en: "17.9%" },
        text: {
          id: "remaja di dunia pernah berjudi dalam 12 bulan terakhir.",
          en: "of adolescents worldwide had gambled in the past 12 months.",
        },
        src: "Tran dkk., The Lancet Public Health",
        date: "2024",
        url: "https://doi.org/10.1016/S2468-2667(24)00126-9",
      },
    ],
  },
  {
    key: "kebencian",
    title: { id: "Ujaran kebencian dan paham kekerasan", en: "Hate and violent ideas" },
    dcai: { id: "dcAI menahan situs kebencian di ponsel anak.", en: "dcAI holds hate sites on the child's phone." },
    facts: [
      {
        v: { id: "620", en: "620" },
        text: {
          id: "anak di Indonesia terpapar paham kekerasan dan radikalisme melalui media sosial sepanjang Januari hingga 26 Agustus 2026.",
          en: "children in Indonesia were exposed to violent ideas and radicalism through social media from January to 26 August 2026.",
        },
        src: "BNPT, melalui ANTARA",
        date: "2026",
        url: "https://www.antaranews.com/berita/5722115/bnpt-620-anak-terpapar-radikalisme-melalui-media-sosial",
      },
      {
        v: { id: "110", en: "110" },
        text: {
          id: "anak usia 10 sampai 18 tahun di 23 provinsi diduga direkrut jaringan terorisme, awalnya lewat platform terbuka dan gim online.",
          en: "children aged 10 to 18 in 23 provinces were suspected of being recruited by terror networks, first through open platforms and online games.",
        },
        src: "Polri, melalui ANTARA",
        date: "2025",
        url: "https://www.antaranews.com/berita/5249337/densus-88-catat-110-anak-diduga-direkrut-jaringan-terorisme",
      },
      {
        v: { id: "17%", en: "17%" },
        text: {
          id: "anak usia 12 sampai 16 tahun di 19 negara Eropa melihat pesan kebencian setidaknya sebulan sekali, konten berbahaya yang paling sering mereka temui.",
          en: "of children aged 12 to 16 in 19 European countries saw hate messages at least monthly, the harmful content they met most often.",
        },
        src: "EU Kids Online",
        date: "2020",
        url: EUKO,
      },
    ],
  },
  {
    key: "data",
    title: { id: "Data pribadi dan orang asing", en: "Personal data and strangers" },
    dcai: {
      id: "dcAI menyamarkan nama, nomor, alamat, dan sekolah di ponsel, dan mengaburkan data pribadi di gambar sebelum dibagikan.",
      en: "dcAI masks names, numbers, addresses and schools on the phone, and blurs personal data in images before they are shared.",
    },
    facts: [
      {
        v: { id: "29%", en: "29%" },
        text: {
          id: "anak usia 12 sampai 17 tahun di Indonesia membagikan informasi pribadi (nama lengkap, alamat, atau nomor telepon) kepada orang yang belum pernah mereka temui langsung dalam setahun terakhir.",
          en: "of children aged 12 to 17 in Indonesia shared personal information (full name, address or phone number) with someone they had never met face-to-face in the past year.",
        },
        src: DH_SRC,
        date: "2022",
        url: DH_ID,
      },
      {
        v: { id: "43%", en: "43%" },
        text: {
          id: "menambahkan orang yang belum pernah mereka temui langsung ke daftar kontak dalam setahun terakhir.",
          en: "added people they had never met face-to-face to their contact lists in the past year.",
        },
        src: DH_SRC,
        date: "2022",
        url: DH_ID,
      },
      {
        v: { id: "11%", en: "11%" },
        text: {
          id: "bertemu langsung dengan orang yang pertama kali mereka kenal secara online dalam setahun terakhir.",
          en: "met someone in person whom they had first met online in the past year.",
        },
        src: DH_SRC,
        date: "2022",
        url: DH_ID,
      },
    ],
  },
  {
    key: "layar",
    title: { id: "Layar, jam tidur, dan video pendek", en: "Screens, bedtime and short video" },
    dcai: {
      id: "Orang tua mengatur batas harian, jam tidur, dan jeda setelah lama menonton video pendek.",
      en: "Parents set daily limits, bedtime and breaks after long short-video sessions.",
    },
    facts: [
      {
        v: { id: "36%", en: "36%" },
        text: {
          id: "remaja usia 13 sampai 17 tahun di Amerika Serikat memakai setidaknya satu dari lima platform besar hampir terus-menerus; 21% untuk TikTok saja.",
          en: "of US teens aged 13 to 17 use at least one of five major platforms almost constantly; 21% for TikTok alone.",
        },
        src: "Pew Research Center",
        date: "2025",
        url: "https://www.pewresearch.org/internet/2025/12/09/teens-social-media-and-ai-chatbots-2025/",
      },
      {
        v: { id: "-3 menit", en: "-3 min" },
        text: {
          id: "total tidur untuk setiap tambahan 10 menit layar di tempat tidur, pada remaja usia 11 sampai 14 tahun (satu studi, 79 peserta).",
          en: "of total sleep for every extra 10 minutes of screen time in bed, in youths aged 11 to 14 (one study, 79 participants).",
        },
        src: "Brosnan dkk., JAMA Pediatrics",
        date: "2024",
        url: "https://doi.org/10.1001/jamapediatrics.2024.2914",
      },
      {
        v: { id: "50,3%", en: "50.3%" },
        text: {
          id: "siswa laki-laki di empat SMP di Jakarta sering atau selalu bermain gim online sebelum tidur (perempuan 21,7%).",
          en: "of boys in four Jakarta middle schools often or always played online games before sleep (girls 21.7%).",
        },
        src: "Gandaputra dkk., IJERPH",
        date: "2021",
        url: "https://doi.org/10.3390/ijerph18020691",
      },
    ],
  },
  {
    key: "gim",
    title: { id: "Waktu bermain gim", en: "Time on games" },
    dcai: { id: "Orang tua mengatur batas waktu untuk kategori game.", en: "Parents set a time limit for the games category." },
    facts: [
      {
        v: { id: "22%", en: "22%" },
        text: {
          id: "remaja bermain setidaknya 4 jam pada hari mereka bermain gim; 34% bermain setiap hari (44 negara dan wilayah Eropa, Asia Tengah, dan Kanada).",
          en: "of adolescents play for at least 4 hours on days they game; 34% play daily (44 countries and regions in Europe, Central Asia and Canada).",
        },
        src: "WHO/Europe, studi HBSC",
        date: "2024",
        url: HBSC_GAMES,
      },
      {
        v: { id: "12%", en: "12%" },
        text: {
          id: "remaja berisiko memiliki pola bermain gim yang bermasalah, laki-laki 16% dan perempuan 7%.",
          en: "of adolescents are at risk of problematic gaming, boys 16% and girls 7%.",
        },
        src: "WHO/Europe, studi HBSC",
        date: "2024",
        url: HBSC_GAMES,
      },
    ],
  },
  {
    key: "kenakalan",
    title: { id: "Kenakalan remaja yang diajak lewat online", en: "Delinquency arranged online" },
    dcai: {
      id: "dcAI mengenali ajakan tawuran, narkoba, miras, atau membawa senjata tajam di obrolan, dan menahan situs narkoba.",
      en: "dcAI recognises invitations to fights, drugs, alcohol or carrying blades in chats, and holds drug sites.",
    },
    facts: [
      {
        v: { id: "312 ribu", en: "312,000" },
        text: {
          id: "penyalahguna narkoba di kelompok usia remaja (pelajar) di Indonesia, menurut survei prevalensi 2023.",
          en: "drug users among adolescent students in Indonesia, according to the 2023 prevalence survey.",
        },
        src: "BNN, melalui ANTARA",
        date: "2025",
        url: "https://www.antaranews.com/berita/4775797/bnn-pelajar-kelompok-remaja-berpotensi-besar-salahgunakan-narkoba",
      },
    ],
    note: {
      id: "Belum ada angka nasional tentang ajakan tawuran yang dibuat lewat online. Polrestabes Makassar menyebut tawuran pelajar sering diatur lewat \"janjian COD\" di media sosial, dan menjalankan patroli siber (ANTARA, 2025).",
      en: "There is no national figure yet for fights arranged online. Makassar police say student fights are often set up as \"COD\" meet-ups on social media, and run cyber patrols in response (ANTARA, 2025).",
    },
  },
  {
    key: "internet",
    title: { id: "Anak dan internet", en: "Children and the internet" },
    facts: [
      {
        v: { id: "92%", en: "92%" },
        text: {
          id: "anak usia 12 sampai 17 tahun di Indonesia menggunakan internet dalam tiga bulan terakhir; 95% di antaranya online setidaknya sekali sehari.",
          en: "of 12 to 17 year olds in Indonesia used the internet in the past three months; 95% of them go online at least once a day.",
        },
        src: DH_SRC,
        date: "2022",
        url: DH_ID,
      },
      {
        v: { id: "79,5%", en: "79.5%" },
        text: {
          id: "penetrasi internet Indonesia pada 2024, sekitar 221,5 juta pengguna, semua usia.",
          en: "internet penetration in Indonesia in 2024, about 221.5 million users, all ages.",
        },
        src: "APJII",
        date: "2024",
        url: "https://apjii.or.id/berita/d/apjii-jumlah-pengguna-internet-indonesia-tembus-221-juta-orang",
      },
      {
        v: { id: "82%", en: "82%" },
        text: {
          id: "penduduk usia 15 sampai 24 tahun di dunia menggunakan internet, dibanding 72% pada kelompok usia lain.",
          en: "of people aged 15 to 24 worldwide use the internet, against 72% of the rest of the population.",
        },
        src: "ITU, Facts and Figures",
        date: "2025",
        url: "https://www.itu.int/itu-d/reports/statistics/2025/10/15/ff25-youth-internet-use/",
      },
    ],
  },
];
