// Decorative line-and-duotone illustrations for the homepage, drawn in the same single
// stroke weight and navy palette as the page's icons. All are aria-hidden: they carry no
// information the surrounding copy does not already give.

type Props = { className?: string };

const base = "h-auto w-full";

/** A school beside an anonymous class aggregate: a row of identical figures grouped inside a
 * dashed boundary (k-anonymity), summarised as bars on the four-level scale behind a shield.
 * Nothing points to a single child. */
export function SchoolScene({ className = "" }: Props) {
  return (
    <svg
      viewBox="0 0 420 300"
      className={`${base} ${className}`}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {/* ground */}
      <path d="M34 254h352" className="stroke-navy/20" strokeWidth="2" />

      {/* school building */}
      <g className="stroke-navy" strokeWidth="2.4">
        <path d="M72 254V150h132v104" className="fill-navy/[0.05]" />
        <path d="M60 150 138 108l78 42z" className="fill-navy/10" />
        <rect x="122" y="206" width="32" height="48" rx="2" className="fill-navy/[0.12]" />
        <path d="M138 206v48" className="stroke-navy/40" strokeWidth="1.6" />
        <rect x="88" y="170" width="26" height="24" rx="2" className="fill-paper" strokeWidth="1.8" />
        <rect x="162" y="170" width="26" height="24" rx="2" className="fill-paper" strokeWidth="1.8" />
        <path d="M138 108V88" />
        <path d="M138 90h22l-6 7 6 7h-22" className="fill-navy/70" stroke="none" />
      </g>

      {/* aggregate card: bars on the four-level scale, behind a privacy shield */}
      <g>
        <rect x="250" y="96" width="140" height="104" rx="12" className="fill-paper stroke-navy/15" strokeWidth="2" />
        <path d="M268 120h58" className="stroke-navy/25" strokeWidth="3" />
        <rect x="268" y="162" width="16" height="22" rx="3" className="fill-aman" />
        <rect x="292" y="150" width="16" height="34" rx="3" className="fill-perhatian" />
        <rect x="316" y="168" width="16" height="16" rx="3" className="fill-waspada" />
        <rect x="340" y="156" width="16" height="28" rx="3" className="fill-mendesak" />
        {/* shield */}
        <path
          d="M360 104l16 6v10c0 8-6 14-16 17-10-3-16-9-16-17v-10z"
          className="fill-navy/10 stroke-navy"
          strokeWidth="2"
        />
        <path d="M353 120l5 5 9-10" className="stroke-navy" strokeWidth="2.2" />
      </g>

      {/* an anonymous group: identical figures inside a dashed boundary */}
      <g>
        <rect x="250" y="214" width="140" height="44" rx="22" className="stroke-navy/30" strokeWidth="1.6" strokeDasharray="4 6" />
        {[274, 300, 326, 352].map((cx) => (
          <g key={cx} className="fill-navy/15 stroke-navy" strokeWidth="1.6">
            <circle cx={cx} cy="230" r="5.5" />
            <path d={`M${cx - 8} 246c0-6 3.6-9.5 8-9.5s8 3.5 8 9.5`} className="fill-none" />
          </g>
        ))}
      </g>
    </svg>
  );
}

/** One protection covering three areas: a shield with a check over a child's phone, with
 * content, social and privacy badges beneath it. Matches the three feature pillars. */
export function ProtectScene({ className = "" }: Props) {
  return (
    <svg
      viewBox="0 0 420 300"
      className={`${base} ${className}`}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {/* shield with a check */}
      <g className="stroke-navy" strokeWidth="2.6">
        <path d="M210 34l66 23v48c0 46-29 69-66 83-37-14-66-37-66-83V57z" className="fill-navy/[0.05]" />
        <path d="M184 112l18 18 34-40" strokeWidth="3" />
      </g>

      {/* connectors to the three pillars */}
      <path
        d="M172 150c-22 20-44 30-68 40M210 170v34M248 150c22 20 44 30 68 40"
        className="stroke-navy/25"
        strokeWidth="1.6"
        strokeDasharray="3 7"
      />

      {/* content: a site held */}
      <g>
        <circle cx="104" cy="236" r="30" className="fill-paper stroke-navy/15" strokeWidth="2" />
        <g className="stroke-navy" strokeWidth="2">
          <rect x="90" y="224" width="28" height="22" rx="3" className="fill-navy/[0.06]" />
          <path d="M90 231h28" strokeWidth="1.6" />
        </g>
        <circle cx="104" cy="236" r="12" className="stroke-mendesak fill-none" strokeWidth="2.4" />
        <path d="M96 244l16-16" className="stroke-mendesak" strokeWidth="2.4" />
      </g>

      {/* social: a kind conversation */}
      <g>
        <circle cx="210" cy="238" r="30" className="fill-paper stroke-navy/15" strokeWidth="2" />
        <path d="M196 226h28a5 5 0 0 1 5 5v12a5 5 0 0 1-5 5h-15l-9 7v-7a5 5 0 0 1-4-22z" className="fill-navy/[0.06] stroke-navy" strokeWidth="2" />
        <path d="M210 234c-3-4-9-2-9 3 0 4 6 7 9 10 3-3 9-6 9-10 0-5-6-7-9-3z" className="fill-navy/70" stroke="none" />
      </g>

      {/* privacy: a lock */}
      <g>
        <circle cx="316" cy="236" r="30" className="fill-paper stroke-navy/15" strokeWidth="2" />
        <g className="stroke-navy" strokeWidth="2.2">
          <rect x="304" y="234" width="24" height="18" rx="3" className="fill-navy/[0.06]" />
          <path d="M308 234v-5a8 8 0 0 1 16 0v5" />
          <circle cx="316" cy="242" r="2.4" className="fill-navy" stroke="none" />
        </g>
      </g>
    </svg>
  );
}

