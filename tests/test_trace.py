"""Cas limites BDD, sans Postgres réel."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from src.db.create_db import _native
from src.db.trace import get_employee_payload


def test_employe_absent_leve_value_error():
    """session.get → None : même erreur que l'API transforme en 404."""
    session = MagicMock()
    session.get.return_value = None
    with pytest.raises(ValueError, match="99"):
        get_employee_payload(session, 99)


def test_native_convertit_numpy_int():
    """pandas livre des np.int64 ; psycopg2 attend des int Python."""
    assert _native({"age": np.int64(41)})["age"] == 41
    assert isinstance(_native({"age": np.int64(41)})["age"], int)
