import { IntlProvider } from 'react-intl';
import { createRoot, Root } from 'react-dom/client';
import { StudioView } from './StudioView';
import { StudioConfig } from '../common/types';

interface StudioRuntime {
  notify?: (action: string, data?: Record<string, unknown>) => void;
}

let root: Root | null = null;

export function renderBlock(
  runtime: StudioRuntime,
  element: HTMLElement,
  initData: StudioConfig,
): Root {
  // element may be a jQuery object from Studio's handleXBlockFragment
  const container =
    element && 'jquery' in element
      ? (element as unknown as HTMLElement[])[0]
      : element;

  const modalBody = (container as HTMLElement).parentElement?.parentElement;
  if (modalBody instanceof HTMLElement) {
    modalBody.style.minHeight = '635px';
  }

  root = createRoot(container as HTMLElement);
  root.render(
    <IntlProvider locale={initData.locale} messages={{}}>
      <StudioView initData={initData} runtime={runtime} />
    </IntlProvider>
  );
  return root;
}
