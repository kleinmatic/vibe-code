---
theme:
  mode: dark
  colors:
    background: "#08070a"      # Obsidian void with deep purple-black tone
    surface: "rgba(16, 14, 20, 0.7)" # Translucent spiky surface layer
    surfaceSolid: "#100e14"
    primary: "#ff5722"         # Vibrant, aggressive neon milkbar orange
    primaryHover: "#ff7043"
    primaryGlow: "rgba(255, 87, 34, 0.4)"
    secondary: "#00bcd4"       # Electric cyber cyan (phonetic keys)
    secondaryHover: "#26c6da"
    secondaryGlow: "rgba(0, 188, 212, 0.25)"
    text: "#f6f4f8"            # High-contrast bone/ash white
    textMuted: "#8a8594"       # Muted, decaying lavender-grey
    border: "rgba(255, 255, 255, 0.07)" # Fine glass line
    borderActive: "rgba(255, 87, 34, 0.6)"
  effects:
    radiusOuter: "24px 4px 24px 4px" # Asymmetric, organic spiky leaf/thorn shape
    radiusInner: "16px 2px 16px 2px"
    blur: "16px"
    shadow: "0 16px 40px rgba(0, 0, 0, 0.7)"
    shadowActive: "0 0 25px rgba(255, 87, 34, 0.3)"
  typography:
    fontDisplay: "'Outfit', sans-serif"    # High-impact geometric display font with a premium finish
    fontSans: "'Inter', sans-serif"        # Ultra-clean, readable sans-serif for body and definitions
    fontMono: "'Fira Code', 'Courier New', monospace"
---

# Nadsat Dictionary Design System

A high-fidelity retro-futuristic dark mode inspired by the Korova Milkbar's neon-accented obsidian surfaces and Alex DeLarge’s iconic bowler hat & single fake eyelash makeup.

## Atmosphere & Mood

- **Density**: High drama and spacious.
- **Asymmetric Spiky Forms**: Emulates organic, thorny leaf shapes by using sharp asymmetric corner-radius mapping (`24px 4px 24px 4px`).
- **Cyberpunk Contrast**: Blends cold ash-white letterforms with neon orange flames and cyber cyan indicators.
- **Iconic Branding**: Embeds a signature graphic symbol featuring the bowler hat and Alex's single spiky eyelash makeup.

## Typography System

1. **Heading Display**:
   - Font: `Outfit`.
   - Characteristics: Clean, modern, geometric sans-serif that projects a refined, premium tech aesthetic.
   - Usage: App Title, widget titles, and the Nadsat words themselves.
2. **Body Sans**:
   - Font: `Inter`.
   - Characteristics: Highly readable, neutral sans-serif built specifically for screen text.
   - Usage: English definitions, etymology texts, and explanatory notes.

## Component Tuning

### 1. Dictionary Cards
- **Asymmetry**: Shaped as `24px 4px 24px 4px` (`border-radius`) to feel like organic shields or thorns.
- **Hover**: Scale factor `1.02x` with an intense neon border and a glowing backdrop shadow. A solid primary-colored left border active line rises to frame the card's sharp corner.

### 2. Search Box
- Border radius matches the card system (`12px 2px 12px 2px`) to remain cohesive with the spiky design language.
