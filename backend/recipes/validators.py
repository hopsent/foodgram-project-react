import re

from django.forms import ValidationError


def validate_is_hex(value):
    """To check if value looks like hex-code."""
    v_len = len(value)
    if v_len != 7 or not re.match(
        '^\#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$',  # noqa: W605
        value
    ):
        raise ValidationError(
            'В поле цвет введите hex-значение e.g. #000000.',
            params={'value': value},
        )


def validate_max_size_text(value):
    """To check if it's too many symbols in text-field."""
    v_len = len(value)
    if v_len > 512:
        raise ValidationError(
            'Длина текста рецепта не должна превышать 512 символов.',
            params={'value': value},
        )
