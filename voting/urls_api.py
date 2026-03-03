from django.urls import path
from . import views_api

urlpatterns = [
    path("auth/register", views_api.api_register),
    path("auth/login", views_api.api_login),

    path("elections", views_api.api_elections),
    path("elections/<int:election_id>/candidates", views_api.api_candidates),
    path("elections/<int:election_id>/vote", views_api.api_vote),
    path("elections/<int:election_id>/results", views_api.api_results),
]