from django.urls import path
from . import views_web
from .views_ajax import constituencies_by_district


urlpatterns = [
    # Home
    path("", views_web.home, name="home"),

    # Auth (keep old names + add new aliases)
    path("register/", views_web.web_register, name="web_register"),
    path("register/", views_web.web_register, name="register"),  # alias for templates

    path("login/", views_web.web_login, name="web_login"),
    path("login/", views_web.web_login, name="login"),  # alias for templates

    path("logout/", views_web.web_logout, name="web_logout"),
    path("logout/", views_web.web_logout, name="logout"),  # alias for templates

    # Voter
    path("voter/profile/", views_web.voter_profile, name="voter_profile"),

    path("voter/elections/<int:election_id>/vote/", views_web.voter_vote, name="voter_vote"),
    path("voter/elections/<int:election_id>/vote/", views_web.voter_vote, name="vote_page"),  # alias

    # Results (keep old names + add new aliases)
    path("results/", views_web.results_elections, name="results_elections"),
    path("results/", views_web.results_elections, name="results"),  # alias for templates

    path("results/<int:election_id>/", views_web.results_view, name="results_view"),
    path("results/<int:election_id>/", views_web.results_view, name="results_detail"),  # alias

    # AJAX
    path("ajax/constituencies/", constituencies_by_district, name="ajax_constituencies"),
]