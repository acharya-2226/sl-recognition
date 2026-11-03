from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("learn/", views.learn, name="learn"),
    path("learn/category/<int:category_id>/", views.category_detail, name="category_detail"),
    path("learn/item/<int:item_id>/", views.item_detail, name="item_detail"),
    path("practice/", views.practice, name="practice"),
    path("practice/check/", views.practice_check, name="practice_check"),
    path("test/", views.test_page, name="test_page"),
    path("test/category/<int:category_id>/", views.test_category, name="test_category"),
    path("tts/", views.tts, name="tts"),
    path("api/validate/<int:category_id>/", views.validate_api, name="validate_api"),

]
