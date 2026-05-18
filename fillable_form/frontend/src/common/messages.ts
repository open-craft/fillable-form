import { defineMessages } from 'react-intl';

export const learnerMessages = defineMessages({
  saving: {
    id: 'fillable.form.learner.saving',
    defaultMessage: 'Saving changes...',
  },
  savedAt: {
    id: 'fillable.form.learner.saved.at',
    defaultMessage: 'Changes saved automatically at {time}. You can close this page and return anytime.',
  },
  saved: {
    id: 'fillable.form.learner.saved',
    defaultMessage: 'Changes saved automatically. You can close this page and return anytime.',
  },
  error: {
    id: 'fillable.form.learner.error',
    defaultMessage: 'Save failed. Your text is preserved in this field.',
  },
  placeholder: {
    id: 'fillable.form.learner.placeholder',
    defaultMessage: 'Type your response...',
  },
  fallbackLabel: {
    id: 'fillable.form.learner.fallback.label',
    defaultMessage: 'Form field',
  },
  downloadHeading: {
    id: 'fillable.form.learner.download.heading',
    defaultMessage: 'Download Exercise',
  },
  downloadDescription: {
    id: 'fillable.form.learner.download.description',
    defaultMessage: 'Your response is part of a collection. Click Download to save them all as a PDF.',
  },
  downloadButton: {
    id: 'fillable.form.learner.download.button',
    defaultMessage: 'Download PDF',
  },
});

export const studioMessages = defineMessages({
  errorTitle: {
    id: 'fillable.form.studio.error.title',
    defaultMessage: 'Save Error',
  },
  errorPdfOrder: {
    id: 'fillable.form.studio.error.pdf.order',
    defaultMessage: 'PDF Order must be a non-negative whole number.',
  },
  errorSaveFailed: {
    id: 'fillable.form.studio.error.save.failed',
    defaultMessage: 'Save failed.',
  },
  errorNetwork: {
    id: 'fillable.form.studio.error.network',
    defaultMessage: 'Network error while saving.',
  },
  labelDisplayName: {
    id: 'fillable.form.studio.label.display.name',
    defaultMessage: 'Display Name',
  },
  labelInstructions: {
    id: 'fillable.form.studio.label.instructions',
    defaultMessage: 'Introduction',
  },
  helpInstructions: {
    id: 'fillable.form.studio.help.instructions',
    defaultMessage: 'The introduction shows above the answer field. Include any instructions the learner might need',
  },
  labelFieldLabel: {
    id: 'fillable.form.studio.label.field.label',
    defaultMessage: 'Answer Field Label',
  },
  helpFieldLabel: {
    id: 'fillable.form.studio.help.field.label',
    defaultMessage: 'Provide a name for the field learners use to answer the question',
  },
  labelFormGroupId: {
    id: 'fillable.form.studio.label.form.group.id',
    defaultMessage: 'Form Group ID',
  },
  placeholderFormGroupId: {
    id: 'fillable.form.studio.placeholder.form.group.id',
    defaultMessage: 'Add group ID',
  },
  createFormGroupId: {
    id: 'fillable.form.studio.create.form.group.id',
    defaultMessage: 'Create "{inputValue}"',
  },
  helpFormGroupId: {
    id: 'fillable.form.studio.help.form.group.id',
    defaultMessage: 'Select a Group ID to connect fields across units for a PDF version. Create a new Group ID by typing the title and selecting "create" from the bottom of the list.',
  },
  labelPdfOrder: {
    id: 'fillable.form.studio.label.pdf.order',
    defaultMessage: 'PDF Order',
  },
  helpPdfOrder: {
    id: 'fillable.form.studio.help.pdf.order',
    defaultMessage: 'Lower numbers appear first in the downloaded PDF. Use gaps like 10, 20, 30 to leave room for future fields.',
  },
  labelShowDownload: {
    id: 'fillable.form.studio.label.show.download',
    defaultMessage: 'Show PDF download button on this field',
  },
  buttonSave: {
    id: 'fillable.form.studio.button.save',
    defaultMessage: 'Save',
  },
  buttonSaving: {
    id: 'fillable.form.studio.button.saving',
    defaultMessage: 'Saving...',
  },
  buttonSaved: {
    id: 'fillable.form.studio.button.saved',
    defaultMessage: 'Saved',
  },
  buttonError: {
    id: 'fillable.form.studio.button.error',
    defaultMessage: 'Error',
  },
  buttonCancel: {
    id: 'fillable.form.studio.button.cancel',
    defaultMessage: 'Cancel',
  },
});