/** The four steps as one quiet pipeline: on the phone, masked and flagged, assessed by the
 * model, then guidance. Sits above the step cards. */
export function FlowScene({ className = "" }: Props) {
  const nodes = [48, 180, 312, 444];
  return (
    <svg
      viewBox="0 0 492 116"
      className={`${base} ${className}`}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {/* arrows between the nodes */}
      <g className="stroke-navy/30" strokeWidth="2">
        {[[78, 150], [210, 282], [342, 414]].map(([x1, x2]) => (
          <g key={x1}>
            <path d={`M${x1} 58h${x2 - x1 - 8}`} strokeDasharray="2 7" />
            <path d={`M${x2 - 14} 52l6 6-6 6`} className="stroke-navy/55" />
          </g>
        ))}
      </g>

      {nodes.map((cx) => (
        <rect
          key={cx}
          x={cx - 28}
          y={30}
          width="56"
          height="56"
          rx="15"
          className="fill-navy/[0.04] stroke-navy"
          strokeWidth="2.3"
        />
      ))}

      {/* 1. on the phone */}
      <g className="stroke-navy" strokeWidth="2.1">
        <rect x={38} y={42} width="20" height="32" rx="4" className="fill-paper" />
        <path d="M44 48h8" strokeWidth="1.6" />
      </g>

      {/* 2. masked and flagged */}
      <g className="fill-navy/70" stroke="none">
        {[170, 180, 190].map((x) => (
          <circle key={x} cx={x} cy="58" r="3.4" />
        ))}
      </g>

      {/* 3. assessed by the model */}
      <path
        d="M312 42l4.5 11.5 11.5 4.5-11.5 4.5-4.5 11.5-4.5-11.5-11.5-4.5 11.5-4.5z"
        className="fill-navy/15 stroke-navy"
        strokeWidth="2"
      />

      {/* 4. guidance */}
      <g>
        <path d="M430 46h28a4 4 0 0 1 4 4v12a4 4 0 0 1-4 4h-16l-8 6v-6a4 4 0 0 1-4-20z" className="fill-navy/[0.06] stroke-navy" strokeWidth="2" />
        <path d="M444 54c-2.6-3.4-7.6-1.6-7.6 2.6 0 3.4 5 6 7.6 8.4 2.6-2.4 7.6-5 7.6-8.4 0-4.2-5-6-7.6-2.6z" className="fill-navy/70" stroke="none" />
      </g>
    </svg>
  );
}

/** How Meta's models reach the phone: a large teacher model distils into a small student
 * that runs on-device. The lineage, not literal hardware. */
export function ModelsScene({ className = "" }: Props) {
  return (
    <svg
      viewBox="0 0 420 240"
      className={`${base} ${className}`}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {/* teacher: a large node with a spark (Muse Spark) */}
      <g>
        <rect x="34" y="64" width="112" height="112" rx="20" className="fill-navy/[0.06] stroke-navy" strokeWidth="2.4" />
        {/* chip pins */}
        <g className="stroke-navy/40" strokeWidth="2">
          <path d="M56 64V50M90 64V50M124 64V50M56 176v14M90 176v14M124 176v14" />
        </g>
        {/* spark */}
        <path
          d="M90 92l7 19 19 7-19 7-7 19-7-19-19-7 19-7z"
          className="fill-navy/15 stroke-navy"
          strokeWidth="2"
        />
      </g>

      {/* teacher -> student */}
      <path d="M150 120h44" className="stroke-navy/35" strokeWidth="2.2" strokeDasharray="2 7" />
      <path d="M190 114l8 6-8 6" className="stroke-navy/60" strokeWidth="2.2" />

      {/* student: a smaller distilled node (a small network) */}
      <g>
        <rect x="204" y="86" width="72" height="68" rx="14" className="fill-navy/[0.04] stroke-navy" strokeWidth="2.2" />
        <g className="fill-navy stroke-navy" strokeWidth="1.8">
          <path d="M224 104l20 16M244 120l12-12M224 104v24M244 120v16" className="stroke-navy/50 fill-none" />
          <circle cx="224" cy="104" r="4" />
          <circle cx="256" cy="108" r="4" />
          <circle cx="244" cy="120" r="4" />
          <circle cx="224" cy="128" r="4" />
          <circle cx="244" cy="136" r="4" />
        </g>
      </g>

      {/* student -> phone */}
      <path d="M280 120h32" className="stroke-navy/35" strokeWidth="2.2" strokeDasharray="2 7" />
      <path d="M308 114l8 6-8 6" className="stroke-navy/60" strokeWidth="2.2" />

      {/* on-device: the distilled student runs on the phone */}
      <g>
        <rect x="330" y="68" width="60" height="104" rx="13" className="fill-paper stroke-navy" strokeWidth="2.4" />
        <path d="M352 80h16" className="stroke-navy/35" strokeWidth="2.4" />
        <path
          d="M360 104l4.5 12 12 4.5-12 4.5-4.5 12-4.5-12-12-4.5 12-4.5z"
          className="fill-navy/15 stroke-navy"
          strokeWidth="1.8"
        />
      </g>
    </svg>
  );
}
