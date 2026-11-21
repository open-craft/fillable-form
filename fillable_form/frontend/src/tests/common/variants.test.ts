import {
  COLOR_VARIANTS,
  colorVariantStyle,
  findColorVariant,
  swatchTiles,
  type ColorVariant,
} from '../../common/variants';

const NAVY: ColorVariant = {
  id: 'primary-navy',
  category: 'primary',
  label: 'Navy',
  tokens: {
    '--fillable-form-color-background': 'var(--pgn-wgu-color-navy-base, #002855)',
    '--fillable-form-color-heading': 'var(--pgn-color-white, #ffffff)',
    '--fillable-form-color-text': 'var(--pgn-color-white, #ffffff)',
    '--fillable-form-color-download-bg': 'var(--pgn-wgu-color-navy-900, #001124)',
    '--fillable-form-color-download-text': 'var(--pgn-color-white, #ffffff)',
  },
};

describe('colour variant registry', () => {
  test('ships the configured variants', () => {
    expect(COLOR_VARIANTS.map((variant) => variant.id)).toEqual(['secondary-light', 'primary-dark']);
  });

  test('every shipped variant has a unique id', () => {
    const ids = COLOR_VARIANTS.map((variant) => variant.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test.each(['', 'not-shipped'])(
    'applies no overrides for an unset or unavailable id (%s)',
    (id) => {
      expect(findColorVariant(id, [NAVY])).toBeUndefined();
      expect(colorVariantStyle(id, [NAVY])).toBeUndefined();
    },
  );

  test('returns the variant tokens as inline custom properties', () => {
    expect(colorVariantStyle('primary-navy', [NAVY])).toEqual(NAVY.tokens);
  });

  test('builds the swatch tiles from the background and download card colours', () => {
    expect(swatchTiles(NAVY)).toEqual([
      {
        background: NAVY.tokens['--fillable-form-color-background'],
        color: NAVY.tokens['--fillable-form-color-heading'],
      },
      {
        background: NAVY.tokens['--fillable-form-color-download-bg'],
        color: NAVY.tokens['--fillable-form-color-download-text'],
      },
    ]);
  });
});
