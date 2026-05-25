import { render, screen, fireEvent, act } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { StudioView } from '../../studio/StudioView';
import type { StudioConfig } from '../../common/types';

// Mock the API module
jest.mock('../../common/api', () => ({
  postJson: jest.fn(),
}));

// Mock the TinyMCE editor to avoid loading actual TinyMCE in tests
jest.mock('../../studio/TinyMceEditor', () => ({
  TinyMceEditor: ({
    value,
    onChange,
    ariaLabel,
  }: {
    value: string;
    onChange: (v: string) => void;
    ariaLabel?: string;
  }) => (
    <textarea
      aria-label={ariaLabel || 'Instructions'}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

// Mock react-select/creatable
jest.mock('react-select/creatable', () => {
  return function MockCreatable({ onChange, options, inputId, placeholder }: any) {
    return (
      <select
        data-testid="creatable-select"
        id={inputId}
        onChange={(e) => {
          const val = e.target.value;
          onChange(val ? { value: val, label: val } : null);
        }}
      >
        <option value="">{placeholder}</option>
        {options.map((opt: any) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    );
  };
});

const { postJson } = require('../../common/api');

function renderWithIntl(ui: React.ReactElement, locale = 'en') {
  return render(<IntlProvider locale={locale} messages={{}}>{ui}</IntlProvider>);
}

function createConfig(overrides: Partial<StudioConfig> = {}): StudioConfig {
  return {
    block_id: 'test-block-id',
    display_name: 'My Form Field',
    instructions: '<p>Instructions here</p>',
    form_group_id: 'group-alpha',
    form_group_options: ['group-alpha', 'group-beta'],
    field_label: 'Section Title',
    show_download_button: true,
    pdf_order: 10,
    handler_urls: {
      studio_submit: '/handler/studio_submit',
    },
    locale: 'en',
    ...overrides,
  };
}

function createRuntime() {
  return {
    notify: jest.fn(),
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('StudioView', () => {
  test('renders all form fields', () => {
    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);

    expect(screen.getByLabelText('Display Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Answer Field Label')).toBeInTheDocument();
    expect(screen.getByLabelText('Form Group ID')).toBeInTheDocument();
    expect(screen.getByLabelText('PDF Order')).toBeInTheDocument();
    expect(screen.getByLabelText('Introduction')).toBeInTheDocument();
    expect(screen.getByText('Show PDF download button on this field')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  test('pre-fills fields from init data', () => {
    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);

    expect(screen.getByLabelText('Display Name')).toHaveValue('My Form Field');
    expect(screen.getByLabelText('Answer Field Label')).toHaveValue('Section Title');
    expect(screen.getByLabelText('PDF Order')).toHaveValue(10);
    expect(screen.getByLabelText('Introduction')).toHaveValue('<p>Instructions here</p>');
  });

  test('calls studio_submit on save', async () => {
    (postJson as jest.Mock).mockResolvedValueOnce({ success: true });

    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);

    fireEvent.click(screen.getByText('Save'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(postJson).toHaveBeenCalledWith(
      '/handler/studio_submit',
      {
        display_name: 'My Form Field',
        instructions: '<p>Instructions here</p>',
        form_group_id: 'group-alpha',
        field_label: 'Section Title',
        show_download_button: true,
        pdf_order: 10,
      },
    );
  });

  test('does not submit invalid PDF order from init data', async () => {
    const runtime = createRuntime();

    renderWithIntl(<StudioView initData={createConfig({ pdf_order: -1 })} runtime={runtime} />);

    fireEvent.click(screen.getByText('Save'));

    expect(postJson).not.toHaveBeenCalled();
    expect(runtime.notify).toHaveBeenCalledWith('error', {
      title: 'Save Error',
      message: 'PDF Order must be a non-negative whole number.',
    });
  });

  test('submits changed PDF order', async () => {
    (postJson as jest.Mock).mockResolvedValueOnce({ success: true });

    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);

    fireEvent.change(screen.getByLabelText('PDF Order'), { target: { value: '20' } });
    fireEvent.click(screen.getByText('Save'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(postJson).toHaveBeenCalledWith(
      '/handler/studio_submit',
      expect.objectContaining({ pdf_order: 20 }),
    );
  });

  test('does not submit blank PDF order', async () => {
    const runtime = createRuntime();

    renderWithIntl(<StudioView initData={createConfig()} runtime={runtime} />);

    fireEvent.change(screen.getByLabelText('PDF Order'), { target: { value: '' } });
    fireEvent.click(screen.getByText('Save'));

    expect(postJson).not.toHaveBeenCalled();
    expect(runtime.notify).toHaveBeenCalledWith('error', {
      title: 'Save Error',
      message: 'PDF Order must be a non-negative whole number.',
    });
  });

  test('notifies runtime on save start', async () => {
    (postJson as jest.Mock).mockResolvedValueOnce({ success: true });
    const runtime = createRuntime();

    renderWithIntl(<StudioView initData={createConfig()} runtime={runtime} />);

    fireEvent.click(screen.getByText('Save'));

    expect(runtime.notify).toHaveBeenCalledWith('save', { state: 'start' });
  });

  test('ignores duplicate save clicks while saving', async () => {
    let resolve: (value: unknown) => void;
    const promise = new Promise((r) => { resolve = r; });
    (postJson as jest.Mock).mockReturnValueOnce(promise);

    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);

    fireEvent.click(screen.getByText('Save'));
    fireEvent.click(screen.getByText('Saving...'));

    expect(postJson).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolve({ success: true });
    });
  });

  test('notifies runtime on save success', async () => {
    (postJson as jest.Mock).mockResolvedValueOnce({ success: true });
    const runtime = createRuntime();

    renderWithIntl(<StudioView initData={createConfig()} runtime={runtime} />);

    fireEvent.click(screen.getByText('Save'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(runtime.notify).toHaveBeenCalledWith('save', { state: 'end' });
  });

  test('notifies runtime on save error', async () => {
    (postJson as jest.Mock).mockResolvedValueOnce({
      success: false,
      error: 'Something went wrong',
    });
    const runtime = createRuntime();

    renderWithIntl(<StudioView initData={createConfig()} runtime={runtime} />);

    fireEvent.click(screen.getByText('Save'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(runtime.notify).toHaveBeenCalledWith('error', {
      title: 'Save Error',
      message: 'Something went wrong',
    });
  });

  test('notifies runtime on network error', async () => {
    (postJson as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
    const runtime = createRuntime();

    renderWithIntl(<StudioView initData={createConfig()} runtime={runtime} />);

    fireEvent.click(screen.getByText('Save'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(runtime.notify).toHaveBeenCalledWith('error', {
      title: 'Save Error',
      message: 'Network error while saving.',
    });
  });

  test('notifies runtime on cancel', () => {
    const runtime = createRuntime();

    renderWithIntl(<StudioView initData={createConfig()} runtime={runtime} />);

    fireEvent.click(screen.getByText('Cancel'));

    expect(runtime.notify).toHaveBeenCalledWith('cancel', {});
  });

  test('shows error message on failure', async () => {
    (postJson as jest.Mock).mockResolvedValueOnce({
      success: false,
      error: 'Save failed.',
    });

    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);

    fireEvent.click(screen.getByText('Save'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByText('Save failed.')).toBeInTheDocument();
  });

  test('shows help text for form group ID', () => {
    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);
    expect(screen.getByText(
      'Select a Group ID to connect fields across units for a PDF version. Create a new Group ID by typing the title and selecting "create" from the bottom of the list.',
    )).toBeInTheDocument();
  });

  test('shows help text for field label', () => {
    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);
    expect(screen.getByText(
      'Provide a name for the field learners use to answer the question',
    )).toBeInTheDocument();
  });

  test('toggles download button checkbox', () => {
    renderWithIntl(<StudioView initData={createConfig({ show_download_button: false })} runtime={createRuntime()} />);

    const checkbox = screen.getByLabelText('Show PDF download button on this field');
    expect(checkbox).not.toBeChecked();

    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();

    fireEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  test('displays runtime error message on API error', async () => {
    (postJson as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    renderWithIntl(<StudioView initData={createConfig()} runtime={createRuntime()} />);

    fireEvent.click(screen.getByText('Save'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByText('Network error while saving.')).toBeInTheDocument();
  });
});
