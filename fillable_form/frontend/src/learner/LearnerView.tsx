import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useIntl } from 'react-intl';
import { Button } from '@openedx/paragon';
import { Download } from '@openedx/paragon/icons';
import { postJson } from '../common/api';
import { LearnerConfig, SaveResponseResult } from '../common/types';
import { learnerMessages } from '../common/messages';

interface LearnerViewProps {
  initData: LearnerConfig;
}

export function LearnerView({ initData }: LearnerViewProps) {
  const { block_id, field_label, instructions, current_text,
          show_download_button, in_course_context, handler_urls } = initData;

  const inCourse = in_course_context !== false;

  const intl = useIntl();
  const [text, setText] = useState<string>(current_text);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [lastSaved, setLastSaved] = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSavedTextRef = useRef<string>(current_text);
  const currentTextRef = useRef<string>(current_text);

  const lastSavedTime = useMemo(
    () => (lastSaved ? new Date(lastSaved).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }) : null),
    [lastSaved],
  );

  const saveStatus = useMemo(() => {
    if (!inCourse) {
      return intl.formatMessage(learnerMessages.previewNotice);
    }
    if (saveState === 'saving') {
      return intl.formatMessage(learnerMessages.saving);
    }
    if (saveState === 'saved') {
      return lastSavedTime
        ? intl.formatMessage(learnerMessages.savedAt, { time: lastSavedTime })
        : intl.formatMessage(learnerMessages.saved);
    }
    if (saveState === 'error') {
      return intl.formatMessage(learnerMessages.error);
    }
    return intl.formatMessage(learnerMessages.saved);
  }, [inCourse, lastSavedTime, saveState, intl]);

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
    if (!inCourse) {
      return;
    }
    debounceRef.current = setTimeout(() => {
      saveResponse(newText);
    }, 1500);
  };

  const handleBlur = () => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    if (inCourse && text !== lastSavedTextRef.current) {
      saveResponse(text);
    }
  };

  const downloadUrl = show_download_button && inCourse
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
          placeholder={intl.formatMessage(learnerMessages.placeholder)}
          rows={6}
          aria-label={field_label || intl.formatMessage(learnerMessages.fallbackLabel)}
        />

        <div className="fillable-form-meta">
          <span className={`fillable-form-status fillable-form-status-${saveState}`}>
            {saveStatus}
          </span>
        </div>
      </div>

      {show_download_button && (
        <section className="fillable-form-download-panel" aria-labelledby={`${block_id}-download-title`}>
          <h3 id={`${block_id}-download-title`}>
            {intl.formatMessage(learnerMessages.downloadHeading)}
          </h3>
          <p>
            {intl.formatMessage(
              downloadUrl ? learnerMessages.downloadDescription : learnerMessages.downloadUnavailable,
            )}
          </p>
          <Button
            as="a"
            href={downloadUrl ?? undefined}
            target="_blank"
            variant="primary"
            iconBefore={Download}
            className="fillable-form-download-btn"
            disabled={!downloadUrl}
            aria-disabled={!downloadUrl}
          >
            {intl.formatMessage(learnerMessages.downloadButton)}
          </Button>
        </section>
      )}
    </div>
  );
}
