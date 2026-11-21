// Copied from exemplar-blocks (frontend/src/shared/components/IconPicker).
import { useMemo, useState, type ElementType } from 'react';
import { Form, Sticky } from '@openedx/paragon';
import Fuse from 'fuse.js';
import { ICONS } from './icons';

const fuse = new Fuse(ICONS, { threshold: 0.3, minMatchCharLength: 2 });

export interface IconPickerProps {
  defaultIcons: string[];
  selectedIcon?: string;
  onSelect: (icon: string) => void;
  autoFocus?: boolean;
  itemAs?: ElementType;
}

/**
 * Search field and grid of Material Icons (outlined).
 *
 * Shows `defaultIcons` until the author types, then the icons matching the search.
 */
export default function IconPicker({
  defaultIcons,
  selectedIcon,
  onSelect,
  autoFocus = false,
  itemAs: Item = 'button',
}: IconPickerProps) {
  const [searchTerm, setSearchTerm] = useState('');

  const icons = useMemo(
    () =>
      searchTerm
        ? fuse.search(searchTerm).map((result) => result.item)
        : defaultIcons,
    [searchTerm, defaultIcons],
  );

  return (
    <div className="icon-picker">
      <Sticky>
        <Form.Group size="sm">
          <Form.Control
            autoFocus={autoFocus}
            type="text"
            className="m-0"
            placeholder="Search icons"
            aria-label="Search icons"
            trailingElement={
              <span className="material-icons-outlined medium text-gray-500">
                search
              </span>
            }
            value={searchTerm}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setSearchTerm(e.currentTarget.value)
            }
          />
        </Form.Group>
      </Sticky>
      <div className="icon-list d-flex flex-wrap justify-items-start">
        {icons.map((icon) => (
          <Item
            as={Item === 'button' ? undefined : 'button'}
            eventKey={Item === 'button' ? undefined : icon}
            type="button"
            key={icon}
            className={`icon-symbol p-2 ${icon === selectedIcon ? 'active' : ''}`}
            title={icon}
            aria-label={icon}
            aria-pressed={icon === selectedIcon}
            onClick={() => onSelect(icon)}
          >
            <span className="material-icons-outlined" aria-hidden="true">
              {icon}
            </span>
          </Item>
        ))}
      </div>
    </div>
  );
}
