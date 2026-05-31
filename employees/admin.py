from django.contrib import admin
from .models import Employee, Attendance, WorkSettings, Shift, Payroll, Promotion, Request

admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(WorkSettings)
admin.site.register(Shift)
admin.site.register(Payroll)
admin.site.register(Promotion)
admin.site.register(Request)