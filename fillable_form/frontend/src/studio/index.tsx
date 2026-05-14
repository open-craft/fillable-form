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
  root = createRoot(element);
  root.render(<StudioView initData={initData} runtime={runtime} />);
  return root;
}
