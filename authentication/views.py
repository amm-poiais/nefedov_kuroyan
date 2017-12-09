import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render

from rest_framework import parsers, permissions, viewsets, views, mixins, status, renderers
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response
from vk_api import VkApi

from authentication.models import User
from authentication.permissions import IsAccountOwner
from authentication.serializers import UserSerializer, VkTokenSerializer

# Create your views here.


class AccountViewSet(mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    lookup_field = 'id'
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS or self.request.method == "POST":
            return permissions.AllowAny(),

        return permissions.IsAuthenticated(), IsAccountOwner(),

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            User.objects.create_user(**serializer.validated_data)
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'Bad request',
            'message': "Can't create account with provided data",
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def list(self):
        return Response({
            'status': 'Forbidden',
            'message': "It's illigal to list users",
        }, status=status.HTTP_403_FORBIDDEN)


class ObtainAuthTokenMultiView(views.APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser)
    renderer_classes = (renderers.JSONRenderer, )
    serializer_class = VkTokenSerializer

    def get_user(self, validated_data):
        User = get_user_model()

        if validated_data.get("is_new_user"):
            vk_api_wrapper = VkApi().get_api()

            vk_id = validated_data.get("vk_id")
            email = validated_data.get("email")
            user_info = vk_api_wrapper.users.get(user_id=vk_id)[0]

            user, created = User.objects.update_or_create(email=email, defaults={
                "vk_id": vk_id,
                "first_name": user_info["first_name"],
                "last_name": user_info["last_name"],
            })
            return user
        else:
            return validated_data["user"]

    def post(self, request: Request, *args, **kwargs):
        logger = logging.getLogger('heroku')
        logger.info('Request body: '.format(request.body))

        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = self.get_user(serializer.validated_data)
        token, token_created = Token.objects.get_or_create(user=user)
        return Response({
            'id': user.id,
            'token': token.key,
        })
