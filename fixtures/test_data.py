"""
Test ma'lumotlarni yaratish skripti
python manage.py shell < fixtures/test_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geeks_crm.settings')
django.setup()

from django.utils import timezone
from datetime import datetime, timedelta, time
from decimal import Decimal
import random

from accounts.models import User, Branch
from courses.models import Course, Module, Topic, Room, Group, Lesson, StudentProgress
from attendance.models import Attendance, AttendanceStatistics
from crm.models import LeadStatus, Lead, FollowUp, TrialLesson, SalesProfile
from homework.models import Homework, HomeworkGrade
from exams.models import Exam, ExamResult
from gamification.models import Badge, StudentBadge, PointTransaction
from finance.models import Contract, Payment

print("Test ma'lumotlar yaratish boshlandi...")

# ============ BRANCHES ============
branches_data = [
    {'name': 'Chilonzor filiali', 'address': 'Chilonzor 9, Toshkent', 'phone': '+998901234567'},
    {'name': 'Yunusobod filiali', 'address': 'Yunusobod 7, Toshkent', 'phone': '+998901234568'},
]

branches = []
for data in branches_data:
    branch, created = Branch.objects.get_or_create(name=data['name'], defaults=data)
    branches.append(branch)
    if created:
        print(f"  ✓ Filial yaratildi: {branch.name}")

# ============ USERS ============
# Admin
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@geeks.uz',
        'first_name': 'Admin',
        'last_name': 'Adminov',
        'role': 'admin',
        'phone': '+998900000001',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    admin.set_password('admin123')
    admin.save()
    print("  ✓ Admin yaratildi: admin / admin123")

# Manager
manager, created = User.objects.get_or_create(
    username='manager',
    defaults={
        'email': 'manager@geeks.uz',
        'first_name': 'Sardor',
        'last_name': 'Karimov',
        'role': 'manager',
        'phone': '+998900000002',
    }
)
if created:
    manager.set_password('manager123')
    manager.save()
    print("  ✓ Manager yaratildi: manager / manager123")

# Sales Manager
sales_manager, created = User.objects.get_or_create(
    username='sales_manager',
    defaults={
        'email': 'sales_manager@geeks.uz',
        'first_name': 'Dilshod',
        'last_name': 'Rahimov',
        'role': 'sales_manager',
        'phone': '+998900000003',
    }
)
if created:
    sales_manager.set_password('sales123')
    sales_manager.save()
    SalesProfile.objects.get_or_create(user=sales_manager, defaults={'branch': branches[0]})
    print("  ✓ Sales Manager yaratildi: sales_manager / sales123")

# Sales users
sales_names = [
    ('Aziz', 'Toshmatov', 'aziz'),
    ('Nodira', 'Karimova', 'nodira'),
    ('Jamshid', 'Aliyev', 'jamshid'),
]
sales_users = []
for first, last, username in sales_names:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@geeks.uz',
            'first_name': first,
            'last_name': last,
            'role': 'sales',
            'phone': f'+99890{random.randint(1000000, 9999999)}',
        }
    )
    if created:
        user.set_password('sales123')
        user.save()
        SalesProfile.objects.get_or_create(user=user, defaults={'branch': random.choice(branches)})
        print(f"  ✓ Sales yaratildi: {username} / sales123")
    sales_users.append(user)

# Mentors
mentor_names = [
    ('Rashidov', 'Abdurahmon', 'rashidov', 'Web Full Stack'),
    ('Alimov', 'Bekzod', 'bekzod', 'Python Backend'),
    ('Karimova', 'Nilufar', 'nilufar', 'Frontend Development'),
    ('Toshmatov', 'Ulugbek', 'ulugbek', 'Mobile Development'),
]
mentors = []
for last, first, username, specialty in mentor_names:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@geeks.uz',
            'first_name': first,
            'last_name': last,
            'role': 'mentor',
            'phone': f'+99890{random.randint(1000000, 9999999)}',
        }
    )
    if created:
        user.set_password('mentor123')
        user.save()
        print(f"  ✓ Mentor yaratildi: {username} / mentor123")
    mentors.append(user)

# Students
student_names = [
    'Ayubxon', 'Erkinjonova Gulzira', 'Hamidov Abubakr', 'Isakjonov Muhammadyusuf',
    'Islomov Oyatillo', 'Muhammadyusuf', 'Nizomov Abdulaziz', 'Shukrullayeva Sabina',
    'Sirojiddinov Abdulboriy', 'Tursunov Ahmadillo', 'Usmonaliyeva Mohinur',
    'Karimov Jasur', 'Rahimova Madina', 'Toshmatov Sardor', 'Aliyeva Zarina',
]
students = []
for i, name in enumerate(student_names):
    parts = name.split()
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    username = f'student{i+1}'
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@geeks.uz',
            'first_name': first_name,
            'last_name': last_name,
            'role': 'student',
            'phone': f'+99890{544+i:03d}{20+i:02d}{50+i:02d}',
        }
    )
    if created:
        user.set_password('student123')
        user.save()
    students.append(user)

print(f"  ✓ {len(students)} ta talaba yaratildi")

# Parents
parent, created = User.objects.get_or_create(
    username='parent1',
    defaults={
        'email': 'parent1@geeks.uz',
        'first_name': 'Karim',
        'last_name': 'Karimov',
        'role': 'parent',
        'phone': '+998901112233',
    }
)
if created:
    parent.set_password('parent123')
    parent.save()
    print("  ✓ Parent yaratildi: parent1 / parent123")

# ============ ROOMS ============
rooms = []
for branch in branches:
    for i in range(1, 4):
        room, created = Room.objects.get_or_create(
            branch=branch,
            name=f'Xona {i}',
            defaults={'capacity': 20, 'is_active': True}
        )
        rooms.append(room)
        if created:
            print(f"  ✓ Xona yaratildi: {room}")

# ============ COURSES ============
courses_data = [
    {'name': 'Web Full Stack', 'description': 'Frontend va Backend dasturlash', 'duration_weeks': 24, 'price': Decimal('3000000')},
    {'name': 'Python Backend', 'description': 'Python va Django bilan backend', 'duration_weeks': 16, 'price': Decimal('2500000')},
    {'name': 'Frontend Development', 'description': 'React, Vue, Angular', 'duration_weeks': 12, 'price': Decimal('2000000')},
    {'name': 'Mobile Development', 'description': 'Flutter va React Native', 'duration_weeks': 16, 'price': Decimal('2800000')},
    {'name': 'Data Science', 'description': 'Python bilan data tahlil', 'duration_weeks': 20, 'price': Decimal('3500000')},
]

courses = []
for data in courses_data:
    course, created = Course.objects.get_or_create(
        name=data['name'],
        defaults={**data, 'branch': random.choice(branches), 'is_active': True}
    )
    courses.append(course)
    if created:
        print(f"  ✓ Kurs yaratildi: {course.name}")
        
        # Modules
        modules_names = ['Asoslar', 'O\'rta daraja', 'Ilg\'or mavzular', 'Amaliyot']
        for j, mod_name in enumerate(modules_names):
            module = Module.objects.create(
                course=course,
                name=f'{mod_name}',
                order=j+1
            )
            # Topics
            for k in range(1, 6):
                Topic.objects.create(
                    module=module,
                    name=f'{mod_name} - Mavzu {k}',
                    order=k,
                    duration_minutes=90
                )

# ============ GROUPS ============
groups_data = [
    {'name': 'Computer Science 14:00 (s,p,sh)', 'course': courses[0], 'mentor': mentors[0], 'start_time': time(14, 0), 'end_time': time(15, 30), 'schedule_type': 'odd'},
    {'name': 'Python Backend 10:00', 'course': courses[1], 'mentor': mentors[1], 'start_time': time(10, 0), 'end_time': time(11, 30), 'schedule_type': 'even'},
    {'name': 'Frontend 16:00', 'course': courses[2], 'mentor': mentors[2], 'start_time': time(16, 0), 'end_time': time(17, 30), 'schedule_type': 'odd'},
    {'name': 'Mobile Dev 18:00', 'course': courses[3], 'mentor': mentors[3], 'start_time': time(18, 0), 'end_time': time(19, 30), 'schedule_type': 'daily'},
]

groups = []
for data in groups_data:
    group, created = Group.objects.get_or_create(
        name=data['name'],
        defaults={
            'course': data['course'],
            'mentor': data['mentor'],
            'room': random.choice(rooms),
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'schedule_type': data['schedule_type'],
            'capacity': 15,
            'is_active': True,
        }
    )
    groups.append(group)
    if created:
        print(f"  ✓ Guruh yaratildi: {group.name}")

# Assign students to groups
for i, student in enumerate(students):
    group = groups[i % len(groups)]
    group.students.add(student)

print(f"  ✓ Talabalar guruhlarga biriktirildi")

# ============ LESSONS ============
today = timezone.now().date()
for group in groups:
    # Oxirgi 30 kun uchun darslar
    for i in range(30):
        lesson_date = today - timedelta(days=i)
        # Dars kunlarini tekshirish
        weekday = lesson_date.weekday()
        if group.schedule_type == 'odd' and weekday in [1, 3, 5]:  # Seshanba, Payshanba, Shanba
            pass
        elif group.schedule_type == 'even' and weekday in [0, 2, 4]:  # Dushanba, Chorshanba, Juma
            pass
        elif group.schedule_type == 'daily':
            pass
        else:
            continue
            
        Lesson.objects.get_or_create(
            group=group,
            date=lesson_date,
            defaults={
                'start_time': group.start_time,
                'end_time': group.end_time,
                'title': f'{group.name} - {lesson_date}'
            }
        )

print(f"  ✓ Darslar yaratildi")

# ============ ATTENDANCE ============
lessons = Lesson.objects.all()
for lesson in lessons:
    for student in lesson.group.students.all():
        status = random.choices(['present', 'late', 'absent'], weights=[75, 15, 10])[0]
        Attendance.objects.get_or_create(
            lesson=lesson,
            student=student,
            defaults={'status': status}
        )

print(f"  ✓ Davomat yozuvlari yaratildi")

# ============ LEAD STATUSES ============
statuses_data = [
    {'code': 'new', 'name': 'Yangi', 'color': '#3B82F6', 'order': 1},
    {'code': 'contacted', 'name': 'Bog\'lanildi', 'color': '#8B5CF6', 'order': 2},
    {'code': 'interested', 'name': 'Qiziqdi', 'color': '#F59E0B', 'order': 3},
    {'code': 'trial_registered', 'name': 'Sinovga yozildi', 'color': '#06B6D4', 'order': 4},
    {'code': 'trial_attended', 'name': 'Sinovga keldi', 'color': '#10B981', 'order': 5},
    {'code': 'enrolled', 'name': 'Yozildi', 'color': '#22C55E', 'order': 6},
    {'code': 'lost', 'name': 'Yo\'qotildi', 'color': '#EF4444', 'order': 7},
]

lead_statuses = []
for data in statuses_data:
    status, created = LeadStatus.objects.get_or_create(
        code=data['code'],
        defaults=data
    )
    lead_statuses.append(status)
    if created:
        print(f"  ✓ Lead status yaratildi: {status.name}")

# ============ LEADS ============
lead_names = [
    ('Alisher Karimov', '+998901234567', 'instagram'),
    ('Malika Rahimova', '+998912345678', 'telegram'),
    ('Jasur Toshmatov', '+998933456789', 'website'),
    ('Zarina Aliyeva', '+998944567890', 'instagram'),
    ('Bobur Saidov', '+998955678901', 'referral'),
    ('Dilnoza Karimova', '+998966789012', 'telegram'),
    ('Shoxrux Rahimov', '+998977890123', 'instagram'),
    ('Madina Tosheva', '+998988901234', 'website'),
    ('Akmal Alimov', '+998909012345', 'google_sheets'),
    ('Nilufar Saidova', '+998910123456', 'telegram'),
    ('Sardor Kamolov', '+998921234567', 'instagram'),
    ('Gulnora Rahimova', '+998932345678', 'referral'),
]

leads = []
for name, phone, source in lead_names:
    status = random.choice(lead_statuses[:5])  # First 5 statuses
    lead, created = Lead.objects.get_or_create(
        phone=phone,
        defaults={
            'name': name,
            'source': source,
            'status': status,
            'branch': random.choice(branches),
            'interested_course': random.choice(courses),
            'assigned_sales': random.choice(sales_users) if random.random() > 0.3 else None,
            'notes': f'{name} - {source} orqali keldi',
        }
    )
    leads.append(lead)
    if created:
        print(f"  ✓ Lead yaratildi: {name}")

# ============ FOLLOW-UPS ============
for lead in leads:
    if lead.assigned_sales:
        for i in range(random.randint(1, 3)):
            due_date = timezone.now() + timedelta(days=random.randint(-5, 5))
            FollowUp.objects.create(
                lead=lead,
                sales=lead.assigned_sales,
                due_date=due_date,
                notes=f'{lead.name} bilan bog\'lanish',
                completed=random.random() > 0.5,
            )

print(f"  ✓ Follow-uplar yaratildi")

# ============ HOMEWORK ============
lessons_list = list(Lesson.objects.all()[:50])
for lesson in lessons_list:
    for student in lesson.group.students.all()[:random.randint(2, 5)]:
        deadline = timezone.now() + timedelta(days=random.randint(-10, 10))
        hw, created = Homework.objects.get_or_create(
            lesson=lesson,
            student=student,
            defaults={
                'title': f'{lesson.group.course.name} - Vazifa',
                'description': f'Bu {lesson.group.course.name} kursi uchun vazifa',
                'deadline': deadline,
                'is_submitted': random.random() > 0.3,
                'submitted_at': timezone.now() - timedelta(days=random.randint(0, 5)) if random.random() > 0.3 else None,
            }
        )
        if created and hw.is_submitted and random.random() > 0.4:
            HomeworkGrade.objects.create(
                homework=hw,
                mentor=lesson.group.mentor,
                grade=random.randint(60, 100),
                comment='Yaxshi bajarilgan'
            )

print(f"  ✓ Vazifalar yaratildi")

# ============ EXAMS ============
for group in groups:
    for i in range(2):
        exam_date = timezone.now() + timedelta(days=random.randint(-20, 20))
        exam, created = Exam.objects.get_or_create(
            course=group.course,
            group=group,
            title=f'{group.course.name} - Imtihon {i+1}',
            defaults={
                'description': f'{i+1}-oraliq imtihon',
                'date': exam_date,
                'duration_minutes': 90,
                'max_score': 100,
            }
        )
        if created and exam_date.date() < today:
            for student in group.students.all():
                score = random.randint(50, 100)
                ExamResult.objects.create(
                    exam=exam,
                    student=student,
                    score=score,
                    percentage=(score / 100) * 100,
                    is_passed=score >= 60
                )

print(f"  ✓ Imtihonlar yaratildi")

# ============ BADGES ============
badges_data = [
    {'name': 'Eng faol', 'badge_type': 'top_student', 'description': 'Eng faol talaba', 'icon': '⭐', 'points_required': 100},
    {'name': 'Vazifa ustasi', 'badge_type': 'homework_master', 'description': 'Barcha vazifalarni bajargan', 'icon': '📚', 'points_required': 200},
    {'name': 'Davomat yulduzi', 'badge_type': 'perfect_attendance', 'description': '100% davomat', 'icon': '📅', 'points_required': 150},
    {'name': 'Imtihon chempioni', 'badge_type': 'exam_champion', 'description': 'Imtihonlarda 90+ ball', 'icon': '🏆', 'points_required': 300},
]

badges = []
for data in badges_data:
    badge, created = Badge.objects.get_or_create(
        badge_type=data['badge_type'],
        defaults=data
    )
    badges.append(badge)
    if created:
        print(f"  ✓ Badge yaratildi: {badge.name}")

# Assign badges to students
for student in students[:5]:
    badge = random.choice(badges)
    StudentBadge.objects.get_or_create(
        student=student,
        badge=badge
    )

# Points
for student in students:
    for _ in range(random.randint(1, 5)):
        PointTransaction.objects.create(
            student=student,
            points=random.randint(5, 50),
            point_type=random.choice(['attendance_present', 'homework_on_time', 'manual']),
            description=random.choice(['Darsga keldi', 'Vazifa bajargan', 'Faollik']),
        )

print(f"  ✓ Gamification ma'lumotlari yaratildi")

# ============ CONTRACTS & PAYMENTS ============
contract_num = 1
for student in students[:10]:
    group = student.student_groups.first()
    if group:
        contract, created = Contract.objects.get_or_create(
            student=student,
            course=group.course,
            defaults={
                'contract_number': f'GC-2025-{contract_num:04d}',
                'group': group,
                'total_amount': group.course.price,
                'discount_amount': Decimal('0'),
                'status': 'active',
                'start_date': today - timedelta(days=30),
                'end_date': today + timedelta(days=180),
            }
        )
        contract_num += 1
        
        if created:
            # Payment
            Payment.objects.create(
                payment_number=f'PAY-2025-{contract_num:04d}',
                contract=contract,
                amount=Decimal(random.randint(500000, int(group.course.price))),
                payment_method='cash',
                status='completed',
                paid_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                created_by=manager,
            )

print(f"  ✓ Shartnomalar va to'lovlar yaratildi")

print("\n" + "="*50)
print("✅ Test ma'lumotlar muvaffaqiyatli yaratildi!")
print("="*50)
print("\nLogin ma'lumotlari:")
print("  Admin: admin / admin123")
print("  Manager: manager / manager123")
print("  Sales Manager: sales_manager / sales123")
print("  Sales: aziz, nodira, jamshid / sales123")
print("  Mentors: rashidov, bekzod, nilufar, ulugbek / mentor123")
print("  Students: student1-15 / student123")
print("  Parent: parent1 / parent123")

