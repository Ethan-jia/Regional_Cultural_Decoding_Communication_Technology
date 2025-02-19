"""listen1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path, re_path
from app import views
from api import views as u_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('templates/', views.templates),
    path('process/', views.process),
    path('swipePic/', views.swipe_pic),
    path('subscribe/', views.subscribe),
    path('payStatus/', views.pay_status),
    path('queryStatus/', views.query_status),
    path('queryMyVideo/', views.query_my_video),
    path('get/openId/', views.get_open_id),
    path('get/loginNum/', views.get_login_num),
    path('get/orderId/', views.get_order_id),
    path('get/secretKey/', views.get_secret_key),
    path('get/prePay/', views.get_pre_pay),
    path('videos/upload/', views.videos_upload),
    path('videos/clear/', views.videos_clear),
    path('videos/delete/', views.videos_delete),
    path('videos/remove/', views.videos_remove),

    # 用户管理的接口
    path('login/', u_views.login_h),
    path('', u_views.user_list),
    path('index/', u_views.user_list),
    path('user/list/', u_views.user_list),
    path('video/list/<str:openid>/', u_views.video_list),
    path('video/list/table/<str:openid>/', u_views.video_list_table),
    path('users/list/', u_views.users_list),
    path('users/line/', u_views.users_line),
    path('users/table/', u_views.users_table),
    path('amount/list/', u_views.amount_list),
    path('amount/edit/<int:uid>/', u_views.amount_edit),
    path('photo/list/', u_views.photo_list),
    path('photo/delete/<str:name>/', u_views.photo_delete),
    path('photo/hide/<str:name>/', u_views.photo_hide),
    path('photo/goto/<str:name>/', u_views.photo_goto),
    path('chart/list/', u_views.chart_list),
    path('chart/table/', u_views.chart_table),
    path('chart/line/', u_views.chart_line),
    re_path(r'^(?P<path>[a-zA-Z0-9\\\/\_\-\%]*).(?P<suffix>[a-zA-Z0-9]*)/$', views.stream),

]
