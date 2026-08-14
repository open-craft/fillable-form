/** Init data passed from Python to Learner React app */
export interface LearnerConfig {
  block_id: string;
  field_label: string;
  instructions: string;         // HTML from TinyMCE
  current_text: string;
  show_download_button: boolean;
  in_course_context?: boolean;
  handler_urls: {
    save_response: string;
    download_pdf: string;
  };
  locale: string;
}

/** Init data passed from Python to Studio React app */
export interface StudioConfig {
  block_id: string;
  display_name: string;
  instructions: string;         // HTML from TinyMCE
  form_group_id: string;
  form_group_options: string[]; // Existing form group IDs in the course
  field_label: string;
  show_download_button: boolean;
  pdf_order: number;
  handler_urls: {
    studio_submit: string;
  };
  locale: string;
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
