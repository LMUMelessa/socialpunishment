from django.conf.urls import url
from pg_vote_famfeud import views

urlpatterns = [
    url('downloadguess', views.downloadguess, name='downloadguess')
]




