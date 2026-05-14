import { Editor } from '@tinymce/tinymce-react';

// TinyMCE core modules — explicit imports bundle everything needed
import 'tinymce/tinymce';
import 'tinymce/models/dom/model';
import 'tinymce/themes/silver';
import 'tinymce/icons/default';
import 'tinymce/skins/ui/oxide/skin';

// Plugins
import 'tinymce/plugins/advlist';
import 'tinymce/plugins/autolink';
import 'tinymce/plugins/code';
import 'tinymce/plugins/fullscreen';
import 'tinymce/plugins/help';
import 'tinymce/plugins/help/js/i18n/keynav/en';
import 'tinymce/plugins/link';
import 'tinymce/plugins/lists';
import 'tinymce/plugins/quickbars';
import 'tinymce/plugins/table';

// Content styles
import 'tinymce/skins/content/default/content';
import 'tinymce/skins/ui/oxide/content';

interface TinyMceEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export function TinyMceEditor({ value, onChange }: TinyMceEditorProps) {
  return (
    <Editor
      licenseKey="gpl"
      value={value}
      onEditorChange={(newValue) => onChange(newValue)}
      init={{
        promotion: false,
        menubar: false,
        height: 300,
        plugins: [
          'advlist', 'autolink', 'lists', 'link',
          'quickbars', 'table', 'code', 'fullscreen', 'help',
        ],
        toolbar: [
          'undo redo | blocks | bold italic underline forecolor | '
          + 'alignleft aligncenter alignright | bullist numlist | '
          + 'link unlink | table | removeformat | code | fullscreen | help',
        ],
        quickbars_selection_toolbar:
          'bold italic underline | blocks | bullist numlist',
        contextmenu: false,
      }}
    />
  );
}
