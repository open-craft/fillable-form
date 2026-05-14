import { useMemo, useState } from 'react';
import Creatable from 'react-select/creatable';
import { Button, Form, StatefulButton } from '@openedx/paragon';
import { postJson } from '../common/api';
import { StudioConfig, HandlerResponse } from '../common/types';
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
    runtime.notify?.(NOTIFY_ERROR, { title: 'Save Error', message });
  };

  const handleSave = async () => {
    if (pdfOrder.trim() === '') {
      notifyError('PDF Order must be a non-negative whole number.');
      return;
    }

    const parsedPdfOrder = Number(pdfOrder);
    if (!Number.isInteger(parsedPdfOrder) || parsedPdfOrder < 0) {
      notifyError('PDF Order must be a non-negative whole number.');
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
        notifyError(result.error || 'Save failed.');
      }
    } catch {
      notifyError('Network error while saving.');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    runtime.notify?.(NOTIFY_CANCEL, {});
  };

  return (
    <div className="fillable-form-studio">
      <Form.Group>
        <Form.Label htmlFor={fieldId(block_id, 'display-name')}>
          Display Name
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
        <Form.Label htmlFor={fieldId(block_id, 'field-label')}>
          Field Label
        </Form.Label>
        <Form.Control
          id={fieldId(block_id, 'field-label')}
          type="text"
          value={fieldLabel}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setFieldLabel(e.target.value)
          }
        />
        <Form.Control.Feedback>
          This label appears as a section heading in the downloaded PDF.
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group>
        <Form.Label htmlFor={fieldId(block_id, 'pdf-order')}>
          PDF Order
        </Form.Label>
        <Form.Control
          id={fieldId(block_id, 'pdf-order')}
          type="number"
          min={0}
          value={pdfOrder}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setPdfOrder(e.target.value)
          }
        />
        <Form.Control.Feedback>
          Lower numbers appear first in the downloaded PDF. Use gaps like 10, 20, 30 to leave room for future fields.
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group>
        <Form.Label htmlFor={fieldId(block_id, 'form-group-id')}>
          Form Group ID
        </Form.Label>
        <Creatable
          inputId={fieldId(block_id, 'form-group-id')}
          isClearable
          options={groupOptions}
          value={formGroupId ? { value: formGroupId, label: formGroupId } : null}
          onChange={(option) => setFormGroupId(option?.value || '')}
          placeholder="Select or type a new group..."
          formatCreateLabel={(inputValue) => `Create "${inputValue}"`}
        />
        <Form.Control.Feedback>
          Fields with the same Form Group ID are aggregated in the downloaded PDF.
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group>
        <Form.Label htmlFor={fieldId(block_id, 'instructions')}>
          Instructions
        </Form.Label>
        <TinyMceEditor
          value={instructionsText}
          onChange={setInstructionsText}
        />
        <Form.Control.Feedback>
          Rich-text instructions shown to students above the text area. HTML is supported.
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group>
        <Form.Checkbox
          id={fieldId(block_id, 'show-download')}
          checked={showDownloadButton}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setShowDownloadButton(e.target.checked)
          }
        >
          Show download button on this field
        </Form.Checkbox>
      </Form.Group>

      {error && (
        <div className="fillable-form-studio-error">{error}</div>
      )}

      <div className="fillable-form-studio-actions">
        <Button variant="secondary" onClick={handleCancel}>
          Cancel
        </Button>
        <StatefulButton
          variant="primary"
          onClick={handleSave}
          state={saving ? 'pending' : 'default'}
          labels={{
            default: 'Save',
            pending: 'Saving...',
            complete: 'Saved',
            error: 'Error',
          }}
        />
      </div>
    </div>
  );
}
