from __future__ import annotations

from django.contrib import admin
from django.urls import path, include
from voting.views_web import home


admin.site.site_header = "Nepal Election Voting System"
admin.site.site_title = "Nepal Voting Admin"
admin.site.index_title = "Administration Dashboard"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("", include("voting.urls_web")),
    path("api/", include("voting.urls_api")),
]