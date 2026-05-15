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
  const currentTextRef = useRef<string>(current_text);

  const lastSavedTime = useMemo(
    () => (lastSaved ? new Date(lastSaved).toLocaleTimeString() : null),
    [lastSaved],
  );

  const saveStatus = useMemo(() => {
    if (saveState === 'saving') {
      return 'Saving changes...';
    }
    if (saveState === 'saved') {
      return lastSavedTime
        ? `Changes saved automatically at ${lastSavedTime}. You can close this page and return anytime.`
        : 'Changes saved automatically. You can close this page and return anytime.';
    }
    if (saveState === 'error') {
      return 'Save failed. Your text is preserved in this field.';
    }
    return 'Changes saved automatically. You can close this page and return anytime.';
  }, [lastSavedTime, saveState]);

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
        setSaveState(currentTextRef.current === textToSave ? 'saved' : 'idle');
        setLastSaved(result.modified || null);
        lastSavedTextRef.current = textToSave;
      } else {
        setSaveState(currentTextRef.current === textToSave ? 'error' : 'idle');
      }
    } catch {
      setSaveState(currentTextRef.current === textToSave ? 'error' : 'idle');
    }
  }, [handler_urls.save_response]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    currentTextRef.current = newText;

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
      {instructions && (
        <div
          className="fillable-form-instructions"
          dangerouslySetInnerHTML={{ __html: instructions }}
        />
      )}

      <div className="fillable-form-response">
        {field_label && (
          <p className="fillable-form-field-label">{field_label}</p>
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
          <span className={`fillable-form-status fillable-form-status-${saveState}`}>
            {saveStatus}
          </span>
        </div>
      </div>

      {downloadUrl && (
        <section className="fillable-form-download-panel" aria-labelledby={`${block_id}-download-title`}>
          <h3 id={`${block_id}-download-title`}>Download Exercise</h3>
          <p>Your response is part of a collection. Click Download to save them all as a PDF.</p>
          <Button
            as="a"
            href={downloadUrl}
            target="_blank"
            variant="primary"
            className="fillable-form-download-btn"
          >
            <span aria-hidden="true" className="fillable-form-download-icon" />
            Download PDF
          </Button>
        </section>
      )}
    </div>
  );
}
