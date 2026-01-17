# Design System

We employs a minimalist, data-first aesthetic that balances "Friendly" Brutalism with technical precision. Interfaces are monochromatic, using sharp corners, visible borders, and monospaced typography to evoke a research-oriented atmosphere.

## Core Principles

- **Minimalist**: Clean interfaces with hierarchy driven by space and typography.
- **Friendly Brutalism**: Sharp corners and visible borders softened by a warm palette.
- **Data-First**: Monospaced fonts for technical data, numbers, and labels.
- **Adaptive**: Seamless light and dark mode support using CSS variables.

## Color Palette

The system uses a unified set of CSS variables centered around Wood Beige borders and monochromatic surfaces.

### Light Mode
- Background: #efede5 (Creme)
- Surface: #ffffff
- Text: #1a1a1b (Friendly Gray)
- Border: #634936 (Wood Beige)

### Dark Mode
- Background: #1a1a1b
- Surface: #202021
- Text: #efede5
- Border: #634936

## Typography

### Inter
Used for headings and body copy. Regular (400) for prose and Bold (700) for titles.

### Space Mono
Used for numbers, labels, navigation items, and metadata. Primarily uppercase for a technical aesthetic.

## Components

### Navigation
Shared across all properties. Fixed header with backdrop blur and responsive behavior. Desktop menu uses numeric prefixes and horizontal spacing. Mobile menu employs a slide-down hamburger transition.

### Elements
- **Buttons**: Sharp corners, 1px borders, uppercase Space Mono labels.
- **Cards**: Surface background with subtle 1px Wood Beige borders.
- **Icons**: Line style icons with 2px stroke width.

## Implementation

Components must use CSS variables to ensure theme compatibility.

```css
.component {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-family: var(--font-mono);
}
```