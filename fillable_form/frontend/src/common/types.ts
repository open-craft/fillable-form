/** Init data passed from Python to Learner React app */
import type { XBlockConfig } from '@opencraft/xblock-react-utils';

export interface LearnerConfig {
  block_id: string;
  display_name: string;
  icon: string;                 // Material Icons (outlined) name
  field_label: string;
  instructions: string;         // HTML from TinyMCE
  current_text: string;
  show_download_button: boolean;
  download_button_info: string;
  color_variant: string;        // Id from COLOR_VARIANTS, or 'default'
  in_course_context?: boolean;
  handler_urls: {
    save_response: string;
    download_pdf: string;
  };
  locale: string;
  config: XBlockConfig;
}

/** Init data passed from Python to Studio React app */
export interface StudioConfig {
  block_id: string;
  display_name: string;
  icon: string;                 // Material Icons (outlined) name
  instructions: string;         // HTML from TinyMCE
  form_group_id: string;
  form_group_options: string[]; // Existing form group IDs in the course
  field_label: string;
  show_download_button: boolean;
  download_button_info: string;
  color_variant: string;        // Id from COLOR_VARIANTS, or 'default'
  pdf_order: number;
  handler_urls: {
    studio_submit: string;
  };
  locale: string;
  config: XBlockConfig;
}

/** Standard JSON handler response */
export interface HandlerResponse {
  success: boolean;
  error?: string;
}

/** Save response result */
export interface SaveResponseResult extends HandlerResponse {
  modified?: string;
}
