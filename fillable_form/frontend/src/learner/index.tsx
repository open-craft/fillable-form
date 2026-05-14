import { createRoot, Root } from 'react-dom/client';
import { LearnerView } from './LearnerView';
import { LearnerConfig } from '../common/types';

let root: Root | null = null;

export function renderBlock(
  _runtime: unknown,
  element: HTMLElement,
  initData: LearnerConfig,
): Root {
  root = createRoot(element);
  root.render(<LearnerView initData={initData} />);
  return root;
}
