from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Employee, Attendance, WorkSettings, Shift
from .forms import EmployeeForm
import qrcode
import io
import base64
import jwt
import datetime

@login_required
def dashboard(request):
    total = Employee.objects.count()
    active = Employee.objects.filter(is_active=True).count()
    inactive = Employee.objects.filter(is_active=False).count()
    departments = Employee.objects.values('department').distinct().count()
    employees = Employee.objects.order_by('-id')[:5]
    context = {
        'total': total,
        'active': active,
        'inactive': inactive,
        'departments': departments,
        'employees': employees,
    }
    return render(request, 'employees/dashboard.html', context)

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employees/employee_list.html', {'employees': employees})

@login_required
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'إضافة موظف'})

@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'تعديل موظف'})

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})

@login_required
def generate_qr(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    payload = {
        'employee_id': pk,
        'minute': datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
    }
    from django.conf import settings
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    url = request.build_absolute_uri(f'/attendance/{token}/')
    qr = qrcode.make(url)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    qr_image = base64.b64encode(buffer.getvalue()).decode()
    return render(request, 'employees/qr_code.html', {
        'employee': employee,
        'qr_image': qr_image
    })

def mark_attendance(request, token):
    try:
        from django.conf import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        token_time = datetime.datetime.strptime(payload['minute'], '%Y-%m-%d-%H-%M')
        now = datetime.datetime.now()
        diff = (now - token_time).total_seconds()

        if diff > 90:
            return render(request, 'employees/attendance_success.html', {
                'message': '❌ انتهت صلاحية الـ QR — اطلب كود جديد',
                'employee': None
            })

        employee = get_object_or_404(Employee, pk=payload['employee_id'])
        today = datetime.date.today()

        if employee.shift:
            work_start_time = employee.shift.start_time
            grace = employee.shift.grace_period
        else:
            work_settings_obj = WorkSettings.objects.first()
            grace = work_settings_obj.grace_period if work_settings_obj else 15
            work_start_time = work_settings_obj.work_start if work_settings_obj else datetime.time(9, 0)

        work_start = (datetime.datetime.combine(today, work_start_time) + datetime.timedelta(minutes=grace)).time()

        attendance = Attendance.objects.filter(employee=employee, date=today).first()

        if not attendance:
            now_time = now.time()
            status = 'late' if now_time > work_start else 'present'
            Attendance.objects.create(employee=employee, time_in=now_time, status=status)
            message = f'✅ تم تسجيل دخول {employee.name}'
        elif not attendance.time_out:
            time_out = now.time()
            time_in = datetime.datetime.combine(today, attendance.time_in)
            time_out_dt = datetime.datetime.combine(today, time_out)
            work_hours = round((time_out_dt - time_in).total_seconds() / 3600, 2)
            attendance.time_out = time_out
            attendance.work_hours = work_hours
            attendance.save()
            message = f'✅ تم تسجيل خروج {employee.name} — ساعات العمل: {work_hours}'
        else:
            message = f'⚠️ تم تسجيل دخول وخروج {employee.name} مسبقاً اليوم'

        return render(request, 'employees/attendance_success.html', {
            'employee': employee,
            'message': message
        })

    except Exception as e:
        return render(request, 'employees/attendance_success.html', {
            'message': '❌ QR غير صالح',
            'employee': None
        })

@login_required
def attendance_list(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.date.fromisoformat(date_str)
        except:
            selected_date = datetime.date.today()
    else:
        selected_date = datetime.date.today()

    attendances = Attendance.objects.filter(date=selected_date).select_related('employee')
    employees = Employee.objects.filter(is_active=True)
    present_ids = attendances.values_list('employee_id', flat=True)
    absent = employees.exclude(id__in=present_ids)

    return render(request, 'employees/attendance_list.html', {
        'attendances': attendances,
        'absent': absent,
        'today': selected_date
    })

@login_required
def work_settings(request):
    settings_obj = WorkSettings.objects.first()
    if not settings_obj:
        settings_obj = WorkSettings.objects.create()
    if request.method == 'POST':
        settings_obj.work_start = request.POST.get('work_start')
        settings_obj.work_end = request.POST.get('work_end')
        settings_obj.grace_period = request.POST.get('grace_period')
        settings_obj.save()
        return redirect('work_settings')
    return render(request, 'employees/work_settings.html', {'settings': settings_obj})

@login_required
def shift_list(request):
    if request.method == 'POST':
        Shift.objects.create(
            name=request.POST.get('name'),
            start_time=request.POST.get('start_time'),
            end_time=request.POST.get('end_time'),
            grace_period=request.POST.get('grace_period')
        )
        return redirect('shift_list')
    shifts = Shift.objects.all()
    return render(request, 'employees/shifts.html', {'shifts': shifts})

@login_required
def shift_delete(request, pk):
    shift = get_object_or_404(Shift, pk=pk)
    shift.delete()
    return redirect('shift_list')
from .models import Attendance, WorkSettings, Shift, Payroll

@login_required
def payroll_list(request):
    month = int(request.GET.get('month', datetime.date.today().month))
    year = int(request.GET.get('year', datetime.date.today().year))
    payrolls = Payroll.objects.filter(month=month, year=year).select_related('employee')
    return render(request, 'employees/payroll_list.html', {
        'payrolls': payrolls,
        'month': month,
        'year': year
    })

@login_required
def payroll_generate(request):
    month = int(request.POST.get('month', datetime.date.today().month))
    year = int(request.POST.get('year', datetime.date.today().year))
    employees = Employee.objects.filter(is_active=True)

    for employee in employees:
        # حساب أيام الغياب
        work_days = Attendance.objects.filter(
            employee=employee,
            date__month=month,
            date__year=year
        ).count()

        import calendar
        total_days = calendar.monthrange(year, month)[1]
        absent_days = total_days - work_days

        # حساب الخصومات
        daily_salary = employee.salary / total_days
        absence_deduction = daily_salary * absent_days

        # حساب خصم التأخير
        late_days = Attendance.objects.filter(
            employee=employee,
            date__month=month,
            date__year=year,
            status='late'
        ).count()
        late_deduction = daily_salary * late_days * 1 / 4

        # صافي الراتب
        net_salary = employee.salary - absence_deduction - late_deduction

        Payroll.objects.update_or_create(
            employee=employee,
            month=month,
            year=year,
            defaults={
                'basic_salary': employee.salary,
                'absence_deduction': round(absence_deduction, 2),
                'late_deduction': round(late_deduction, 2),
                'net_salary': round(net_salary, 2)
            }
        )

    return redirect(f'/payroll/?month={month}&year={year}')

from .models import Attendance, WorkSettings, Shift, Payroll, Promotion

@login_required
def promotion_list(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    promotions = Promotion.objects.filter(employee=employee).order_by('-date')
    return render(request, 'employees/promotions.html', {
        'employee': employee,
        'promotions': promotions
    })

@login_required
def promotion_add(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        old_position = employee.position
        old_salary = employee.salary
        new_position = request.POST.get('new_position')
        new_salary = request.POST.get('new_salary')
        notes = request.POST.get('notes')

        Promotion.objects.create(
            employee=employee,
            date=request.POST.get('date'),
            old_position=old_position,
            old_salary=old_salary,
            new_position=new_position,
            new_salary=new_salary,
            notes=notes
        )

        # تحديث بيانات الموظف
        employee.position = new_position
        employee.salary = new_salary
        employee.save()

        return redirect('promotion_list', pk=pk)

    return render(request, 'employees/promotion_form.html', {'employee': employee})
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.http import HttpResponse

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

@login_required
def payroll_pdf(request, pk, month, year):
    employee = get_object_or_404(Employee, pk=pk)
    payroll = get_object_or_404(Payroll, employee=employee, month=month, year=year)

    # تسجيل خط عربي
    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Arabic.ttf')
    pdfmetrics.registerFont(TTFont('Arabic', font_path))

    def ar(text):
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="payroll_{month}_{year}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # العنوان
    p.setFont("Arabic", 20)
    p.drawCentredString(width/2, height-50, ar("كشف الراتب"))

    p.setFont("Arabic", 14)
    p.drawCentredString(width/2, height-80, ar(f"الشهر: {month}/{year}"))

    # خط فاصل
    p.setStrokeColor(colors.HexColor('#1e3a5f'))
    p.setLineWidth(2)
    p.line(50, height-100, width-50, height-100)

    # بيانات الموظف
    p.setFont("Arabic", 12)
    p.setFillColor(colors.HexColor('#1e3a5f'))
    p.drawRightString(width-50, height-130, ar("بيانات الموظف"))

    p.setFont("Arabic", 11)
    p.setFillColor(colors.black)
    p.drawRightString(width-50, height-155, ar(f"الاسم: {employee.name}"))
    p.drawRightString(width-50, height-175, ar(f"المنصب: {employee.position}"))
    p.drawRightString(width-50, height-195, ar(f"القسم: {employee.department}"))

    # جدول الراتب
    p.setFont("Arabic", 12)
    p.setFillColor(colors.HexColor('#1e3a5f'))
    p.drawRightString(width-50, height-230, ar("تفاصيل الراتب"))

    data = [
        [ar('المبلغ'), ar('البند')],
        [f"{payroll.basic_salary}", ar('الراتب الأساسي')],
        [f"-{payroll.absence_deduction}", ar('خصم الغياب')],
        [f"-{payroll.late_deduction}", ar('خصم التأخير')],
        [f"{payroll.net_salary}", ar('صافي الراتب')],
    ]

    table = Table(data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Arabic'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e8f5e9')),
        ('FONTNAME', (0,-1), (-1,-1), 'Arabic'),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))

    table.wrapOn(p, width, height)
    table.drawOn(p, 50, height-400)

    # التوقيع
    p.setFont("Arabic", 10)
    p.setFillColor(colors.grey)
    p.drawRightString(width-50, 50, ar(f"تم الإنشاء بواسطة نظام HR"))
    p.drawRightString(width-50, 35, ar(f"التاريخ: {datetime.date.today()}"))

    p.save()
    return response
from .models import Attendance, WorkSettings, Shift, Payroll, Promotion, Request
from django.contrib.auth.models import User

@login_required
def request_list(request):
    # المدير يشوف كل الطلبات
    if request.user.is_staff:
        requests = Request.objects.all().order_by('-created_at')
    else:
        # الموظف يشوف بس طلباته
        try:
            employee = Employee.objects.get(user=request.user)
            requests = Request.objects.filter(employee=employee).order_by('-created_at')
        except Employee.DoesNotExist:
            requests = Request.objects.none()

    return render(request, 'employees/request_list.html', {'requests': requests})

@login_required
def request_add(request):
    if request.method == 'POST':
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return redirect('dashboard')

        Request.objects.create(
            employee=employee,
            request_type=request.POST.get('request_type'),
            description=request.POST.get('description'),
            start_date=request.POST.get('start_date') or None,
            end_date=request.POST.get('end_date') or None,
        )
        return redirect('request_list')

    return render(request, 'employees/request_form.html')

@login_required
def request_update(request, pk):
    if not request.user.is_staff:
        return redirect('request_list')

    req = get_object_or_404(Request, pk=pk)
    if request.method == 'POST':
        req.status = request.POST.get('status')
        req.manager_note = request.POST.get('manager_note')
        req.save()
        return redirect('request_list')

    return render(request, 'employees/request_update.html', {'req': req})
@login_required
def create_employee_account(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            return render(request, 'employees/create_account.html', {
                'employee': employee,
                'error': 'اسم المستخدم موجود مسبقاً'
            })
        
        user = User.objects.create_user(username=username, password=password)
        employee.user = user
        employee.save()
        
        return redirect('employee_list')
    
    return render(request, 'employees/create_account.html', {'employee': employee})