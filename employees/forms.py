from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'email', 'phone', 'department', 'position', 'salary', 'hire_date', 'is_active', 'shift']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الموظف'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'القسم'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المنصب'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الراتب'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
        }