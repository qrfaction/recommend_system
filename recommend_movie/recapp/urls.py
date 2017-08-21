from django.conf.urls import url
from . import views
from . import api

urlpatterns = [
    url(r'^users-list/',api.UsersList.as_view(),name='users-list'),
    url(r'^auth/$',views.auth, name='auth'),
    url(r'^$', views.home, name='home'),
    url(r'^rate_movie/',views.rate_movie,name='rate_movie'),
    url(r'^movies-recs/',views.movies_recs,name='movies-recs'),
    url(r'^signout/',views.signout,name='signout'),
]