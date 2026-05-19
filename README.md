# Fillable Form XBlock

An Open edX XBlock that lets students fill in text fields progressively
throughout a course and download all their responses as a single PDF. Authors
place fields in any unit and group them with a **Form Group ID**. Fields
sharing the same group ID are aggregated in the downloaded document.

## Architecture

This repository contains both the XBlock and its Django plugin app in a single
package. The XBlock handles authoring (Studio) and learner interaction, while
the plugin app provides the database models and service layer.

| Component | Purpose |
|---|---|
| `FillableFormXBlock` | Studio editor + learner view + auto-save + PDF download handlers |
| `FormResponse` | Stores one learner response per field (`user` + `usage_key`) |
| `FillableFormField` | Denormalized registry of author metadata for efficient PDF field lookup |
| `pdf_generator.py` | Jinja2 HTML template → WeasyPrint PDF/A-3b |



## Features

- **Progressive form filling** - fields placed across multiple course units,
  responses persist independently
- **Auto-save** - debounced (1.5s) saves as the learner types, plus immediate
  save on blur
- **PDF download** - aggregates all fields in a form group into a single,
  timestamped PDF with student name, email, and course name
- **Author-managed PDF order** - `pdf_order` field lets authors control the
  sequence fields appear in the PDF (gaps encouraged: 10, 20, 30)
- **Rich-text instructions** - TinyMCE editor in Studio for authoring
  introduction text
- **Form group ID dropdown** - `Creatable` select lets authors pick an existing
  group or create a new one
- **React + Paragon frontend** - learner and studio views built with
  `@openedx/paragon` design system
- **Legacy Studio compatible** - dual CSS output (prefixed for legacy Studio,
  non-prefixed for LMS iframes and MFE Studio)

## Installation

```bash
pip install fillable-form-xblock
```

Then add `fillable_form` to the advanced module list of your course.

Run migrations:

```bash
tutor local run lms python manage.py lms migrate fillable_form
```

Restart the platform:

```bash
tutor local restart lms cms
```

### Dependencies

- Python >= 3.11
- Django 4.2
- XBlock >= 1.5.0, < 7.0
- pydantic >= 2.12.5, < 3
- WeasyPrint >= 57.2, < 62
- Jinja2 >= 3.0

Build-time (frontend):

- Node 18+
- React 18.2
- Paragon 23.x
- TypeScript 5.x
- Webpack 5

## Usage

1. In Studio, add a **Fillable Form** component to a unit.
2. Click **Edit** to open the Studio editor:
   - Set the **Display Name**.
   - Write an **Introduction** (rich text) with instructions for the learner.
   - Set the **Answer Field Label** - this appears as a heading in the PDF.
   - Choose or create a **Form Group ID** to link fields across units.
   - Set the **PDF Order** number (lower numbers appear first; use gaps like
     10, 20, 30 to leave room for future fields).
   - Toggle **Show PDF download button** if this field should surface the
     download.
3. Click **Save** - the field is registered for PDF generation.
4. Learners type their response into the text area. Their work saves
   automatically.
5. On any field with the download button enabled, learners click **Download
   PDF** to get a single document with all their responses from that form
   group.

## Development

```bash
# Install in editable mode
pip install -e .

# Build frontend
cd fillable_form/frontend
npm install
npm run build          # production
npm run watch          # development (rebuilds on change)
npm test               # run Jest tests
```

CSS is authored once in `src/fillable_form.css` and compiled by Webpack into
four outputs:
- `static/css/fillable_form.css` — non-prefixed (LMS iframes + MFE Studio)
- `static/css/fillable_form_studio.css` — `.fillable-form-block` prefixed
  (legacy Studio)
- `static/js/fillable_form_learner.js` — learner React bundle
- `static/js/fillable_form_studio.js` — studio React bundle

## License

AGPL-3.0
