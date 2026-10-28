"use client";

import { useEffect, useRef } from "react";

// One passive scroll listener for the whole page, transforms written on the next animation
// frame. An element with an anchor moves by its anchor's distance from the middle of the
// screen times speed, so depth looks the same anywhere on the page; one without (the fixed
// background) moves by scrollY times speed. Nothing moves when the reader asks for reduced
// motion.
type Target = { speed: number; anchor: HTMLElement | null };
const targets = new Map<HTMLElement, Target>();
let frame = 0;
let listening = false;

function apply() {
  frame = 0;
  const y = window.scrollY;
  const mid = window.innerHeight / 2;
  // All reads first, then all writes, so the frame never forces a second layout.
  const moves: [HTMLElement, number][] = [];
  targets.forEach(({ speed, anchor }, el) => {
    if (!anchor) return moves.push([el, y * speed]);
    const r = anchor.getBoundingClientRect();
    if (r.bottom < -200 || r.top > window.innerHeight + 200) return;
    moves.push([el, -(r.top + r.height / 2 - mid) * speed]);
  });
  for (const [el, px] of moves) el.style.transform = `translate3d(0, ${px.toFixed(1)}px, 0)`;
}

function onScroll() {
  if (!frame) frame = requestAnimationFrame(apply);
}

function register(el: HTMLElement, speed: number, anchor: HTMLElement | null = null) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return () => undefined;
  targets.set(el, { speed, anchor });
  if (!listening) {
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    listening = true;
  }
  onScroll();
  return () => {
    targets.delete(el);
    if (!targets.size && listening) {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      listening = false;
    }
  };
}

/** A block that drifts against the scroll. Small speeds (0.03 to 0.12) read as depth:
 * positive lags behind the page, negative runs ahead of it. The outer box keeps the layout
 * and is measured; only the inner box moves. */
export function Parallax({
  speed,
  className = "",
  children,
}: {
  speed: number;
  className?: string;
  children?: React.ReactNode;
}) {
  const outer = useRef<HTMLDivElement>(null);
  const inner = useRef<HTMLDivElement>(null);
  useEffect(
    () => (inner.current && outer.current ? register(inner.current, speed, outer.current) : undefined),
    [speed],
  );
  return (
    <div ref={outer} className={className}>
      <div ref={inner} data-parallax className="h-full">
        {children}
      </div>
    </div>
  );
}

/** The quiet background behind every page: three soft colour fields at different depths. */
export function Scene() {
  const navy = useRef<HTMLDivElement>(null);
  const teal = useRef<HTMLDivElement>(null);
  const sand = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const offs = [
      navy.current && register(navy.current, -0.04),
      teal.current && register(teal.current, -0.07),
      sand.current && register(sand.current, -0.02),
    ];
    return () => offs.forEach((off) => off && off());
  }, []);
  return (
    <div aria-hidden className="scene">
      <div ref={navy} className="scene-field navy" />
      <div ref={teal} className="scene-field teal" />
      <div ref={sand} className="scene-field sand" />
    </div>
  );
}
