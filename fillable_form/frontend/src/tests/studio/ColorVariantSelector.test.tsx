import { render, screen, fireEvent } from '@testing-library/react';
import { ColorVariantSelector } from '../../studio/ColorVariantSelector';
import type { ColorVariant } from '../../common/variants';

const tokens = {
  '--fillable-form-color-background': '#ecf5f7',
  '--fillable-form-color-heading': '#2f808e',
  '--fillable-form-color-text': '#002855',
  '--fillable-form-color-download-bg': '#223e5d',
  '--fillable-form-color-download-text': '#ffffff',
};

const VARIANTS: ColorVariant[] = [
  { id: 'light-lake', category: 'secondary', label: 'Light Lake', tokens },
  { id: 'primary-navy', category: 'primary', label: 'Navy', tokens },
];

describe('ColorVariantSelector', () => {
  test('renders a default swatch followed by one swatch per variant', () => {
    render(
      <ColorVariantSelector
        name="color-variant"
        variants={VARIANTS}
        value=""
        onChange={jest.fn()}
        ariaLabel="Color variant"
        defaultLabel="Default"
      />,
    );

    expect(screen.getByRole('radiogroup', { name: 'Color variant' })).toBeInTheDocument();
    expect(screen.getAllByRole('radio').map((radio) => radio.getAttribute('value'))).toEqual([
      '',
      'light-lake',
      'primary-navy',
    ]);
    expect(screen.getByRole('radio', { name: 'Default' })).toBeChecked();
    expect(screen.getByRole('radio', { name: 'Light Lake' })).not.toBeChecked();
  });

  test('marks the stored variant as selected', () => {
    render(
      <ColorVariantSelector
        name="color-variant"
        variants={VARIANTS}
        value="primary-navy"
        onChange={jest.fn()}
        ariaLabel="Color variant"
        defaultLabel="Default"
      />,
    );

    expect(screen.getByRole('radio', { name: 'Navy' })).toBeChecked();
    expect(screen.getByRole('radio', { name: 'Navy' }).closest('label')).toHaveClass('fillable-form-swatch--selected');
  });

  test('reports the chosen variant id', () => {
    const onChange = jest.fn();
    render(
      <ColorVariantSelector
        name="color-variant"
        variants={VARIANTS}
        value=""
        onChange={onChange}
        ariaLabel="Color variant"
        defaultLabel="Default"
      />,
    );

    fireEvent.click(screen.getByRole('radio', { name: 'Light Lake' }));
    expect(onChange).toHaveBeenCalledWith('light-lake');
  });

  test('the default swatch clears the variant', () => {
    const onChange = jest.fn();
    render(
      <ColorVariantSelector
        name="color-variant"
        variants={VARIANTS}
        value="primary-navy"
        onChange={onChange}
        ariaLabel="Color variant"
        defaultLabel="Default"
      />,
    );

    fireEvent.click(screen.getByRole('radio', { name: 'Default' }));
    expect(onChange).toHaveBeenCalledWith('');
  });
});
