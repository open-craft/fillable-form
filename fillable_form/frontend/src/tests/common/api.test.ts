import { postJson } from '../../common/api';

describe('postJson', () => {
  beforeEach(() => {
    // Set a CSRF token cookie
    Object.defineProperty(document, 'cookie', {
      value: 'csrftoken=test-csrf-token-123; other=value',
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('sends CSRF token', async () => {
    const mockFetch = jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    } as Response);

    await postJson('/test-url', { key: 'value' });

    const call = mockFetch.mock.calls[0];
    const headers = call[1]?.headers as Record<string, string>;
    expect(headers['X-CSRFToken']).toBe('test-csrf-token-123');
  });

  test('sends JSON body', async () => {
    const mockFetch = jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    } as Response);

    await postJson('/test-url', { response_text: 'hello' });

    const call = mockFetch.mock.calls[0];
    expect(call[1]?.body).toBe(JSON.stringify({ response_text: 'hello' }));
  });

  test('sends Content-Type application/json', async () => {
    const mockFetch = jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    } as Response);

    await postJson('/test-url', {});

    const call = mockFetch.mock.calls[0];
    const headers = call[1]?.headers as Record<string, string>;
    expect(headers['Content-Type']).toBe('application/json');
  });

  test('throws on non-2xx response', async () => {
    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    } as Response);

    await expect(postJson('/test-url', {})).rejects.toThrow('HTTP 500');
  });

  test('throws on 404 response', async () => {
    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    } as Response);

    await expect(postJson('/test-url', {})).rejects.toThrow('HTTP 404');
  });

  test('returns parsed JSON on success', async () => {
    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true, modified: '2026-05-13T10:00:00' }),
    } as Response);

    const result = await postJson('/test-url', {});
    expect(result).toEqual({ success: true, modified: '2026-05-13T10:00:00' });
  });

  test('handles missing CSRF cookie gracefully', async () => {
    Object.defineProperty(document, 'cookie', {
      value: '',
      writable: true,
      configurable: true,
    });

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    } as Response);

    await postJson('/test-url', {});

    const call = (global.fetch as jest.Mock).mock.calls[0];
    const headers = call[1]?.headers as Record<string, string>;
    expect(headers['X-CSRFToken']).toBe('');
  });
});
