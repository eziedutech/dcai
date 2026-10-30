// Decorative illustrations for the homepage, in the page's navy palette: soft gradients, a
// gentle drop shadow and a faint backdrop glow, one stroke weight throughout. All are
// aria-hidden; the surrounding copy carries the meaning. They sit on the page background,
// never inside a card.

type Props = { className?: string };

const NAVY = "#1f3a5f";
const NAVY_2 = "#2f5486";
const INK = "#14233a";
const LINE = "#d8dfe6";
const MIST = "#eef2f6";
const AMAN = "#2f6b4f";
const PERHATIAN = "#b07a12";
const WASPADA = "#c45a1f";
const MENDESAK = "#9e2b25";

const svgBase = "h-auto w-full overflow-visible";

/** Shared defs: a soft shadow and the navy gradient, with ids namespaced per illustration. */
function Defs({ id }: { id: string }) {
  return (
    <defs>
      <filter id={`${id}-shadow`} x="-30%" y="-30%" width="160%" height="170%">
        <feDropShadow dx="0" dy="12" stdDeviation="12" floodColor={INK} floodOpacity="0.14" />
      </filter>
      <filter id={`${id}-shadow-sm`} x="-30%" y="-30%" width="160%" height="170%">
        <feDropShadow dx="0" dy="6" stdDeviation="6" floodColor={INK} floodOpacity="0.12" />
      </filter>
      <linearGradient id={`${id}-navy`} x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor={NAVY_2} />
        <stop offset="1" stopColor={NAVY} />
      </linearGradient>
      <linearGradient id={`${id}-paper`} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#ffffff" />
        <stop offset="1" stopColor={MIST} />
      </linearGradient>
      <radialGradient id={`${id}-glow`}>
        <stop offset="0" stopColor={NAVY} stopOpacity="0.13" />
        <stop offset="1" stopColor={NAVY} stopOpacity="0" />
      </radialGradient>
      <radialGradient id={`${id}-teal`}>
        <stop offset="0" stopColor="#3c7a86" stopOpacity="0.12" />
        <stop offset="1" stopColor="#3c7a86" stopOpacity="0" />
      </radialGradient>
    </defs>
  );
}

/** A four-point sparkle, the page's small accent. */
function Sparkle({ x, y, r = 6, opacity = 0.35 }: { x: number; y: number; r?: number; opacity?: number }) {
  return (
    <path
      d={`M${x} ${y - r}l${r * 0.28} ${r * 0.72} ${r * 0.72} ${r * 0.28}-${r * 0.72} ${r * 0.28}-${r * 0.28} ${r * 0.72}-${r * 0.28}-${r * 0.72}-${r * 0.72}-${r * 0.28} ${r * 0.72}-${r * 0.28}z`}
      fill={NAVY}
      opacity={opacity}
    />
  );
}

