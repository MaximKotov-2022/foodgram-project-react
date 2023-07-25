from rest_framework import serializers


def validate_username(value):
    if value.lower() == 'me':
        raise serializers.ValidationError(
            'Недопустимый псевдоним "me"'
        )
    return value
