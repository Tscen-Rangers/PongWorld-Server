from django.urls import path
from . import views

app_name = "blocks"

urlpatterns = [
    path("<int:to_block_id>/", views.BlocksView.as_view({'post': 'block_user'}), name="block_user"),
    path("cancel/<int:blocked_id>/", views.BlocksView.as_view({'delete': 'unblocked_user'}), name="unblocked_user"),
    path("search/", views.SearchBlockingView.as_view({'get': 'get_all_blockings'}), name="get_all_blockings"),
    path('search/<str:name>/', views.SearchBlockingView.as_view({'get': 'get_blockings'}), name="get_blockings"),
]