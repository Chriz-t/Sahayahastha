from django.contrib import admin
from django.urls import path, include
from .views import get_districts,get_camps,get_tasks
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('',views.home,name="home"),
    path('home',views.home,name="home"),
    path('volunteerlogin',views.volunteerlogin,name="volunteerlogin"),
    path('volunteer',views.volunteer,name="volunteer"),
    path('volunteerreg',views.volunteerreg,name="volunteerreg"),
    path("get-districts/", get_districts, name="get-districts"),
    path('get-camps/', views.get_camps, name='get-camps'),
    path('get-tasks/', views.get_tasks, name='get-tasks'),
    path('update-task-status/', views.update_task_status, name='update_task_status'),
    path('get-task-progress/', views.get_task_progress, name='get_task_progress'),
    path('set-task-progress/', views.set_task_progress, name='set_task_progress'),
    path('addtask',views.addtask,name='addtask'),
    path('get-volunteers/',views.get_volunteers,name='get-volunteers'),
    path('insert-task/',views.insert_task,name='insert-task'),
    path('coordinator',views.coordinator,name='coordinator'),
    path('insertcoord/',views.insertcoord,name='insertcoord'),# remove this
    path('coordinatorlogin',views.coordinatorlogin,name='coordinatorlogin'),
    path('loadcoordinator/',views.loadcoordinator,name='loadcoordinator'),
    path('campinventory',views.campinventory,name='campinventory'),
    path('get-inventory/',views.get_inventory,name="get-inventory"),
    path('add-item/',views.add_item,name="add-item"),
    path('update-item/',views.update_item,name="update-item"),
    path('delete-item/',views.delete_item,name="delete-item"),
    path('people',views.people,name='people'),
    path('camprequest',views.camprequest,name='camprequest'),
    path('addrequest',views.addrequest,name='addrequest'),
    path('insert-request/',views.insert_request,name='insert-request'),
    path('get-requests/',views.get_requests,name='get-requests'),
    path('delete-request/',views.delete_request,name="delete-request"),
    path('update-request/',views.update_request,name="update-request"),
    path('validate-coordinator/',views.validate_coordinator,name="validate-coordinator"),
    path('append-reply/',views.append_reply,name="append-reply"),
    path('get-all-requests/',views.get_all_requests,name='get-all-requests'),
    path('donor',views.donor,name='donor'), 
    path('validate-volunteer/',views.validate_volunteer,name="validate-volunteer"),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
