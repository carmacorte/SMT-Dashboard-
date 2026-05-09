# SMTINEL — Technical Specification

## Dependencies

### Production

| Package | Version | Purpose |
|---------|---------|---------|
| react | ^19.0.0 | UI framework |
| react-dom | ^19.0.0 | React DOM renderer |
| gsap | ^3.12.7 | Animation engine, timelines, ScrollTrigger, SplitText, DrawSVG |
| lenis | ^1.2.3 | Virtual smooth scrolling |
| imagesloaded | ^5.0.0 | Image preload detection for video backgrounds |

### Development

| Package | Version | Purpose |
|---------|---------|---------|
| vite | ^6.3.0 | Build tool |
| @vitejs/plugin-react | ^4.4.0 | React plugin for Vite |
| tailwindcss | ^4.1.0 | Utility CSS framework |
| @tailwindcss/vite | ^4.1.0 | Tailwind Vite integration |
| typescript | ^5.7.0 | Type checking |
| @types/react | ^19.0.0 | React type definitions |
| @types/react-dom | ^19.0.0 | React DOM type definitions |
| @types/imagesloaded | ^4.2.6 | imagesloaded type definitions |

---

## Component Inventory

### Layout

| Component | Source | Reuse | Notes |
|-----------|--------|-------|-------|
| CustomCursor | Custom | Global singleton | Desktop-only, RAF-driven lerp tracking. Three states: dot (default), circle (interactive hover), I-beam (text hover). Includes ghost trail system. Disabled on touch devices. |
| RadialNav | Custom | Global singleton | Desktop: radial satellite menu (210° arc, 5 items). Mobile: slide-in panel (320px). Menu button bounces in on load with elastic ease. |
| SmoothScrollProvider | Custom | Global wrapper | Initializes Lenis, connects to GSAP ScrollTrigger ticker. Wraps the entire app. |

### Sections

| Component | Source | Notes |
|-----------|--------|-------|
| IntroSection | Custom | Orchestrated 12s GSAP timeline (radar sweep + content reveal). NOT scroll-driven — plays on mount. |
| MissionSection | Custom | Two-column with left text + right video. Watermark "S" decorative element. |
| FeaturesSection | Custom | Scroll-driven pinned panels (3). Contains internal Sidebar + ProgressBar. |
| TechnologySection | Custom | WebGL shader canvas + 5 floating stat cards. |
| DiagramSection | Custom | SVG ring chart (5 segments) + numbered step list. |
| ContactSection | Custom | Form + company info. Glassmorphic panels. |
| Footer | Custom | Minimal two-column footer. |

### Shared Components

| Component | Source | Reuse | Notes |
|-----------|--------|-------|-------|
| GlassPanel | Custom | Tech stats, Contact form, Direct Access | Glassmorphic surface: rgba(19,21,23,0.85) + backdrop-filter blur(12px) + 1px White 4 border |
| LabelTag | Custom | All sections | Green label with optional dot prefix. Bebas Neue, 0.75rem. |
| PrimaryButton | Custom | All sections | Green CTA button with hover glow. |
| GhostButton | Custom | Intro, Contact | Transparent bordered button. |
| FormInput | Custom | Contact | Underline-style input with focus glow animation. |

### Hooks

| Hook | Purpose |
|------|---------|
| useMousePosition | Returns normalized mouse coords, used by cursor + shader |
| useLenis | Access Lenis instance for scroll-to and scroll callbacks |
| useMediaQuery | Responsive breakpoint detection (desktop/tablet/mobile) |

---

## Animation Implementation

| Animation | Library | Implementation Approach | Complexity |
|-----------|---------|------------------------|------------|
| Radar sweep intro (Phase 1) | GSAP timeline | SVG `<rect>` clip-path sweep, `x: -2 → 102` over 4s linear. Dark overlay rect clipped by text path. | 🔒 High |
| Content reveal (Phase 2) | GSAP timeline | Chained timeline with absolute delays (4s–7s). Word-by-word headline split via SplitText. Radar display scales with elastic ease. | 🔒 High |
| Hero radar continuous | CSS animation | `@keyframes`: sweep arm `rotate(360deg)` 4s linear infinite. Blip opacity pulses via staggered CSS delays. Ring scale pulse 3s ease-in-out infinite. | Low |
| Mission entrance | GSAP ScrollTrigger | Single trigger at 30% threshold. Timeline with staggered elements (label → headline words → body → CTA → video → caption). | Medium |
| Features panel scroll-sequence | GSAP ScrollTrigger | **Pin** each panel for `100vh` of scroll distance. Per-panel entrance timeline (video scale → label → headline → description → bullet points). Progress bar height maps to scrub progress across all 3 panels combined. | 🔒 High |
| Features sidebar active state | ScrollTrigger callbacks | `onEnter` / `onLeaveBack` per panel trigger updates active sidebar item index. CSS transition for border-color and text color. | Low |
| WebGL particle shader | Raw WebGL | Full-viewport canvas with custom vertex/fragment shaders (provided in design). RAF loop updates `u_time` uniform. Mouse position drives `u_mouse` for particle repulsion. Particle count reduced to 80 on mobile via uniform. | 🔒 High |
| Shader canvas entrance | GSAP ScrollTrigger | Fade in canvas opacity 0→1 over 1.2s at viewport entry. | Low |
| Stat card floating | CSS animation | `@keyframes translateY ±6px`, 4–6s duration, staggered per card via animation-delay. Infinite ease-in-out. | Low |
| Stat card entrance | GSAP ScrollTrigger | Staggered fade-in + translateY, 0.15s stagger, 0.6s each. | Low |
| Ring chart segment reveal | GSAP DrawSVG | Animate `stroke-dashoffset` from full circumference to 0 per segment. Staggered 0.15s clockwise from top. Combined with scale + rotation entrance. | Medium |
| Ring chart slow rotation | CSS animation | `@keyframes rotate(360deg)`, 120s linear infinite. Counter-rotate center text with same animation. | Low |
| Diagram entrance | GSAP ScrollTrigger | Multi-step timeline: headline → label → ring chart scale/rotate → segments draw → steps stagger → legend. | Medium |
| Contact entrance | GSAP ScrollTrigger | Timeline: headline → label → form container → fields stagger → access panel → info stagger → social icons stagger. | Medium |
| Form focus animation | CSS transition | Label translateY(-4px) + scale(0.85) + color change. Border-bottom-color transition. | Low |
| Custom cursor system | Custom (RAF) | requestAnimationFrame loop with lerp (factor 0.15) for smooth follow. State machine for 3 cursor types. 3–4 ghost trail dots rendered at delayed positions. | Medium |
| Radial menu satellite orbit | GSAP | Staggered scale(0.5→1) + opacity(0→1) on open, reverse on close. 0.08s stagger, 0.4s total. | Medium |
| Menu button bounce-in | GSAP | translateY(100px→0), 0.8s, elastic ease. Plays on load. | Low |
| Mobile nav slide-in | CSS transition | Panel translateX(100%→0), 0.3s ease. Links staggered opacity with transition-delay. | Low |
| Scroll indicator bounce | CSS animation | `@keyframes translateY(0→8px→0)`, 1.5s infinite ease-in-out. | Low |
| Watermark "S" entrance | GSAP ScrollTrigger | opacity 0→0.04 + scale 0.9→1, 1.2s. | Low |
| Button hover | CSS transition | Background color shift + scale(1.02) + shadow intensify, 0.25s. | Low |

