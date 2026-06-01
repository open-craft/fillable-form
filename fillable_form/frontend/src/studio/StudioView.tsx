import { useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import Creatable from 'react-select/creatable';
import { Button, Form, StatefulButton } from '@openedx/paragon';
import { postJson } from '../common/api';
import { StudioConfig, HandlerResponse } from '../common/types';
import { studioMessages } from '../common/messages';
import { TinyMceEditor } from './TinyMceEditor';

const NOTIFY_SAVE = 'save';
const NOTIFY_ERROR = 'error';
const NOTIFY_CANCEL = 'cancel';

interface StudioViewProps {
  initData: StudioConfig;
  runtime: {
    notify?: (action: string, data?: Record<string, unknown>) => void;
  };
}

const fieldId = (blockId: string, prefix: string) => `${prefix}-${blockId}`;

export function StudioView({ initData, runtime }: StudioViewProps) {
  const { block_id, display_name, instructions, form_group_id,
          form_group_options, field_label, show_download_button,
          pdf_order, handler_urls } = initData;

  const intl = useIntl();
  const [displayName, setDisplayName] = useState(display_name);
  const [instructionsText, setInstructionsText] = useState(instructions);
  const [formGroupId, setFormGroupId] = useState(form_group_id);
  const [fieldLabel, setFieldLabel] = useState(field_label);
  const [showDownloadButton, setShowDownloadButton] = useState(show_download_button);
  const [pdfOrder, setPdfOrder] = useState<string>(String(pdf_order));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const groupOptions = useMemo(
    () => form_group_options.map((id) => ({ value: id, label: id })),
    [form_group_options],
  );

  const notifyError = (message: string) => {
    setError(message);
    runtime.notify?.(NOTIFY_ERROR, {
      title: intl.formatMessage(studioMessages.errorTitle),
      message,
    });
  };

  const handleSave = async () => {
    if (saving) {
      return;
    }

    const pdfOrderError = intl.formatMessage(studioMessages.errorPdfOrder);

    if (pdfOrder.trim() === '') {
      notifyError(pdfOrderError);
      return;
    }

    const parsedPdfOrder = Number(pdfOrder);
    if (!Number.isInteger(parsedPdfOrder) || parsedPdfOrder < 0) {
      notifyError(pdfOrderError);
      return;
    }

    setSaving(true);
    setError(null);
    runtime.notify?.(NOTIFY_SAVE, { state: 'start' });

    try {
      const result = await postJson<HandlerResponse>(
        handler_urls.studio_submit,
        {
          display_name: displayName,
          instructions: instructionsText,
          form_group_id: formGroupId,
          field_label: fieldLabel,
          show_download_button: showDownloadButton,
          pdf_order: parsedPdfOrder,
        },
      );

      if (result.success) {
        runtime.notify?.(NOTIFY_SAVE, { state: 'end' });
      } else {
        notifyError(result.error || intl.formatMessage(studioMessages.errorSaveFailed));
      }
    } catch {
      notifyError(intl.formatMessage(studioMessages.errorNetwork));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    runtime.notify?.(NOTIFY_CANCEL, {});
  };

  return (
    <div className="fillable-form-block">
      <div className="fillable-form-studio">
        <Form.Group>
          <Form.Label htmlFor={fieldId(block_id, 'display-name')}>
            {intl.formatMessage(studioMessages.labelDisplayName)}
          </Form.Label>
          <Form.Control
            id={fieldId(block_id, 'display-name')}
            type="text"
            value={displayName}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setDisplayName(e.target.value)
            }
          />
        </Form.Group>

        <Form.Group>
          <Form.Label htmlFor={fieldId(block_id, 'instructions')}>
            {intl.formatMessage(studioMessages.labelInstructions)}
          </Form.Label>
          <Form.Control.Feedback>
            {intl.formatMessage(studioMessages.helpInstructions)}
          </Form.Control.Feedback>
          <TinyMceEditor
            id={fieldId(block_id, 'instructions')}
            ariaLabel={intl.formatMessage(studioMessages.labelInstructions)}
            value={instructionsText}
            onChange={setInstructionsText}
          />
        </Form.Group>

        <Form.Group>
          <Form.Label htmlFor={fieldId(block_id, 'field-label')}>
            {intl.formatMessage(studioMessages.labelFieldLabel)}
          </Form.Label>
          <Form.Control.Feedback>
            {intl.formatMessage(studioMessages.helpFieldLabel)}
          </Form.Control.Feedback>
          <Form.Control
            id={fieldId(block_id, 'field-label')}
            type="text"
            value={fieldLabel}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setFieldLabel(e.target.value)
            }
          />
        </Form.Group>

        <Form.Group>
          <Form.Label htmlFor={fieldId(block_id, 'form-group-id')}>
            {intl.formatMessage(studioMessages.labelFormGroupId)}
          </Form.Label>
          <Form.Control.Feedback>
            {intl.formatMessage(studioMessages.helpFormGroupId)}
          </Form.Control.Feedback>
          <Creatable
            inputId={fieldId(block_id, 'form-group-id')}
            classNamePrefix="fillable-form-select"
            isClearable
            options={groupOptions}
            value={formGroupId ? { value: formGroupId, label: formGroupId } : null}
            onChange={(option) => setFormGroupId(option?.value || '')}
            placeholder={intl.formatMessage(studioMessages.placeholderFormGroupId)}
            formatCreateLabel={(inputValue) =>
              intl.formatMessage(studioMessages.createFormGroupId, { inputValue })
            }
          />
        </Form.Group>

        <Form.Group>
          <Form.Label htmlFor={fieldId(block_id, 'pdf-order')}>
            {intl.formatMessage(studioMessages.labelPdfOrder)}
          </Form.Label>
          <Form.Control.Feedback>
            {intl.formatMessage(studioMessages.helpPdfOrder)}
          </Form.Control.Feedback>
          <Form.Control
            id={fieldId(block_id, 'pdf-order')}
            type="number"
            min={0}
            value={pdfOrder}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setPdfOrder(e.target.value)
            }
          />
        </Form.Group>

        <Form.Group>
          <Form.Checkbox
            id={fieldId(block_id, 'show-download')}
            checked={showDownloadButton}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setShowDownloadButton(e.target.checked)
            }
          >
            {intl.formatMessage(studioMessages.labelShowDownload)}
          </Form.Checkbox>
        </Form.Group>

        {error && (
          <div className="fillable-form-studio-error">{error}</div>
        )}

        <div className="fillable-form-studio-actions">
          <StatefulButton
            variant="primary"
            onClick={handleSave}
            state={saving ? 'pending' : 'default'}
            labels={{
              default: intl.formatMessage(studioMessages.buttonSave),
              pending: intl.formatMessage(studioMessages.buttonSaving),
              complete: intl.formatMessage(studioMessages.buttonSaved),
              error: intl.formatMessage(studioMessages.buttonError),
            }}
          />
          <Button variant="link" onClick={handleCancel}>
            {intl.formatMessage(studioMessages.buttonCancel)}
          </Button>
        </div>
      </div>
    </div>
  );
}
