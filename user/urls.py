from django.urls import path
from user import views

urlpatterns = [
    path("", views.user_list_view, name="user_list"),
    path("<str:id>/", views.user_detail_view, name="user_detail"),
    path("<str:id>/delete", views.delete_admin_or_moderatorv_view, name="delete_admin_or_moderatorv_view"),
    path("<str:id>/photo/", views.photo_upload_view, name="user_photo_upload"),
    path("<str:id>/like/<str:friend_id>/", views.user_like_view, name="user_like"),
    path("<str:id>/reports/", views.delete_reports_view, name="delete_reports"),
    path("moderator/transfer", views.transfer_moderator_view, name="transfer_moderator_view"),
]

https://api.chatadmin-mod.click/admin/user/instagramscrapy/