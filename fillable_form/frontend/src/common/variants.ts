import type { CSSProperties } from 'react';

/**
 * Colour variants available to the fillable form block.
 *
 * The registry is the single source of truth: adding a variant means adding an
 * entry here, not changing components. Each token value should reference a theme
 * token with the design fallback, e.g. `var(--pgn-wgu-color-navy-base, #002855)`,
 * so the variant still renders when the theme CSS isn't loaded.
 */

export type ColorCategory =
  | 'primary'
  | 'secondary'
  | 'interactives'
  | 'feedback';

/** Block variables a variant can override (see fillable_form.css). */
export type ColorToken =
  | '--fillable-form-color-background'
  | '--fillable-form-color-heading'
  | '--fillable-form-color-text'
  | '--fillable-form-color-download-bg'
  | '--fillable-form-color-download-text';

export interface ColorVariant {
  /** Stored in the block's `color_variant` field. Never rename a shipped id. */
  id: string;
  category: ColorCategory;
  /** Human-readable name shown under the swatch. */
  label: string;
  /** Values applied inline on the learner wrapper (.fillable-form-learner). */
  tokens: Record<ColorToken, string>;
}

export const COLOR_VARIANTS: ColorVariant[] = [
  {
    id: 'secondary-light',
    category: 'secondary',
    label: 'Light',
    tokens: {
      '--fillable-form-color-background': '#ecf5f7',
      '--fillable-form-color-heading': '#327d8a',
      '--fillable-form-color-text': 'var(--pgn-wgu-color-navy-muted, #223e5d)',
      '--fillable-form-color-download-bg': 'var(--pgn-wgu-color-navy-muted, #223e5d)',
      '--fillable-form-color-download-text': 'var(--pgn-wgu-color-text-pure-white, #ffffff)',
    },
  },
  {
    id: 'primary-dark',
    category: 'primary',
    label: 'Dark',
    tokens: {
      '--fillable-form-color-background': 'var(--pgn-wgu-color-background-main-navy, #002855)',
      '--fillable-form-color-heading': 'var(--pgn-wgu-color-text-main-lake, #46b1ef)',
      '--fillable-form-color-text': 'var(--pgn-wgu-color-text-pure-white, #ffffff)',
      '--fillable-form-color-download-bg': 'var(--pgn-wgu-color-text-main-lake, #46b1ef)',
      '--fillable-form-color-download-text': 'var(--pgn-wgu-color-text-main-navy, #002855)',
    },
  },
];

export const findColorVariant = (
  id: string,
  variants: ColorVariant[] = COLOR_VARIANTS,
) => variants.find((variant) => variant.id === id);

export interface SwatchTile {
  background: string;
  color: string;
}

/**
 * Swatch tiles for the block's default colours (no variant). They mirror the
 * defaults declared on .fillable-form-learner in fillable_form.css, with white
 * standing in for the transparent background.
 */
export const DEFAULT_SWATCH_TILES: SwatchTile[] = [
  {
    background: 'var(--pgn-color-white, #ffffff)',
    color: 'var(--pgn-color-primary-base, #0075b4)',
  },
  {
    background: 'var(--pgn-color-primary-base, #0075b4)',
    color: 'var(--pgn-color-white, #ffffff)',
  },
];

/**
 * The two tiles shown in a Studio swatch: the block background with its heading
 * colour, and the download card with its text colour.
 */
export const swatchTiles = (variant: ColorVariant): SwatchTile[] => [
  {
    background: variant.tokens['--fillable-form-color-background'],
    color: variant.tokens['--fillable-form-color-heading'],
  },
  {
    background: variant.tokens['--fillable-form-color-download-bg'],
    color: variant.tokens['--fillable-form-color-download-text'],
  },
];

/**
 * Inline custom properties for a stored variant id.
 *
 * Returns `undefined` when the id is unset or no longer shipped, which leaves the
 * block's default colours. The stored id is kept, so it recovers if the variant returns.
 */
export const colorVariantStyle = (
  id: string,
  variants: ColorVariant[] = COLOR_VARIANTS,
): CSSProperties | undefined => {
  const variant = findColorVariant(id, variants);
  return variant ? (variant.tokens as CSSProperties) : undefined;
};
