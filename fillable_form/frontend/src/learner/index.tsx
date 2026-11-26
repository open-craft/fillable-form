import { IntlProvider } from 'react-intl';
import {
  createXBlockRoot,
  type XBlockRuntime,
} from '@opencraft/xblock-react-utils';
import { LearnerView } from './LearnerView';
import { LearnerConfig } from '../common/types';
import styles from '../fillable_form.css';

export function renderBlock(
  runtime: XBlockRuntime,
  element: HTMLElement,
  initData: LearnerConfig,
): Promise<void> {
  // createXBlockRoot mounts the app inside a shadow DOM and injects our CSS
  // plus Paragon's core and theme stylesheets, so Paragon layout components
  // (Stack, Icon, ...) are styled and host-page CSS does not leak in.
  return createXBlockRoot({ runtime, element, config: initData.config, styles })(
    <IntlProvider locale={initData.locale} messages={{}}>
      <LearnerView initData={initData} />
    </IntlProvider>,
  );
}
