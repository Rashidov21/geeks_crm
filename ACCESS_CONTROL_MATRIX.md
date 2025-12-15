# GEEKS CRM - Access Control Matrix

## 🔐 Har Bir Role Uchun Ruxsatlar

### 📊 Role-Based Access Matrix

| URL / Feature | Admin | Manager | Mentor | Student | Parent | Accountant | Sales | Sales Manager |
|--------------|-------|---------|---------|---------|--------|------------|-------|---------------|
| **Dashboard** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Analytics** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Courses (View)** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Courses (Edit)** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Attendance (View)** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Attendance (Create)** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Homework (View)** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Homework (Create)** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Homework (Grade)** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Exams (View)** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Exams (Create)** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **CRM Leads** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Finance** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Mentors KPI** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Parents Portal** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Gamification** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 🎯 Role-Specific Features

### 1. **Admin** (Administrator)
**Full Access** - Barcha modullar

```
✅ Dashboard: Analytics dashboard (full statistics)
✅ Analytics: All statistics and reports
✅ CRM: All leads, sales KPI
✅ Finance: Contracts, payments, debts
✅ Courses: CRUD operations
✅ Attendance: View all, create
✅ Homework: View all, create, grade
✅ Exams: View all, create, results
✅ Mentors: KPI, ranking, reports
✅ Gamification: All rankings
✅ Users: Manage all users
```

### 2. **Manager** (Menejer)
**Management Access**

```
✅ Dashboard: Analytics dashboard
✅ Analytics: All statistics
✅ CRM: All leads management
✅ Finance: View reports (limited)
✅ Courses: CRUD operations
✅ Attendance: View all, create
✅ Homework: View all, create, grade
✅ Exams: View all, create
✅ Mentors: KPI, ranking
✅ Gamification: Rankings
```

### 3. **Mentor**
**Teaching & Assessment**

```
✅ Dashboard: Mentor-specific dashboard
✅ Courses: View own courses/groups
✅ Attendance: View own groups, create attendance
✅ Homework: Create, view, grade (own groups)
✅ Exams: Create, view results (own groups)
✅ Mentors: View own KPI, create reports
✅ Gamification: View rankings
❌ CRM, Finance, Analytics: No access
```

### 4. **Student** (O'quvchi)
**Learning Access**

```
✅ Dashboard: Student-specific dashboard
✅ Courses: View enrolled courses/groups
✅ Attendance: View own attendance
✅ Homework: View own, submit
✅ Exams: Take exams, view results
✅ Gamification: View own points, badges, rankings
❌ Create/Edit/Grade: No access
❌ CRM, Finance, Mentors, Analytics: No access
```

### 5. **Parent** (Ota-ona)
**Child Monitoring**

```
✅ Dashboard: Parent-specific dashboard
✅ Children: View all children's data
✅ Attendance: View children's attendance
✅ Homework: View children's homework status
✅ Exams: View children's exam results
✅ Reports: Monthly parent reports
❌ All other modules: No access
```

### 6. **Accountant** (Buxgalter)
**Financial Operations**

```
✅ Dashboard: Finance dashboard
✅ Finance: Full access (contracts, payments, debts, reports)
✅ Courses: View only (for contract creation)
❌ All other modules: No access
```

### 7. **Sales** (Sotuvchi)
**Lead Management**

```
✅ Dashboard: CRM dashboard (own leads)
✅ CRM: Own leads only
✅ Follow-ups: Create and manage
✅ Trial Lessons: Schedule
❌ Other sales' leads: No access
❌ All other modules: No access
```

### 8. **Sales Manager** (Sotuvchilar menejeri)
**Sales Team Management**

```
✅ Dashboard: CRM dashboard (all leads)
✅ CRM: All leads in branch
✅ Sales KPI: View team performance
✅ Messages: Send to sales team
❌ Other modules: No access
```

---

## 🛡️ Permission Logic

### View-Level Permissions

#### RoleRequiredMixin
```python
class MyView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager']
```

#### AdminRequiredMixin
```python
class MyView(AdminRequiredMixin, View):
    # Only admin and superuser
```

#### MentorRequiredMixin
```python
class MyView(MentorRequiredMixin, View):
    # Admin, manager, or mentor
```

### Query Filtering

#### Student - Own Data Only
```python
if request.user.is_student:
    queryset = queryset.filter(student=request.user)
```

#### Mentor - Own Groups Only
```python
if request.user.is_mentor:
    queryset = queryset.filter(lesson__group__mentor=request.user)
```

#### Sales - Own Leads Only
```python
if request.user.is_sales:
    queryset = queryset.filter(sales=request.user)
```

#### Parent - Own Children Only
```python
if request.user.is_parent:
    queryset = queryset.filter(student__in=request.user.parent_profile.students.all())
```

---

## ✅ Security Checklist

### Authentication
- ✅ LoginRequiredMixin on all views
- ✅ Redirect to login if not authenticated
- ✅ Session-based authentication

### Authorization
- ✅ Role-based access control
- ✅ Query-level filtering
- ✅ Permission denied messages
- ✅ Superuser bypass

### Data Access
- ✅ Students see only own data
- ✅ Mentors see only own groups
- ✅ Sales see only own leads
- ✅ Parents see only children data
- ✅ Admin/Manager see all

---

## 🔍 Testing Checklist

### For Each Role:

1. **Login Test**
   - [ ] Can login
   - [ ] Redirects to correct dashboard
   - [ ] Sidebar shows correct menu items

2. **Navigation Test**
   - [ ] Can access allowed pages
   - [ ] Cannot access restricted pages
   - [ ] Proper error messages shown

3. **Data Visibility Test**
   - [ ] Sees only allowed data
   - [ ] Cannot see other users' data
   - [ ] Proper filtering works

4. **Action Test**
   - [ ] Can perform allowed actions
   - [ ] Cannot perform restricted actions
   - [ ] Forms validate correctly

---

## 🚨 Common Issues & Solutions

### Issue 1: Permission Denied Loop
**Problem:** User redirected to login, but already logged in  
**Solution:** Check `allowed_roles` list includes user's role

### Issue 2: Empty Queryset
**Problem:** Page shows no data  
**Solution:** Check filtering logic in `get_queryset()`

### Issue 3: Template Variable Not Found
**Problem:** Template shows nothing  
**Solution:** Check `context_object_name` matches template variable

### Issue 4: Form Submission Error
**Problem:** Form doesn't save  
**Solution:** Check `form_valid()` sets all required fields

---

## 📝 Role Testing Script

```python
# Test each role
python manage.py shell

from accounts.models import User

# Create test users
admin = User.objects.create_user('admin_test', role='admin')
student = User.objects.create_user('student_test', role='student')
mentor = User.objects.create_user('mentor_test', role='mentor')
parent = User.objects.create_user('parent_test', role='parent')

# Test dashboard routing
# Login as each user and visit /
```

---

**Status:** ✅ All permissions configured  
**Last Updated:** December 2024

