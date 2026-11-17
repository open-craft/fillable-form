import { IntlProvider } from 'react-intl';
import {
  createXBlockRoot,
  getRoot,
  type XBlockRuntime,
} from '@opencraft/xblock-react-utils';
import { StudioView } from './StudioView';
import { ShadowEmotionProvider } from './ShadowEmotionProvider';
import { StudioConfig } from '../common/types';
import styles from '../fillable_form.css';

export function renderBlock(
  runtime: XBlockRuntime,
  element: HTMLElement,
  initData: StudioConfig,
): Promise<void> {
  // element may be a jQuery object from Studio's handleXBlockFragment
  const container = getRoot(element);

  const modalBody = container.parentElement?.parentElement;
  if (modalBody instanceof HTMLElement) {
    modalBody.style.minHeight = '635px';
  }

  // createXBlockRoot mounts the app inside a shadow DOM and injects our CSS
  // plus Paragon's core and theme stylesheets, as in the learner view.
  return createXBlockRoot({ runtime, element: container, config: initData.config, styles })(
    <IntlProvider locale={initData.locale} messages={{}}>
      <ShadowEmotionProvider>
        <StudioView initData={initData} runtime={runtime} />
      </ShadowEmotionProvider>
    </IntlProvider>,
  );
}
