import '@testing-library/jest-dom';

Object.defineProperty(global, 'fetch', {
  configurable: true,
  value: jest.fn(),
});

beforeEach(() => {
  (global.fetch as jest.Mock).mockReset();
});

jest.mock('@openedx/paragon', () => ({
  Button: ({ children, ...props }: any) => {
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
    const Control = ({ children, ...props }: any) =>
      React.createElement('input', props, children);
    Control.Feedback = ({ children }: any) =>
      React.createElement('div', {}, children);

    return {
      Group: ({ children }: any) => React.createElement('div', {}, children),
      Label: ({ children, ...props }: any) => React.createElement('label', props, children),
      Control,
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
  Close: () => null,
  Download: () => null,
}));

// Mock crypto.randomUUID for potential use
Object.defineProperty(global, 'crypto', {
  value: { randomUUID: () => 'test-uuid' },
});
