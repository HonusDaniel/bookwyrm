"""fedireads URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from fedireads import federation, openlibrary, views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home),
    path('login/', views.user_login),
    path('logout/', views.user_logout),
    path('user/<str:username>', views.user_profile),
    path('book/<str:book_identifier>', views.book_page),

    path('review/', views.review),
    path('shelve/<str:shelf_id>/<int:book_id>', views.shelve),
    path('follow/', views.follow),
    path('unfollow/', views.unfollow),
    path('search/', views.search),

    path('api/u/<str:username>', federation.get_actor),
    path('api/u/<str:username>/inbox', federation.inbox),
    path('api/u/<str:username>/outbox', federation.outbox),
    path('.well-known/webfinger', federation.webfinger),
]
