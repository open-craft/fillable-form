import { createRoot, Root } from 'react-dom/client';
import { LearnerView } from './LearnerView';
import { LearnerConfig } from '../common/types';

let root: Root | null = null;

export function renderBlock(
  _runtime: unknown,
  element: HTMLElement,
  initData: LearnerConfig,
): Root {
  // element may be a jQuery object from Studio's handleXBlockFragment
  const container =
    element && 'jquery' in element
      ? (element as unknown as HTMLElement[])[0]
      : element;
  root = createRoot(container as HTMLElement);
  root.render(<LearnerView initData={initData} />);
  return root;
}
