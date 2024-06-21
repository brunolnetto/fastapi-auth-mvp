import pytest

from backend.app.utils.security import (
    is_email_valid,
    password_validity_obj,
    any_on_string,
    has_lowercase,
    has_uppercase,
    has_digit,
    has_special,
    has_min_length,
    without_space,
    password_must_have_str,
    password_cannot_have_str,
    get_password_validity_metadict,
    apply_password_validity_dict,
    get_invalid_password_conditions,
    is_password_valid,
    MIN_PASSWORD_LENGTH,
    CONDITION_LIST,
)


def test_is_email_valid_with_valid_email():
    assert is_email_valid("john.doe@example.com")


def test_is_email_valid_with_invalid_email():
    assert not is_email_valid("invalid_email")


def test_password_validity_obj_creation():
    invalid_message = "Password is too short"
    validity_map = lambda password: len(password) >= 8
    result = password_validity_obj(invalid_message, validity_map)
    assert result["invalidation_message"] == invalid_message
    assert result["validity_map"] is validity_map


def test_any_on_string_with_all_matches():
    assert any_on_string("hello123", str.isalnum)


def test_any_on_string_with_no_matches():
    assert not any_on_string("hello", str.isdigit)


def test_has_lowercase():
    assert has_lowercase("helloWorld")
    assert not has_lowercase("WORLD")


def test_has_uppercase():
    assert has_uppercase("HelloWorld")
    assert not has_uppercase("hello")


def test_has_digit():
    assert has_digit("hello123")
    assert not has_digit("hello")


def test_has_special():
    assert has_special("hello!@#$")
    assert not has_special("helloworld")


def test_has_min_length():
    assert has_min_length("password123", 8)
    assert not has_min_length("short", 5)


def test_has_min_length_default():
    assert has_min_length("password")


def test_without_space():
    assert without_space("no_spaces")
    assert not without_space("with spaces")


def test_password_must_have_str():
    message="Password must have lowercase characters"
    assert password_must_have_str("lowercase characters") == message


def test_password_cannot_have_str():
    assert password_must_have_str("spaces") == "Password must have spaces"


def test_get_password_validity_metadict():
    metadict = get_password_validity_metadict()
    assert len(metadict) == len(CONDITION_LIST)
    assert all(key in metadict for key, _, _ in CONDITION_LIST)


def test_apply_password_validity_dict_with_valid_password():
    password = "ThisIsAValid!P@ssw0rd"
    validity_dict = apply_password_validity_dict(password)
    assert all(condition["is_valid"] for condition in validity_dict.values())


def test_apply_password_validity_dict_with_invalid_password():
    password = "short123"
    validity_dict = apply_password_validity_dict(password)
    assert not all(condition["is_valid"] for condition in validity_dict.values())


def test_get_invalid_password_conditions_with_valid_password():
    password = "ThisIsAValid!P@ssw0rd"
    invalid_conditions = get_invalid_password_conditions(password)
    assert not invalid_conditions


def test_get_invalid_password_conditions_with_invalid_password():
    password = "short123"
    invalid_conditions = get_invalid_password_conditions(password)
    assert len(invalid_conditions) > 0
