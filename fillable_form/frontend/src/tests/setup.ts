import '@testing-library/jest-dom';

Object.defineProperty(global, 'fetch', {
  configurable: true,
  value: jest.fn(),
});

beforeEach(() => {
  (global.fetch as jest.Mock).mockReset();
});

jest.mock('@openedx/paragon', () => ({
  Icon: () => null,
  Sticky: ({ children }: any) => children,
  Stack: ({ children, direction, gap, reversed, ...props }: any) => {
    const React = require('react');
    return React.createElement('div', props, children);
  },
  Alert: ({ children, icon, actions, ...props }: any) => {
    const React = require('react');
    return React.createElement('div', { role: 'alert', ...props }, children, actions);
  },
  Button: ({ children, iconBefore, iconAfter, ...props }: any) => {
    const React = require('react');
    return React.createElement('button', { type: 'button', ...props }, children);
  },
  StatefulButton: ({ labels, onClick, state, ...props }: any) => {
    const React = require('react');
    return React.createElement(
      'button',
      { type: 'button', onClick, ...props },
      state === 'pending' ? labels.pending : labels.default,
    );
  },
  Form: (() => {
    const React = require('react');
    // RadioSet shares name/value/onChange with its Radio children, as in Paragon.
    const RadioSetContext = React.createContext({});
    const Control = ({ children, trailingElement, ...props }: any) =>
      React.createElement('input', props, children);
    Control.Feedback = ({ children }: any) =>
      React.createElement('div', {}, children);

    return {
      Group: ({ children }: any) => React.createElement('div', {}, children),
      Label: ({ children, ...props }: any) => React.createElement('label', props, children),
      Control,
      RadioSet: ({ children, name, value, onChange, ...props }: any) =>
        React.createElement(
          RadioSetContext.Provider,
          { value: { name, value, onChange } },
          React.createElement('div', { role: 'radiogroup', ...props }, children),
        ),
      Radio: ({ children, value, labelClassName, ...props }: any) => {
        const set = React.useContext(RadioSetContext);
        return React.createElement(
          'label',
          props,
          React.createElement('input', {
            type: 'radio',
            name: set.name,
            value,
            checked: set.value === value,
            onChange: set.onChange,
          }),
          children,
        );
      },
      Checkbox: ({ children, ...props }: any) =>
        React.createElement(
          'label',
          {},
          React.createElement('input', { type: 'checkbox', ...props }),
          children,
        ),
    };
  })(),
}));

// Mock Paragon icons (avoid loading actual SVG)
jest.mock('@openedx/paragon/icons', () => ({
  CheckCircle: () => null,
  Close: () => null,
  Download: () => null,
  InfoOutline: () => null,
}));

// Mock crypto.randomUUID for potential use
Object.defineProperty(global, 'crypto', {
  value: { randomUUID: () => 'test-uuid' },
});