/** The navy shield with a white check, used as the protection badge. */
function ShieldBadge({ id, x, y, s = 1 }: { id: string; x: number; y: number; s?: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`} filter={`url(#${id}-shadow-sm)`}>
      <path d="M0-30 26-20v18C26 16 15 27 0 32-15 27-26 16-26-2v-18z" fill={`url(#${id}-navy)`} />
      <path d="M-10 1 -3 8 11-7" stroke="#fff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </g>
  );
}

/** Feature pillars: a child's phone with a calm chat and a nudge, under a protection badge,
 * with three floating chips for content, social and privacy. */
export function ProtectScene({ className = "" }: Props) {
  const id = "ps";
  return (
    <svg viewBox="0 0 440 340" className={`${svgBase} ${className}`} fill="none" aria-hidden>
      <Defs id={id} />
      <circle cx="220" cy="175" r="170" fill={`url(#${id}-glow)`} />
      <circle cx="330" cy="250" r="110" fill={`url(#${id}-teal)`} />
      <ellipse cx="220" cy="190" rx="190" ry="78" stroke={NAVY} strokeOpacity="0.16" strokeWidth="1.5" strokeDasharray="3 8" />

      {/* phone */}
      <g filter={`url(#${id}-shadow)`}>
        <rect x="160" y="56" width="120" height="228" rx="26" fill={INK} />
        <rect x="167" y="63" width="106" height="214" rx="20" fill="#f4f6f9" />
      </g>
      <rect x="203" y="70" width="34" height="7" rx="3.5" fill={INK} />
      {/* chat */}
      <rect x="176" y="96" width="62" height="18" rx="9" fill="#fff" stroke={LINE} />
      <rect x="208" y="122" width="54" height="18" rx="9" fill={NAVY} />
      <rect x="176" y="148" width="48" height="18" rx="9" fill="#fff" stroke={LINE} />
      {/* nudge card */}
      <g filter={`url(#${id}-shadow-sm)`}>
        <rect x="176" y="180" width="88" height="56" rx="12" fill="#fff" />
      </g>
      <rect x="176" y="180" width="4" height="56" rx="2" fill={AMAN} />
      <circle cx="194" cy="196" r="7" fill={AMAN} fillOpacity="0.15" />
      <path d="M190.5 196l2.6 2.6 4.6-5" stroke={AMAN} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="206" y="192" width="46" height="6" rx="3" fill={INK} fillOpacity="0.7" />
      <rect x="188" y="210" width="66" height="5" rx="2.5" fill={INK} fillOpacity="0.18" />
      <rect x="188" y="221" width="50" height="5" rx="2.5" fill={INK} fillOpacity="0.18" />
      <rect x="176" y="250" width="88" height="16" rx="8" fill="#fff" stroke={LINE} />

      <ShieldBadge id={id} x={286} y={74} s={1.1} />

      {/* chip: content held */}
      <g filter={`url(#${id}-shadow-sm)`}>
        <rect x="34" y="104" width="112" height="48" rx="14" fill="#fff" />
      </g>
      <rect x="44" y="114" width="28" height="28" rx="9" fill={MENDESAK} fillOpacity="0.1" />
      <circle cx="58" cy="128" r="8" stroke={MENDESAK} strokeWidth="2" />
      <path d="M52.5 133.5l11-11" stroke={MENDESAK} strokeWidth="2" strokeLinecap="round" />
      <rect x="80" y="120" width="52" height="6" rx="3" fill={INK} fillOpacity="0.65" />
      <rect x="80" y="132" width="36" height="5" rx="2.5" fill={INK} fillOpacity="0.2" />

      {/* chip: kind interactions */}
      <g filter={`url(#${id}-shadow-sm)`}>
        <rect x="26" y="226" width="112" height="48" rx="14" fill="#fff" />
      </g>
      <rect x="36" y="236" width="28" height="28" rx="9" fill={AMAN} fillOpacity="0.12" />
      <path d="M50 255c-4-3.4-8-6-8-9.6 0-2.6 2-4.4 4.3-4.4 1.6 0 3 .9 3.7 2.2.7-1.3 2.1-2.2 3.7-2.2 2.3 0 4.3 1.8 4.3 4.4 0 3.6-4 6.2-8 9.6z" fill={AMAN} />
      <rect x="72" y="242" width="52" height="6" rx="3" fill={INK} fillOpacity="0.65" />
      <rect x="72" y="254" width="38" height="5" rx="2.5" fill={INK} fillOpacity="0.2" />

      {/* chip: privacy */}
      <g filter={`url(#${id}-shadow-sm)`}>
        <rect x="304" y="200" width="112" height="48" rx="14" fill="#fff" />
      </g>
      <rect x="314" y="210" width="28" height="28" rx="9" fill={NAVY} fillOpacity="0.1" />
      <rect x="320.5" y="223" width="15" height="11" rx="2.5" fill={NAVY} />
      <path d="M323.5 223v-3a4.5 4.5 0 0 1 9 0v3" stroke={NAVY} strokeWidth="2" />
      <rect x="350" y="216" width="52" height="6" rx="3" fill={INK} fillOpacity="0.65" />
      <rect x="350" y="228" width="40" height="5" rx="2.5" fill={INK} fillOpacity="0.2" />

      <Sparkle x={366} y={140} r={8} />
      <Sparkle x={112} y={196} r={5} opacity={0.25} />
      <Sparkle x={392} y={290} r={5} opacity={0.25} />
    </svg>
  );
}

/** One of the four "how it works" steps, drawn as a tile so the four line up with the step
 * cards beneath them. */
export function StepIcon({ n, className = "" }: Props & { n: 1 | 2 | 3 | 4 }) {
  const id = `st${n}`;
  return (
    <svg viewBox="0 0 160 120" className={`${svgBase} ${className}`} fill="none" aria-hidden>
      <Defs id={id} />
      <circle cx="80" cy="60" r="58" fill={`url(#${id}-glow)`} />
      <g filter={`url(#${id}-shadow)`}>
        <rect x="40" y="20" width="80" height="80" rx="24" fill={`url(#${id}-paper)`} />
      </g>
      <rect x="40.5" y="20.5" width="79" height="79" rx="23.5" stroke={NAVY} strokeOpacity="0.12" />

      {n === 1 && (
        <g>
          {/* on the phone: text masked before it leaves */}
          <rect x="62" y="34" width="36" height="54" rx="8" fill={INK} />
          <rect x="65.5" y="38" width="29" height="46" rx="5" fill="#f4f6f9" />
          <rect x="69" y="46" width="18" height="5" rx="2.5" fill={INK} fillOpacity="0.55" />
          <g fill={NAVY}>
            <circle cx="71" cy="59" r="2.4" />
            <circle cx="77.5" cy="59" r="2.4" />
            <circle cx="84" cy="59" r="2.4" />
          </g>
          <rect x="69" y="67" width="14" height="5" rx="2.5" fill={INK} fillOpacity="0.3" />
          <circle cx="100" cy="38" r="10" fill={`url(#${id}-navy)`} />
          <path d="M96 38.5l2.6 2.6 5-5.2" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </g>
      )}

      {n === 2 && (
        <g>
          {/* only the flagged message is sent */}
          <rect x="56" y="36" width="48" height="11" rx="5.5" fill={INK} fillOpacity="0.12" />
          <rect x="56" y="54" width="48" height="12" rx="6" fill={PERHATIAN} fillOpacity="0.16" stroke={PERHATIAN} strokeWidth="1.6" />
          <rect x="62" y="58" width="22" height="4" rx="2" fill={PERHATIAN} />
          <rect x="56" y="73" width="48" height="11" rx="5.5" fill={INK} fillOpacity="0.12" />
          <path d="M108 50v20" stroke={PERHATIAN} strokeWidth="2" strokeLinecap="round" />
          <path d="M108 51h10l-3 4 3 4h-10" fill={PERHATIAN} />
        </g>
      )}

      {n === 3 && (
        <g>
          {/* assessed as a pattern across messages */}
          <path d="M54 76l14-12 14 6 16-20" stroke={NAVY} strokeOpacity="0.35" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <g fill={NAVY} fillOpacity="0.45">
            <circle cx="54" cy="76" r="3.4" />
            <circle cx="68" cy="64" r="3.4" />
            <circle cx="82" cy="70" r="3.4" />
          </g>
          <path d="M98 34l5 13 13 5-13 5-5 13-5-13-13-5 13-5z" fill={`url(#${id}-navy)`} />
          <g>
            <rect x="56" y="86" width="10" height="5" rx="2.5" fill={AMAN} />
            <rect x="69" y="86" width="10" height="5" rx="2.5" fill={PERHATIAN} />
            <rect x="82" y="86" width="10" height="5" rx="2.5" fill={WASPADA} />
            <rect x="95" y="86" width="10" height="5" rx="2.5" fill={MENDESAK} fillOpacity="0.3" />
          </g>
        </g>
      )}

      {n === 4 && (
        <g>
          {/* guidance: a short nudge for the child, starters for the parent */}
          <path d="M52 40h30a6 6 0 0 1 6 6v8a6 6 0 0 1-6 6H64l-8 6v-6h-4a6 6 0 0 1-6-6v-8a6 6 0 0 1 6-6z" fill={AMAN} fillOpacity="0.14" />
          <rect x="54" y="47" width="26" height="4.5" rx="2.25" fill={AMAN} />
          <g filter={`url(#${id}-shadow-sm)`}>
            <rect x="70" y="56" width="42" height="34" rx="9" fill="#fff" />
          </g>
          <rect x="76" y="63" width="22" height="4.5" rx="2.25" fill={NAVY} />
          <rect x="76" y="72" width="30" height="4" rx="2" fill={INK} fillOpacity="0.2" />
          <rect x="76" y="80" width="24" height="4" rx="2" fill={INK} fillOpacity="0.2" />
          <path d="M106 52c-3-2.6-6-4.5-6-7.2 0-2 1.5-3.3 3.2-3.3 1.2 0 2.3.7 2.8 1.6.5-.9 1.6-1.6 2.8-1.6 1.7 0 3.2 1.3 3.2 3.3 0 2.7-3 4.6-6 7.2z" fill={NAVY} />
        </g>
      )}
    </svg>
  );
}

/** A school beside its anonymous class overview: counts on the four-level scale behind a
 * shield, and a group of identical figures inside a dashed boundary. No single child. */
export function SchoolScene({ className = "" }: Props) {
  const id = "ss";
  return (
    <svg viewBox="0 0 460 340" className={`${svgBase} ${className}`} fill="none" aria-hidden>
      <Defs id={id} />
      <linearGradient id={`${id}-wall`} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#ffffff" />
        <stop offset="1" stopColor="#e7edf4" />
      </linearGradient>
      <linearGradient id={`${id}-glass`} x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#dbe6f3" />
        <stop offset="1" stopColor="#c3d3e7" />
      </linearGradient>
      <circle cx="170" cy="190" r="160" fill={`url(#${id}-glow)`} />
      <circle cx="350" cy="120" r="110" fill={`url(#${id}-teal)`} />

      {/* ground */}
      <ellipse cx="160" cy="288" rx="150" ry="14" fill={INK} fillOpacity="0.06" />

      {/* trees */}
      <g>
        <rect x="35" y="244" width="5" height="40" rx="2" fill={NAVY} fillOpacity="0.35" />
        <circle cx="37.5" cy="236" r="22" fill={AMAN} fillOpacity="0.16" />
        <circle cx="30" cy="242" r="14" fill={AMAN} fillOpacity="0.14" />
        <rect x="281" y="250" width="5" height="34" rx="2" fill={NAVY} fillOpacity="0.35" />
        <circle cx="283.5" cy="244" r="18" fill={AMAN} fillOpacity="0.16" />
      </g>

      {/* building */}
      <g filter={`url(#${id}-shadow)`}>
        <rect x="66" y="160" width="190" height="124" rx="6" fill={`url(#${id}-wall)`} />
        <path d="M52 166 161 104l109 62z" fill={`url(#${id}-navy)`} />
      </g>
      <rect x="66.5" y="160.5" width="189" height="123" rx="5.5" stroke={NAVY} strokeOpacity="0.15" />
      <circle cx="161" cy="142" r="11" fill="#fff" fillOpacity="0.9" />
      <path d="M161 136v6l4 2.5" stroke={NAVY} strokeWidth="1.8" strokeLinecap="round" />
      {/* windows */}
      {[84, 120, 180, 216].map((x) => (
        <g key={x}>
          <rect x={x} y="184" width="24" height="26" rx="3" fill={`url(#${id}-glass)`} />
          <path d={`M${x + 12} 184v26M${x} 197h24`} stroke="#fff" strokeOpacity="0.8" strokeWidth="1.4" />
          <rect x={x} y="226" width="24" height="26" rx="3" fill={`url(#${id}-glass)`} />
          <path d={`M${x + 12} 226v26M${x} 239h24`} stroke="#fff" strokeOpacity="0.8" strokeWidth="1.4" />
        </g>
      ))}
      {/* door */}
      <rect x="146" y="234" width="30" height="50" rx="3" fill={`url(#${id}-navy)`} />
      <circle cx="170" cy="260" r="1.8" fill="#fff" />
      <rect x="138" y="282" width="46" height="5" rx="2" fill={NAVY} fillOpacity="0.2" />
      {/* flag */}
      <path d="M161 104V66" stroke={NAVY} strokeWidth="2.4" strokeLinecap="round" />
      <path d="M161 68h26l-6 7 6 7h-26z" fill={`url(#${id}-navy)`} />

      {/* link from the school to its overview */}
      <path d="M262 174c22-6 28-28 40-40" stroke={NAVY} strokeOpacity="0.3" strokeWidth="1.6" strokeDasharray="3 7" strokeLinecap="round" />

      {/* overview card */}
      <g filter={`url(#${id}-shadow)`}>
        <rect x="290" y="40" width="152" height="122" rx="16" fill="#fff" />
      </g>
      <rect x="306" y="56" width="54" height="7" rx="3.5" fill={INK} fillOpacity="0.7" />
      <rect x="306" y="69" width="34" height="5" rx="2.5" fill={INK} fillOpacity="0.2" />
      <path d="M306 146h120" stroke={LINE} strokeWidth="1.5" />
      <rect x="310" y="114" width="20" height="32" rx="4" fill={AMAN} />
      <rect x="338" y="98" width="20" height="48" rx="4" fill={PERHATIAN} />
      <rect x="366" y="122" width="20" height="24" rx="4" fill={WASPADA} />
      <rect x="394" y="130" width="20" height="16" rx="4" fill={MENDESAK} />
      <ShieldBadge id={id} x={430} y={46} s={0.78} />

      {/* the anonymous group */}
      <g filter={`url(#${id}-shadow-sm)`}>
        <rect x="290" y="190" width="152" height="62" rx="31" fill="#fff" />
      </g>
      <rect x="298" y="198" width="136" height="46" rx="23" stroke={NAVY} strokeOpacity="0.3" strokeWidth="1.5" strokeDasharray="4 6" />
      {[318, 344, 370, 396].map((cx) => (
        <g key={cx}>
          <circle cx={cx} cy="214" r="6" fill={NAVY} fillOpacity="0.75" />
          <path d={`M${cx - 9} 233c0-6.5 4-10 9-10s9 3.5 9 10z`} fill={NAVY} fillOpacity="0.3" />
        </g>
      ))}
      <circle cx="420" cy="221" r="8" fill={NAVY} fillOpacity="0.1" />
      <path d="M416 221h8M420 217v8" stroke={NAVY} strokeWidth="1.8" strokeLinecap="round" />

      <Sparkle x={274} y={60} r={7} />
      <Sparkle x={448} y={186} r={5} opacity={0.25} />
    </svg>
  );
}

/** Meta's models in dcAI: a masked message from the phone is screened by the distilled Llama
 * student, flagged ones are assessed by Muse Spark, and Muse Spark as the teacher labels the
 * data the student learns from (the loop above). Both models run on the server. */
export function ModelsScene({ className = "" }: Props) {
  const id = "ms";
  return (
    <svg viewBox="0 0 460 300" className={`${svgBase} ${className}`} fill="none" aria-hidden>
      <Defs id={id} />
      <radialGradient id={`${id}-spark`}>
        <stop offset="0" stopColor="#ffffff" stopOpacity="0.55" />
        <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
      </radialGradient>
      <circle cx="300" cy="170" r="160" fill={`url(#${id}-glow)`} />
      <circle cx="90" cy="200" r="100" fill={`url(#${id}-teal)`} />
      <ellipse cx="250" cy="268" rx="200" ry="12" fill={INK} fillOpacity="0.05" />

      {/* distillation loop: the teacher labels data the student learns from */}
      <path d="M368 96C368 26 206 26 206 100" stroke={NAVY} strokeOpacity="0.35" strokeWidth="1.8" strokeDasharray="3 7" strokeLinecap="round" />
      <path d="M200 92l6 9 6-9" stroke={NAVY} strokeOpacity="0.6" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <g filter={`url(#${id}-shadow-sm)`}>
        <rect x="262" y="34" width="52" height="30" rx="9" fill="#fff" />
      </g>
      <rect x="270" y="42" width="16" height="4" rx="2" fill={NAVY} fillOpacity="0.6" />
      <rect x="270" y="50" width="22" height="4" rx="2" fill={NAVY} fillOpacity="0.25" />
      <circle cx="302" cy="49" r="6" fill={AMAN} fillOpacity="0.15" />
      <path d="M299.4 49l1.8 1.8 3.4-3.6" stroke={AMAN} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />

      {/* phone: a masked message leaves */}
      <g filter={`url(#${id}-shadow)`}>
        <rect x="22" y="104" width="70" height="128" rx="16" fill={INK} />
        <rect x="27" y="109" width="60" height="118" rx="12" fill="#f4f6f9" />
      </g>
      <rect x="34" y="128" width="40" height="13" rx="6.5" fill="#fff" stroke={LINE} />
      <rect x="44" y="148" width="36" height="13" rx="6.5" fill={NAVY} />
      <g fill={NAVY} fillOpacity="0.8">
        <circle cx="44" cy="177" r="2.6" />
        <circle cx="51" cy="177" r="2.6" />
        <circle cx="58" cy="177" r="2.6" />
      </g>
      <rect x="34" y="169" width="34" height="16" rx="8" stroke={NAVY} strokeOpacity="0.3" strokeDasharray="2 3" />

      {/* phone -> student */}
      <path d="M100 168h44" stroke={NAVY} strokeOpacity="0.35" strokeWidth="1.8" strokeDasharray="3 7" strokeLinecap="round" />
      <path d="M140 162l7 6-7 6" stroke={NAVY} strokeOpacity="0.6" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />

      {/* student: Llama 3.1 8B, the screener */}
      <g stroke={NAVY} strokeOpacity="0.35" strokeWidth="2" strokeLinecap="round">
        <path d="M178 112v-8M206 112v-8M234 112v-8M178 224v8M206 224v8M234 224v8" />
      </g>
      <g filter={`url(#${id}-shadow)`}>
        <rect x="158" y="112" width="96" height="112" rx="22" fill={`url(#${id}-paper)`} />
      </g>
      <rect x="158.5" y="112.5" width="95" height="111" rx="21.5" stroke={NAVY} strokeOpacity="0.18" />
      <g stroke={NAVY} strokeOpacity="0.4" strokeWidth="1.6">
        <path d="M184 146l22 22 22-22M184 190l22-22 22 22M206 146v44" />
      </g>
      <g fill={NAVY}>
        <circle cx="184" cy="146" r="5" />
        <circle cx="228" cy="146" r="5" />
        <circle cx="206" cy="168" r="6.5" />
        <circle cx="184" cy="190" r="5" />
        <circle cx="228" cy="190" r="5" />
      </g>
      <text x="206" y="252" textAnchor="middle" fontSize="12.5" fontWeight="700" fill={INK}>Llama 3.1 8B</text>

      {/* student -> teacher, for flagged messages */}
      <path d="M262 168h30" stroke={NAVY} strokeOpacity="0.35" strokeWidth="1.8" strokeDasharray="3 7" strokeLinecap="round" />
      <path d="M288 162l7 6-7 6" stroke={NAVY} strokeOpacity="0.6" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />

      {/* teacher: Muse Spark */}
      <g stroke={NAVY} strokeOpacity="0.35" strokeWidth="2" strokeLinecap="round">
        <path d="M334 100v-8M368 100v-8M402 100v-8M334 236v8M368 236v8M402 236v8" />
      </g>
      <g filter={`url(#${id}-shadow)`}>
        <rect x="302" y="100" width="132" height="136" rx="28" fill={`url(#${id}-navy)`} />
      </g>
      <circle cx="368" cy="168" r="52" fill={`url(#${id}-spark)`} />
      <path d="M368 130l9.5 28.5 28.5 9.5-28.5 9.5-9.5 28.5-9.5-28.5-28.5-9.5 28.5-9.5z" fill="#fff" />
      <path d="M404 120l3 7.5 7.5 3-7.5 3-3 7.5-3-7.5-7.5-3 7.5-3z" fill="#fff" fillOpacity="0.6" />
      <text x="368" y="264" textAnchor="middle" fontSize="12.5" fontWeight="700" fill={INK}>Muse Spark</text>

      <Sparkle x={128} y={90} r={6} />
      <Sparkle x={446} y={210} r={5} opacity={0.25} />
    </svg>
  );
}

/** The next platforms: the same dcAI engine across a desktop, a laptop and a tablet, held
 * together by one shield and one backend (the dashed arc). Devices, not a literal product. */
export function DevicesScene({ className = "" }: Props) {
  const id = "dv";
  return (
    <svg viewBox="0 0 460 300" className={`${svgBase} ${className}`} fill="none" aria-hidden>
      <Defs id={id} />
      <circle cx="230" cy="150" r="170" fill={`url(#${id}-glow)`} />
      <circle cx="360" cy="210" r="110" fill={`url(#${id}-teal)`} />

      {/* one backend ties them together */}
      <path d="M96 150C150 70 310 70 372 150" stroke={NAVY} strokeOpacity="0.28" strokeWidth="1.6" strokeDasharray="3 8" strokeLinecap="round" />

      <ellipse cx="232" cy="256" rx="180" ry="13" fill={INK} fillOpacity="0.05" />

      {/* desktop monitor (Windows) */}
      <g filter={`url(#${id}-shadow)`}>
        <rect x="150" y="70" width="164" height="110" rx="12" fill={`url(#${id}-paper)`} />
      </g>
      <rect x="150.5" y="70.5" width="163" height="109" rx="11.5" stroke={NAVY} strokeOpacity="0.16" />
      <rect x="164" y="84" width="60" height="7" rx="3.5" fill={INK} fillOpacity="0.5" />
      <rect x="164" y="100" width="136" height="6" rx="3" fill={INK} fillOpacity="0.14" />
      <rect x="164" y="114" width="118" height="6" rx="3" fill={INK} fillOpacity="0.14" />
      <rect x="164" y="128" width="92" height="6" rx="3" fill={INK} fillOpacity="0.14" />
      <rect x="210" y="180" width="44" height="26" fill={INK} fillOpacity="0.14" />
      <rect x="182" y="206" width="100" height="8" rx="4" fill={NAVY} fillOpacity="0.2" />

      {/* laptop (macOS) */}
      <g filter={`url(#${id}-shadow-sm)`}>
        <rect x="320" y="150" width="104" height="70" rx="9" fill={`url(#${id}-paper)`} />
      </g>
      <rect x="320.5" y="150.5" width="103" height="69" rx="8.5" stroke={NAVY} strokeOpacity="0.16" />
      <rect x="332" y="162" width="34" height="5" rx="2.5" fill={INK} fillOpacity="0.5" />
      <rect x="332" y="174" width="80" height="4.5" rx="2.25" fill={INK} fillOpacity="0.14" />
      <rect x="332" y="185" width="64" height="4.5" rx="2.25" fill={INK} fillOpacity="0.14" />
      <rect x="332" y="196" width="72" height="4.5" rx="2.25" fill={INK} fillOpacity="0.14" />
      <path d="M312 230h120l-6-10h-108z" fill={`url(#${id}-paper)`} stroke={NAVY} strokeOpacity="0.16" />

      {/* tablet / phone (iOS) */}
      <g filter={`url(#${id}-shadow)`}>
        <rect x="40" y="128" width="86" height="118" rx="16" fill={INK} />
        <rect x="45" y="133" width="76" height="108" rx="12" fill="#f4f6f9" />
      </g>
      <rect x="74" y="140" width="18" height="5" rx="2.5" fill={INK} />
      <rect x="55" y="156" width="40" height="6" rx="3" fill={INK} fillOpacity="0.5" />
      <rect x="55" y="170" width="56" height="5" rx="2.5" fill={INK} fillOpacity="0.14" />
      <rect x="55" y="182" width="44" height="5" rx="2.5" fill={INK} fillOpacity="0.14" />
      <rect x="55" y="205" width="56" height="20" rx="10" fill={NAVY} fillOpacity="0.14" />

      {/* one shield over all three */}
      <ShieldBadge id={id} x={232} y={150} s={1.25} />

      <Sparkle x={126} y={96} r={7} />
      <Sparkle x={398} y={120} r={5} opacity={0.25} />
      <Sparkle x={300} y={250} r={5} opacity={0.25} />
    </svg>
  );
}

/** The flow above the four step cards: a dashed track with one tile per step, laid out on
 * the same grid as the cards so each tile sits over its card. */
export function StepsFlow() {
  return (
    <div aria-hidden className="relative mt-10 hidden lg:block">
      <div className="absolute top-1/2 right-[12.5%] left-[12.5%] -translate-y-1/2 border-t-2 border-dashed border-navy/15" />
      <div className="relative grid grid-cols-4 gap-5">
        {([1, 2, 3, 4] as const).map((n) => (
          <StepIcon key={n} n={n} className="mx-auto max-w-[11rem]" />
        ))}
      </div>
    </div>
  );
}
