from django.contrib.auth import update_session_auth_hash, get_user_model, authenticate
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers, exceptions
from rest_framework.authtoken.serializers import AuthTokenSerializer

from vk_api import VkApi, VkApiError

from authentication.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'created_at', 'updated_at',
                  'first_name', 'last_name', 'vk_id',
                  'password', 'confirm_password')
        read_only_fields = ('id', 'created_at', 'updated_at', 'vk_id',)

        def create(self, validated_data):
            return User.objects.create(**validated_data)

        def update(self, instance, validated_data):
            instance.first_name = validated_data.get('first_name', instance.first_name)
            instance.last_name = validated_data.get('last_name', instance.last_name)
            instance.vk_id = validated_data.get('vk_id', instance.vk_id)

            instance.save()

            password = validated_data.get('password', None)
            confirm_password = validated_data.get('confirm_password', None)

            if password and confirm_password and confirm_password == password:
                instance.set_password(password)
                instance.save()

            return instance


class VkTokenSerializer(serializers.Serializer):
    provider = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(max_length=40, required=False)
    email = serializers.EmailField(max_length=100, required=False)
    vk_token = serializers.CharField(max_length=255, required=False)

    def validate_vk(self, attrs):
        vk_token = attrs.get('vk_token')
        service_token = settings.VK_SERVICE_TOKEN
        client_secret = settings.VK_CLIENT_SECRET

        vk_session = VkApi(token=service_token, client_secret=client_secret)
        vk_api_wrapper = vk_session.get_api()

        try:
            check_results = vk_api_wrapper.secure.checkToken(token=vk_token)
            vk_id = check_results['user_id']
        except VkApiError as error:
            raise serializers.ValidationError('Invalid VK token', code='authorization')

        attrs["vk_id"] = vk_id
        User = get_user_model()
        try:
            attrs["user"] = User.objects.get(vk_id=vk_id)
            attrs["is_new_user"] = False
        except User.DoesNotExist:
            attrs["is_new_user"] = True

        if attrs["is_new_user"] and not attrs.get("email"):
            raise serializers.ValidationError('Must provide email when first time authorize via VK')

        try:
            same_email_user = User.objects.get(email=attrs.get('email'))
            if same_email_user and same_email_user.vk_id != vk_id:
                raise serializers.ValidationError('Email already in use')
        except User.DoesNotExist:
            pass # It's OK, email is g2g

        return attrs

    def validate_plane(self, attrs):
        auth_field = settings.DRF_AUTH_FIELD
        auth_field_value = attrs.get(auth_field)
        password = attrs.get('password')

        if auth_field and password:
            user = authenticate(**{
                auth_field: auth_field_value,
                "password": password
            }, request=self.context.get('request'))

            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg, code='authorization')
            else:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

    def validate(self, attrs):  # I know that sucks. If I'll have time left I WILL fix this
        auth_provider = attrs.get("provider")
        if auth_provider == "plain":
            return self.validate_plane(attrs)
        elif auth_provider == "vk":
            return self.validate_vk(attrs)
        else:
            raise serializers.ValidationError('Invalid authentication provider')
