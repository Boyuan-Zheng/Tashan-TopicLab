from sqlalchemy.exc import IntegrityError

import app.api.auth as auth_module


class _FakeOrig:
    def __init__(self, message: str):
        self.args = (message,)
        self._message = message

    def __str__(self) -> str:
        return self._message


def _make_integrity_error(message: str) -> IntegrityError:
    return IntegrityError(
        statement="INSERT INTO users (phone, password, username) VALUES (?, ?, ?)",
        params=("13800000000", "hashed", "tester"),
        orig=_FakeOrig(message),
    )


def test_phone_unique_violation_is_detected():
    exc = _make_integrity_error("duplicate key value violates unique constraint 'users_phone_key'")
    assert auth_module._is_phone_unique_violation(exc) is True


def test_non_phone_integrity_error_is_not_misreported_as_registered():
    exc = _make_integrity_error("duplicate key value violates unique constraint 'digital_twins_user_id_agent_name_key'")
    assert auth_module._is_phone_unique_violation(exc) is False
