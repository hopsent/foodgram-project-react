import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
import webcolors


class Hex2NameColor(serializers.Field):
    """
    To customize field 'color', which is used by
    serializer related to :model:'recipes.Tag'.
    """

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError(
                'Для этого цвета нет имени.'
            )
        return data


class Base64ImageField(serializers.ImageField):
    """
    To customize field 'image', which is used by
    serializer related to :model:'recipes.Recipe'.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name='temp.' + ext
            )

        return super().to_internal_value(data)
