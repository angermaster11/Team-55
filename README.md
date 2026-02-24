# FixFlow AI — Landing Page

AI-powered GitHub code correction platform landing page.

## Tech Stack

- **React 18** + **TypeScript**
- **Tailwind CSS v3** with custom color palette
- **Framer Motion** for animations
- **Vite** for bundling

## Color Palette

| Token     | Hex       | Usage                        |
|-----------|-----------|------------------------------|
| `base`    | `#0A0E1A` | Deep navy black — bg         |
| `surface` | `#0F1629` | Midnight blue — section bg   |
| `card`    | `#141C35` | Indigo dark — cards          |
| `mint`    | `#00FFB2` | Electric mint — primary CTA  |
| `coral`   | `#FF6B35` | Burnt coral — warnings/FAQ   |
| `violet`  | `#7B61FF` | Soft violet — gradients      |
| `snow`    | `#E2E8F0` | Cool white — headings        |
| `muted`   | `#6B7280` | Body text                    |
| `slate`   | `#4A5568` | Placeholder / footer text    |
| `subtle`  | `#9CA3AF` | Nav links                    |

## Project Structure

```
src/
├── components/
│   ├── Navbar.tsx
│   ├── HeroSection.tsx
│   ├── TerminalPreview.tsx
│   ├── FeaturesSection.tsx
│   ├── HowItWorksSection.tsx
│   ├── LoginSection.tsx
│   ├── FAQSection.tsx
│   ├── CTASection.tsx
│   ├── Footer.tsx
│   └── GitHubIcon.tsx
├── data.ts          # All static content
├── types.ts         # TypeScript interfaces
├── App.tsx
├── main.tsx
└── index.css
```

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Build

```bash
npm run build
```
