from django.db import models
from django.contrib.auth.models import User

class Shift(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period = models.IntegerField(default=15)

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    department = models.CharField(max_length=50)
    position = models.CharField(max_length=50)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'حاضر'),
        ('late', 'متأخر'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.employee.name} - {self.date}"

class WorkSettings(models.Model):
    work_start = models.TimeField(default='09:00')
    work_end = models.TimeField(default='17:00')
    grace_period = models.IntegerField(default=15)

    class Meta:
        verbose_name = 'إعدادات الدوام'

    def __str__(self):
        return f"الدوام: {self.work_start} - {self.work_end}"

class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    food_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    absence_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employee', 'month', 'year']

    def __str__(self):
        return f"{self.employee.name} - {self.month}/{self.year}"

class Promotion(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    old_position = models.CharField(max_length=50)
    new_position = models.CharField(max_length=50)
    old_salary = models.DecimalField(max_digits=10, decimal_places=2)
    new_salary = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.name} - {self.date}"

class Request(models.Model):
    REQUEST_TYPES = [
        ('vacation', 'إجازة سنوية'),
        ('sick', 'إجازة مرضية'),
        ('advance', 'سلفة'),
        ('certificate', 'شهادة عمل'),
        ('attendance', 'تعديل حضور'),
        ('other', 'أخرى'),
    ]
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق'),
        ('rejected', 'مرفوض'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    description = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    manager_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.name} - {self.get_request_type_display()}"