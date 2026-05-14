import { render, screen, fireEvent, act } from '@testing-library/react';
import { LearnerView } from '../../learner/LearnerView';
import type { LearnerConfig } from '../../common/types';

// Mock the API module
jest.mock('../../common/api', () => ({
  postJson: jest.fn(),
}));

const { postJson } = require('../../common/api');

function createConfig(overrides: Partial<LearnerConfig> = {}): LearnerConfig {
  return {
    block_id: 'test-block-id',
    field_label: 'Test Question',
    instructions: '<p>Please answer carefully.</p>',
    current_text: '',
    show_download_button: true,
    handler_urls: {
      save_response: '/handler/save_response',
      download_pdf: '/handler/download_pdf',
    },
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('LearnerView', () => {
  test('renders field label', () => {
    render(<LearnerView initData={createConfig()} />);
    expect(screen.getByText('Test Question')).toBeInTheDocument();
  });

  test('renders instructions as HTML', () => {
    render(<LearnerView initData={createConfig()} />);
    const instructions = screen.getByText('Please answer carefully.');
    expect(instructions).toBeInTheDocument();
    expect(instructions.tagName).toBe('P');
  });

  test('renders textarea with current text', () => {
    const config = createConfig({ current_text: 'Existing text' });
    render(<LearnerView initData={config} />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveValue('Existing text');
  });

  test('renders download button when enabled', () => {
    render(<LearnerView initData={createConfig({ show_download_button: true })} />);
    const button = screen.getByText('Download Form');
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('href', '/handler/download_pdf');
  });

  test('does not render download button when disabled', () => {
    render(<LearnerView initData={createConfig({ show_download_button: false })} />);
    expect(screen.queryByText('Download Form')).not.toBeInTheDocument();
  });

  test('auto-saves after debounce delay', async () => {
    (postJson as jest.Mock).mockResolvedValueOnce({
      success: true,
      modified: '2026-05-13T10:00:00',
    });

    render(<LearnerView initData={createConfig()} />);
    const textarea = screen.getByRole('textbox');

    fireEvent.change(textarea, { target: { value: 'New text' } });

    // Before timer fires, save should not have been called
    expect(postJson).not.toHaveBeenCalled();

    // Advance timer by 1.5s
    act(() => {
      jest.advanceTimersByTime(1500);
    });

    expect(postJson).toHaveBeenCalledTimes(1);
    expect(postJson).toHaveBeenCalledWith(
      '/handler/save_response',
      { response_text: 'New text' },
    );
  });

  test('cancels pending auto-save on new keystroke', () => {
    render(<LearnerView initData={createConfig()} />);
    const textarea = screen.getByRole('textbox');

    fireEvent.change(textarea, { target: { value: 'A' } });
    act(() => { jest.advanceTimersByTime(500); });

    fireEvent.change(textarea, { target: { value: 'AB' } });
    act(() => { jest.advanceTimersByTime(500); });

    fireEvent.change(textarea, { target: { value: 'ABC' } });

    // Only 500ms elapsed since last keystroke — should not have saved yet
    expect(postJson).not.toHaveBeenCalled();

    // Advance to 1.5s after last keystroke
    act(() => { jest.advanceTimersByTime(1500); });

    expect(postJson).toHaveBeenCalledTimes(1);
    expect(postJson).toHaveBeenCalledWith(
      '/handler/save_response',
      { response_text: 'ABC' },
    );
  });

  test('saves on blur immediately', () => {
    (postJson as jest.Mock).mockResolvedValueOnce({
      success: true,
      modified: '2026-05-13T10:00:00',
    });

    render(<LearnerView initData={createConfig()} />);
    const textarea = screen.getByRole('textbox');

    fireEvent.change(textarea, { target: { value: 'Blur text' } });
    fireEvent.blur(textarea);

    // Should save immediately, not wait for debounce
    expect(postJson).toHaveBeenCalledTimes(1);
    expect(postJson).toHaveBeenCalledWith(
      '/handler/save_response',
      { response_text: 'Blur text' },
    );
  });

  test('shows saving indicator', async () => {
    // Create a promise we control so "saving" state is visible
    let resolve: (value: unknown) => void;
    const promise = new Promise((r) => { resolve = r; });
    (postJson as jest.Mock).mockReturnValueOnce(promise);

    render(<LearnerView initData={createConfig()} />);
    const textarea = screen.getByRole('textbox');

    fireEvent.change(textarea, { target: { value: 'New' } });
    act(() => { jest.advanceTimersByTime(1500); });

    expect(screen.getByText('Saving...')).toBeInTheDocument();

    // Resolve the save
    await act(async () => {
      resolve({ success: true, modified: '2026-05-13T10:00:00' });
    });
  });

  test('shows saved indicator', async () => {
    (postJson as jest.Mock).mockResolvedValueOnce({
      success: true,
      modified: '2026-05-13T10:00:00',
    });

    render(<LearnerView initData={createConfig()} />);
    const textarea = screen.getByRole('textbox');

    fireEvent.change(textarea, { target: { value: 'New' } });
    await act(async () => {
      jest.advanceTimersByTime(1500);
      // Wait for microtasks
      await Promise.resolve();
    });

    // Should show "Saved" (the timestamp part will vary)
    expect(screen.getByText(/Saved/)).toBeInTheDocument();
  });

  test('shows error indicator', async () => {
    (postJson as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<LearnerView initData={createConfig()} />);
    const textarea = screen.getByRole('textbox');

    fireEvent.change(textarea, { target: { value: 'New' } });
    await act(async () => {
      jest.advanceTimersByTime(1500);
      await Promise.resolve();
    });

    expect(screen.getByText(/Save failed/)).toBeInTheDocument();
  });

  test('does not save unchanged text', () => {
    const config = createConfig({ current_text: 'Original' });
    render(<LearnerView initData={config} />);
    const textarea = screen.getByRole('textbox');

    // Type and then delete back to original
    fireEvent.change(textarea, { target: { value: 'OriginalX' } });
    fireEvent.change(textarea, { target: { value: 'Original' } });

    act(() => { jest.advanceTimersByTime(1500); });

    // No save should have been triggered
    expect(postJson).not.toHaveBeenCalled();
  });

  test('empty label does not render heading', () => {
    render(<LearnerView initData={createConfig({ field_label: '' })} />);
    const headings = screen.queryAllByRole('heading');
    expect(headings).toHaveLength(0);
  });

  test('empty instructions does not render instructions div', () => {
    const { container } = render(
      <LearnerView initData={createConfig({ instructions: '' })} />,
    );
    expect(container.querySelector('.fillable-form-instructions')).not.toBeInTheDocument();
  });

  test('textarea has aria-label', () => {
    render(<LearnerView initData={createConfig({ field_label: 'My Label' })} />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('aria-label', 'My Label');
  });

  test('download link opens in new tab', () => {
    render(<LearnerView initData={createConfig({ show_download_button: true })} />);
    const link = screen.getByText('Download Form');
    expect(link).toHaveAttribute('target', '_blank');
  });
});
