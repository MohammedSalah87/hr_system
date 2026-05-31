from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('add/', views.employee_add, name='employee_add'),
    path('edit/<int:pk>/', views.employee_edit, name='employee_edit'),
    path('delete/<int:pk>/', views.employee_delete, name='employee_delete'),
    path('qr/<int:pk>/', views.generate_qr, name='generate_qr'),
    path('attendance/<str:token>/', views.mark_attendance, name='mark_attendance'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('settings/', views.work_settings, name='work_settings'),
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/delete/<int:pk>/', views.shift_delete, name='shift_delete'),
    path('payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/generate/', views.payroll_generate, name='payroll_generate'),
    path('payroll/<int:pk>/<int:month>/<int:year>/pdf/', views.payroll_pdf, name='payroll_pdf'),
    path('employee/<int:pk>/promotions/', views.promotion_list, name='promotion_list'),
    path('employee/<int:pk>/promotions/add/', views.promotion_add, name='promotion_add'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/add/', views.request_add, name='request_add'),
    path('requests/<int:pk>/update/', views.request_update, name='request_update'),
path('employee/<int:pk>/create-account/', views.create_employee_account, name='create_employee_account'),
]