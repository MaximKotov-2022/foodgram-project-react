from django.conf import settings
from django.core.validators import MaxLengthValidator, RegexValidator
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from .models import Follow, User


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            MaxLengthValidator(
                settings.MAX_LENGTH_EMAIL,
                message=(f"Длина email не должна"
                         f"превышать { settings.MAX_LENGTH_EMAIL } символа.")
            ),
        ],
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(regex=r"^[\w.@+-]+$",),
            MaxLengthValidator(settings.MAX_LENGTH_PERSONAL_DATA),
        ]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[
            MaxLengthValidator(
                settings.MAX_LENGTH_PERSONAL_DATA,
                message=f"Длина пароля не должна"
                        f"превышать { settings.MAX_LENGTH_PERSONAL_DATA }"
                        f"символов."
            ),
        ],

    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password',)
        write_only_fields = ('password',)

    def validate_username(self, value):
        if value == "me":
            raise serializers.ValidationError("Нельзя использовать имя 'me'")
        return value

    def to_representation(self, instance):
        """Исключаем из ответа поле is_subscribed при регистрации."""
        data = super().to_representation(instance)
        if self.context.get('view').action == 'create':
            data.pop('is_subscribed', None)
        return data

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserGetSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',
                  )

    def get_is_subscribed(self, obj):
        user_id = self.context.get('request').user.id
        return Follow.objects.filter(
            author=obj.id,
            user=user_id
        ).exists()


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Подписка уже существует.'
            )
        ]
