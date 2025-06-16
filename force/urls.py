# force/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('ai/ask/', views.ask_gemini, name='ask_gemini'),
    path('', views.chat_view, name='chat_view'), # غير هذا السطر من 'chat/' إلى ''
]