from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="paper_vault_index"),
    path("submit/", views.submit_paper, name="paper_vault_submit"),
    path("review/", views.review_queue, name="paper_vault_review"),
    path("review/<int:pk>/", views.review_action, name="paper_vault_review_action"),
]