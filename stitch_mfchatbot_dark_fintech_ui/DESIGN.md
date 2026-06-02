---
name: Luminous Ledger
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#bacac1'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#85948c'
  outline-variant: '#3c4a43'
  surface-tint: '#2fe0aa'
  primary: '#44edb7'
  on-primary: '#003828'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#006c4f'
  secondary: '#c5c6ca'
  on-secondary: '#2e3134'
  secondary-container: '#494c4f'
  on-secondary-container: '#babcc0'
  tertiary: '#f7d000'
  on-tertiary: '#3a3000'
  tertiary-container: '#d7b500'
  on-tertiary-container: '#564700'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#e1e2e6'
  secondary-fixed-dim: '#c5c6ca'
  on-secondary-fixed: '#191c1f'
  on-secondary-fixed-variant: '#44474a'
  tertiary-fixed: '#ffe16d'
  tertiary-fixed-dim: '#e9c400'
  on-tertiary-fixed: '#221b00'
  on-tertiary-fixed-variant: '#544600'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  xl: 64px
  container-max: 1200px
  gutter: 24px
---

## Brand & Style
The design system is engineered for a premium fintech experience that balances high-stakes reliability with cutting-edge technology. It targets a sophisticated audience that values precision, security, and a "dark mode first" aesthetic. 

The style is a fusion of **Minimalism** and **Glassmorphism**, characterized by high-contrast neon accents against deep, matte surfaces. The emotional response should be one of "controlled power"—calm, focused, and expensive. Visual depth is achieved through translucent layers, subtle light-leak borders, and soft glows that simulate high-end hardware interfaces.

## Colors
This design system utilizes a high-contrast dark palette to define hierarchy and focus. 

- **Primary (#00D09C):** A glowing neon teal used exclusively for calls to action, active states, and success indicators. It should feel like a light source.
- **Surface & Backgrounds:** The base is a matte charcoal (#121212). Deep navy slate (#1A1D20) is used for elevated containers to provide tonal depth.
- **Secondary Text (#8A95A5):** A muted silver gray used to reduce visual noise for labels and metadata.
- **Warning (#FFD700):** A gold/amber used for alerts, high-value transactions, or warnings, paired with low-opacity dark backdrops to maintain the premium feel.

## Typography
The typography strategy pairs the geometric, modern personality of **Outfit** for headlines with the utilitarian precision of **Inter** for data and body text. 

Headlines use tight letter-spacing to appear more impactful and "architectural." Labels and small data points utilize uppercase styling with increased letter-spacing to ensure legibility on dark backgrounds and to evoke a technical, financial dashboard feel.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy for desktop to maintain a premium, composed feel, while transitioning to a fluid model for mobile.

- **Desktop:** 12-column grid with 24px gutters. Content is centered with a max-width of 1200px.
- **Mobile:** 4-column fluid grid with 16px side margins. 
- **Spacing Rhythm:** Based on an 8px linear scale. Large vertical gaps (64px+) are encouraged between major sections to emphasize the "Minimalist" brand value and provide breathing room for complex financial data.

## Elevation & Depth
Depth is created through **Glassmorphism** and **Tonal Layering** rather than traditional heavy shadows.

1.  **Level 0 (Base):** #121212 - The matte foundation.
2.  **Level 1 (Cards/Panels):** #1A1D20 with a 1px solid border at 8% white opacity.
3.  **Level 2 (Modals/Overlays):** Translucent navy slate with a 20px backdrop blur and a soft "glow" shadow (0px 8px 32px rgba(0,0,0,0.4)).
4.  **Level 3 (Active/Interactive):** Primary teal elements may have a subtle 0 0 12px neon outer glow (rgba(0, 208, 156, 0.3)) to signify focus or "on" states.

## Shapes
The shape language is "Soft-Modern." All containers and buttons use a base 0.5rem (8px) corner radius. This provides a approachable feel without the playfulness of fully rounded pill shapes. 

Interactive elements like input fields and primary buttons maintain this 8px radius to ensure a consistent, structural appearance across the dashboard.

## Components
- **Buttons:** Primary buttons are solid Teal (#00D09C) with black text. Secondary buttons are "Ghost" style: transparent background with a 1px teal border.
- **Input Fields:** Semi-transparent dark backgrounds with a subtle top-light border. On focus, the border turns solid Teal with a faint inner glow.
- **Cards:** Use the "Level 1" elevation. For featured fintech products, cards may include a subtle gradient linear-border (from white at 10% to white at 2%).
- **Chips/Badges:** Small, high-contrast pills. For "Live" data or "Positive" trends, use a Teal background at 10% opacity with solid Teal text.
- **Lists:** Clean rows separated by 1px dividers (rgba(255,255,255,0.05)). Hover states should trigger a slight brightening of the background color to #1F2326.
- **Charts/Graphs:** Use Primary Teal for the main data line. Use a gradient fill below the line that fades from Teal (20% opacity) to transparent.