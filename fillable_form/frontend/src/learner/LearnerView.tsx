import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Button } from '@openedx/paragon';
import { postJson } from '../common/api';
import { LearnerConfig, SaveResponseResult } from '../common/types';

interface LearnerViewProps {
  initData: LearnerConfig;
}

export function LearnerView({ initData }: LearnerViewProps) {
  const { block_id, field_label, instructions, current_text,
          show_download_button, handler_urls } = initData;

  const [text, setText] = useState<string>(current_text);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [lastSaved, setLastSaved] = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSavedTextRef = useRef<string>(current_text);

  const lastSavedTime = useMemo(
    () => (lastSaved ? new Date(lastSaved).toLocaleTimeString() : null),
    [lastSaved],
  );

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const saveResponse = useCallback(async (textToSave: string) => {
    setSaveState('saving');
    try {
      const result = await postJson<SaveResponseResult>(
        handler_urls.save_response,
        { response_text: textToSave },
      );
      if (result.success) {
        setSaveState('saved');
        setLastSaved(result.modified || null);
        lastSavedTextRef.current = textToSave;
      } else {
        setSaveState('error');
      }
    } catch {
      setSaveState('error');
    }
  }, [handler_urls.save_response]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (newText === lastSavedTextRef.current) {
      if (newText !== text) {
        setText(newText);
      }
      setSaveState('idle');
      return;
    }

    setText(newText);
    setSaveState('idle');
    debounceRef.current = setTimeout(() => {
      saveResponse(newText);
    }, 1500);
  };

  const handleBlur = () => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    if (text !== lastSavedTextRef.current) {
      saveResponse(text);
    }
  };

  const downloadUrl = show_download_button
    ? handler_urls.download_pdf
    : null;

  return (
    <div className="fillable-form-learner" data-block-id={block_id}>
      {field_label && (
        <h3 className="fillable-form-field-label">{field_label}</h3>
      )}

      {instructions && (
        <div
          className="fillable-form-instructions"
          dangerouslySetInnerHTML={{ __html: instructions }}
        />
      )}

      <textarea
        className="fillable-form-textarea"
        value={text}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder="Type your response..."
        rows={6}
        aria-label={field_label || 'Form field'}
      />

      <div className="fillable-form-meta">
        {saveState === 'saving' && (
          <span className="fillable-form-saving">
            Saving...
          </span>
        )}
        {saveState === 'saved' && (
          <span className="fillable-form-saved">
            Saved{lastSavedTime ? ` at ${lastSavedTime}` : ''}
          </span>
        )}
        {saveState === 'error' && (
          <span className="fillable-form-error">
            Save failed — your text is preserved in this field.
          </span>
        )}

        {downloadUrl && (
          <Button
            as="a"
            href={downloadUrl}
            target="_blank"
            variant="primary"
            className="fillable-form-download-btn"
          >
            Download Form
          </Button>
        )}
      </div>
    </div>
  );
}
