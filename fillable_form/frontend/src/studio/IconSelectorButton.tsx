import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react';
import { Button } from '@openedx/paragon';
import IconPicker from './IconPicker';

// Icons shown before searching: the default pencil, followed by other icons
// that suit a writing or reflection exercise.
const DEFAULT_ICONS = [
  'edit',
  'edit_note',
  'draw',
  'create',
  'border_color',
  'description',
  'article',
  'assignment',
  'note_alt',
  'sticky_note_2',
  'menu_book',
  'auto_stories',
  'lightbulb',
  'psychology',
  'question_answer',
  'chat',
  'forum',
  'self_improvement',
  'favorite',
  'flag',
];

export interface IconSelectorButtonProps {
  id: string;
  icon: string;
  onChange: (icon: string) => void;
  buttonLabel: string;
}

/**
 * Button showing the current icon that opens a popover with the IconPicker.
 */
export const IconSelectorButton = ({ id, icon, onChange, buttonLabel }: IconSelectorButtonProps) => {
  const popoverId = useId();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const closeTimeout = useRef<number>();

  const close = () => setIsOpen(false);

  // Focus moving outside the component (click elsewhere or Tab) closes the
  // popover. The close waits for the next focus event: if the focus lands in
  // the component again, it's cancelled.
  const handleBlur = () => {
    closeTimeout.current = window.setTimeout(close, 0);
  };

  const handleFocus = () => {
    window.clearTimeout(closeTimeout.current);
  };

  useEffect(() => () => window.clearTimeout(closeTimeout.current), []);

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Escape' && isOpen) {
      e.preventDefault();
      close();
      buttonRef.current?.focus();
    }
  };

  return (
    <div
      className="fillable-form-icon-selector-button"
      onBlur={handleBlur}
      onFocus={handleFocus}
      onKeyDown={handleKeyDown}
    >
      <Button
        id={id}
        ref={buttonRef}
        variant="outline-primary"
        aria-expanded={isOpen}
        aria-controls={popoverId}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="material-icons-outlined" aria-hidden="true">{icon}</span>
        <span className="ml-2">{buttonLabel}</span>
      </Button>
      {isOpen && (
        <div
          id={popoverId}
          className="fillable-form-icon-selector-button-popover"
          role="dialog"
          aria-label={buttonLabel}
          tabIndex={-1}
        >
          <IconPicker
            autoFocus
            defaultIcons={DEFAULT_ICONS}
            selectedIcon={icon}
            onSelect={(selected) => {
              onChange(selected);
              close();
              buttonRef.current?.focus();
            }}
          />
        </div>
      )}
    </div>
  );
};
