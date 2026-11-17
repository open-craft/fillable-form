"""
Minimal Django settings for running the fillable_form test suite.

These are only used by pytest (see ``[tool.pytest.ini_options]`` in
pyproject.toml); in production the block runs inside the LMS/CMS settings.
"""

SECRET_KEY = "fillable-form-tests-only"  # noqa: S105

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "fillable_form.apps.FillableFormConfig",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
USE_TZ = True