---

## State & Logic Plan

### WebGL Shader Lifecycle (Technology Section)

The particle shader requires careful React-WebGL coordination:

- **Canvas ref** attached to a `<canvas>` element
- **WebGL context** initialized once on mount with `{ alpha: true, antialias: false }`
- **Program setup**: compile shaders, link program, cache attribute/uniform locations
- **RAF loop** managed via a ref-stored callback. Loop starts when section enters viewport (IntersectionObserver) and pauses when section leaves — critical for performance since shader is expensive.
- **Mouse position** passed as `u_mouse` vec2 uniform. Converted to device pixels. Reset to `(-1, -1)` when mouse leaves canvas bounds.
- **Resize handler** updates canvas dimensions (capped at `devicePixelRatio ≤ 2`) and `u_res` uniform.
- **Cleanup**: terminate RAF loop, delete WebGL resources on unmount.

### Scroll-Driven Feature Panels Pinning

FeaturesSection requires GSAP ScrollTrigger pinning orchestration:

- Three panels are stacked vertically in the DOM.
- Each panel gets a ScrollTrigger with `pin: true`, `scrub: true`, `start: "top top"`, `end: "+=100%"`.
- A **master ScrollTrigger** wraps all three with a single `onUpdate` callback that reports combined progress (0–1) to drive the progress bar height.
- Panel entrance animations are timeline-based and scrubbed. Exit animations play as the next panel overlaps.
- `invalidateOnRefresh: true` for responsive recalculation.
- On mobile (<768px): pinning disabled. Panels scroll normally. Progress bar hidden. Sidebar becomes horizontal tabs.

### Intro Animation State Machine

The 12-second intro is a single GSAP master timeline that must not be restarted on React re-renders:

- Timeline stored in a ref (not state).
- Plays once on mount. After completion, the section is "settled" — further scroll simply shows the static hero.
- Radar sweep SVG overlay gets `pointer-events: none` and is removed from DOM after timeline completes (to free clip-path resources).
- The hero radar continuous animations (sweep arm, blips) are CSS-based and start only after the intro timeline finishes (via timeline `onComplete` callback adding an animation class).

### Cursor State Machine

The custom cursor operates a 3-state system driven by `data-cursor` attributes on DOM elements:

| State | Trigger | Visual |
|-------|---------|--------|
| dot (default) | No matching attribute | 8px green circle |
| circle | `data-cursor="interactive"` (links, buttons) | 40px circle with border |
| ibeam | `data-cursor="text"` (text areas) | 2px × 24px vertical bar |

- A delegated `mouseover` listener on `document` checks `e.target.closest('[data-cursor]')` to determine state.
- Cursor position tracked via `mousemove` → stored in refs (not state, for 60fps performance).
- RAF loop applies lerp interpolation for smooth follow.
- Trail dots rendered as an array of previous positions with 0.04s delay steps.
- Entire system disabled when `matchMedia('(hover: none)')` matches (touch devices).

---

## Other Key Decisions

### Raw WebGL over Three.js/R3F

The Technology section shader is a single full-screen quad with a self-contained fragment shader. Three.js would add ~150KB for a use case that only needs: canvas → WebGL context → draw 2 triangles → update uniforms. Raw WebGL is the correct choice here — the shader is fully specified in the design and requires no scene graph, cameras, or 3D objects.

### SVG Ring Chart over D3/Chart Library

The Diagram section ring chart is a decorative static visualization (5 equal segments, labels, slow rotation). Implementing as inline SVG with GSAP DrawSVG for the segment reveal animation avoids pulling in a charting library for a single bespoke graphic. The continuous rotation is pure CSS.

### Video Strategy

Three feature panel videos + one mission video = 4 video elements. Use `<video muted loop playsinline preload="auto">` with `object-fit: cover`. Videos should use `.webm` (VP9) as primary with `.mp4` (H.264) fallback. No lazy loading needed — videos are above the fold in their respective sections. A loading state (simple opacity fade) wraps video elements using `imagesloaded` to detect when each video is ready to play.
