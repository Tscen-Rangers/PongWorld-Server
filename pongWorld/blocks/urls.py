from django.urls import path
from . import views

app_name = "blocks"

urlpatterns = [
    path("<int:to_block_id>/", views.BlocksView.as_view({'post': 'block_user'}), name="block_user"),
    path("cancel/<int:blocked_id>/", views.BlocksView.as_view({'delete': 'unblocked_user'}), name="unblocked_user"),
    path("list/", views.BlocksView.as_view({'get': 'get_blocking_users'}), name="get_blocking_users"),
]