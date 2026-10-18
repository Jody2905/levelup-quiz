from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("levels/<slug:slug>/", views.level_detail, name="level_detail"),
    path("quiz/<slug:slug>/", views.quiz_detail, name="quiz_detail"),
    path("quiz/<slug:slug>/start/", views.start_quiz, name="start_quiz"),
    path("attempt/<int:pk>/", views.take_attempt, name="take_attempt"),
    path("attempt/<int:pk>/result/", views.attempt_result, name="attempt_result"),
    path("history/", views.history, name="history"),
    path("signup/", views.signup, name="signup"),
]
