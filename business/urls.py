# business/urls.py
from django.urls import path
from .views_my import MyOverviewView, MyListView
from .views_admin import AdminSearchView

urlpatterns = [
    path('training/my/overview', MyOverviewView.as_view()),
    path('training/my/list',     MyListView.as_view()),
    path('training/admin/search',AdminSearchView.as_view()),
]
