"""
Mock injection for edx-platform dependencies when running tests outside
of an Open edX environment.
"""

import sys
from unittest.mock import MagicMock, Mock


def setup_mocks():
    """Set up mock modules for edx-platform dependencies."""
    mocks = {
        "lms": MagicMock(),
        "lms.djangoapps": MagicMock(),
        "lms.djangoapps.course_blocks": MagicMock(),
        "lms.djangoapps.course_blocks.api": MagicMock(),
        "cms": MagicMock(),
        "cms.djangoapps": MagicMock(),
        "xmodule": MagicMock(),
        "xmodule.modulestore": MagicMock(),
        "xmodule.modulestore.django": MagicMock(),
        "opaque_keys": MagicMock(),
        "opaque_keys.edx": MagicMock(),
        "opaque_keys.edx.django": MagicMock(),
        "opaque_keys.edx.django.models": MagicMock(),
        "opaque_keys.edx.keys": MagicMock(),
        "model_utils": MagicMock(),
        "model_utils.models": MagicMock(),
        "webob": MagicMock(),
        "webob.response": MagicMock(),
    }
    for name, mock in mocks.items():
        if name not in sys.modules:
            sys.modules[name] = mock

    # Set up commonly used attributes
    sys.modules["lms.djangoapps.course_blocks.api"].get_course_blocks = Mock()
    sys.modules["xmodule.modulestore.django"].modulestore = Mock()


setup_mocks()
