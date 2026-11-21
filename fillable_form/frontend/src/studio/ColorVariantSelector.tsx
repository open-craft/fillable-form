import { Form, Icon } from '@openedx/paragon';
import { CheckCircle } from '@openedx/paragon/icons';
import {
  DEFAULT_SWATCH_TILES,
  swatchTiles,
  type ColorVariant,
  type SwatchTile,
} from '../common/variants';

interface ColorSwatchProps {
  value: string;
  label: string;
  tiles: SwatchTile[];
  selected: boolean;
}

function ColorSwatch({ value, label, tiles, selected }: ColorSwatchProps) {
  return (
    <Form.Radio
      value={value}
      className={`fillable-form-swatch${selected ? ' fillable-form-swatch--selected' : ''} d-block position-relative m-0 p-2 bg-white`}
      labelClassName="fillable-form-swatch-body d-flex flex-column align-items-stretch mb-0"
    >
      <span className="fillable-form-swatch-preview d-flex" aria-hidden="true">
        {tiles.map((tile, index) => (
          <span
            // eslint-disable-next-line react/no-array-index-key -- the two tiles never reorder
            key={index}
            className="fillable-form-swatch-tile d-flex flex-column flex-fill py-3 px-2 rounded-lg"
            style={{ background: tile.background, color: tile.color }}
          >
            <span className="font-weight-bold">Aa</span>
            <span className="fillable-form-swatch-rule" />
          </span>
        ))}
      </span>
      <span className="text-center font-weight-bold">{label}</span>
      {selected && (
        <Icon
          src={CheckCircle}
          className="fillable-form-swatch-check position-absolute rounded-circle bg-primary text-white"
          aria-hidden="true"
        />
      )}
    </Form.Radio>
  );
}

export interface ColorVariantSelectorProps {
  name: string;
  variants: ColorVariant[];
  value: string;
  onChange: (id: string) => void;
  ariaLabel: string;
  defaultLabel: string;
}

export function ColorVariantSelector({
  name,
  variants,
  value,
  onChange,
  ariaLabel,
  defaultLabel,
}: ColorVariantSelectorProps) {
  return (
    <Form.RadioSet
      name={name}
      value={value}
      aria-label={ariaLabel}
      className="fillable-form-swatch-grid d-flex flex-row flex-wrap align-items-stretch mt-3"
      onChange={(event: React.ChangeEvent<HTMLInputElement>) => onChange(event.target.value)}
    >
      <ColorSwatch
        value=""
        label={defaultLabel}
        tiles={DEFAULT_SWATCH_TILES}
        selected={value === ''}
      />
      {variants.map((variant) => (
        <ColorSwatch
          key={variant.id}
          value={variant.id}
          label={variant.label}
          tiles={swatchTiles(variant)}
          selected={value === variant.id}
        />
      ))}
    </Form.RadioSet>
  );
}
