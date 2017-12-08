from django.conf.urls import url, include
from django.conf import settings
from rest_framework.routers import SimpleRouter
from authentication.views import AccountViewSet, ObtainAuthTokenMultiView
from game_stats.views import UpdateScoreView

router = SimpleRouter()
router.register(r'account', AccountViewSet)

urlpatterns = [
    url(r'^token/obtain/$', ObtainAuthTokenMultiView.as_view(), name='obtain_token'),
    url(r'^score/(?P<game_id>[0-9]+)/(?P<difficulty_id>[0-9]+)/', UpdateScoreView.as_view(), name='score')
]

urlpatterns += router.urls
