"""govt_env_protection_eval_dj URL Configuration

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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import my_login.views as v1
import task_manager.views as v2
import DEA.views as v3
import BHT_ARIMA_RUNTIME.views as v4

urlpatterns = [
    path('admin/', admin.site.urls),
    # my login
    path('my_login/view', v1.view_login),
    path('my_login/add', v1.add_login),
    path('my_login/delete', v1.delete_login),
    path('my_login/register', v1.view_register),
    path('my_login/register/add', v1.add_register),
    path('my_login/confirm', v1.add_user),
    # task manager
    path('main', v2.view_main),
    path('task/list', v2.view_tasks),
    path('task/delete', v2.delete_task),
    path('task/view_add', v2.view_add_task),
    path('task/add', v2.add_task),
    # DEA
    path('task/add-1', v3.view_set_variables),
    path('dea/set-variable', v3.set_variable),
    path('task/add-2', v3.view_dea_results),
    path('dea/draw-efficients', v3.draw_efficients),
    path('dea/download-efficients', v3.download_efficients),
    # BHT-ARIMA
    path('task/add-3', v4.view_bht_arima),
    path('bht-arima/add', v4.add_bht_arima),
    path('task/add-4', v4.view_prediction),
    path('bht-arima/download', v4.download_prediction),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
