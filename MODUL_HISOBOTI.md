# GEEKS CRM - Modullar Holati va Hisob-Kitoblar Hisoboti

## Umumiy Ma'lumot

Loyiha Django 5.0.1 framework'ida qurilgan to'liq funksional LMS + CRM tizimi. Quyidagi modullar mavjud:

- **Accounts** (Foydalanuvchilar, Filiallar)
- **Courses** (Kurslar, Guruhlar, Darslar)
- **Attendance** (Davomat)
- **Homework** (Vazifalar)
- **Exams** (Imtihonlar)
- **Finance** (Moliya)
- **CRM** (Lead Management, Follow-ups)
- **Gamification** (Balllar, Badge'lar, Reytinglar)
- **Mentors** (Mentor KPI)
- **Parents** (Ota-onalar moduli)
- **Analytics** (Statistikalar)

---

## 1. MOLIYA MODULI (Finance)

### Model va Hisob-Kitoblar

#### Contract Model
- **Fayl**: `finance/models.py`
- **Asosiy hisob-kitoblar**:
  - `remaining_amount`: Qolgan to'lov miqdori = `total_amount - paid_amount - discount_amount`
  - `is_paid`: To'liq to'langanmi? (property)
  - `payment_percentage`: To'lov foizi = `(paid_amount / total_amount) * 100`
- **Avtomatik yaratish**: Shartnoma raqami avtomatik yaratiladi (signals orqali)

#### Payment Model
- **To'lov usullari**: Naqd, Karta, O'tkazma
- **Status**: Pending, Completed, Cancelled, Refunded
- **Hisob-kitoblar**: To'lov miqdorlari, statuslar

#### PaymentPlan Model
- **Hisob-kitoblar**:
  - `is_overdue`: Muddati o'tganmi? (property)
  - `days_overdue`: Qancha kun o'tgan (property)

#### Debt Model
- **Qarzlar tracking**: Muddati o'tgan to'lovlar
- **Priority**: Low, Medium, High, Urgent

#### FinancialReport Model
- **Hisobot turlari**: Kunlik, Haftalik, Oylik, Yillik
- **Statistikalar**: Revenue, Payments, Debts, Discounts

### View va Statistikalar

#### DashboardView (`finance/views.py:311`)
- **Umumiy statistika**:
  - `total_contracts`: Jami shartnomalar
  - `active_contracts`: Faol shartnomalar
  - `total_revenue`: Jami daromad (Sum(total_amount))
  - `total_paid`: Jami to'langan (Sum(paid_amount))
- **Bu oy**:
  - `contracts_this_month`: Bu oydagi shartnomalar
  - `revenue_this_month`: Bu oydagi daromad
  - `payments_this_month`: Bu oydagi to'lovlar (completed status)
- **Qarzlar**:
  - `total_debts`: Jami qarzlar (is_paid=False, Sum(amount))
  - `overdue_debts`: Muddati o'tgan qarzlar (due_date < today)
- **Oylik trend**: Oxirgi 6 oy uchun chart ma'lumotlari

#### ReportsView (`finance/views.py:400`)
- **Kurslar bo'yicha daromad**: Har bir kurs uchun revenue, paid, contracts
- **Oylik trend**: Oxirgi 12 oy uchun to'lovlar va shartnomalar statistikasi

### Celery Tasks

#### `create_payment_reminders` (`finance/tasks.py:16`)
- **Vazifa**: To'lov eslatmalarini avtomatik yaratish
- **Vaqt**: Har 24 soatda
- **Logic**: PaymentPlan uchun 3 kun, 1 kun, 0 kun oldin eslatmalar yaratadi

#### `check_overdue_payments` (`finance/tasks.py`)
- **Vazifa**: Overdue to'lovlarni tekshirish va Debt yaratish
- **Vaqt**: Har kuni

#### `generate_monthly_financial_report` (`finance/tasks.py`)
- **Vazifa**: Oylik moliya hisoboti generatsiya qilish
- **Vaqt**: Har oyning 1-kuni

### Signals
- Shartnoma yaratilganda to'lov rejasi avtomatik yaratiladi (`finance/signals.py`)
- To'lov yaratilganda PaymentHistory yaratiladi
- To'lov status o'zgarganda contract paid_amount yangilanadi

---

## 2. DARSLAR MODULI (Courses)

### Model va Hisob-Kitoblar

#### StudentProgress Model (`courses/models.py:267`)
- **Hisob-kitob**: `calculate_progress()`
  - `progress_percentage` = `(completed_topics.count() / total_topics) * 100`
  - Total topics: Kursdagi barcha topiclar soni
  - Completed: O'quvchi tomonidan yakunlangan topiclar

#### Group Model
- **Hisob-kitoblar**:
  - `enrolled_students_count`: Yozilgan o'quvchilar soni
  - `trial_students_count`: Trial o'quvchilar soni (Lead modelidan)
  - `total_students_count`: Jami o'quvchilar
  - `fill_percentage`: Guruh to'lish darajasi = `(total_students_count / capacity) * 100`

### View va Statistikalar

#### CourseListView (`courses/views.py:13`)
- **Statistikalar**:
  - `total_courses`: Jami kurslar
  - `active_courses`: Faol kurslar

#### LessonListView (`courses/views.py:499`)
- **Filtering**: Studentlar uchun o'z guruhlari, Mentorlar uchun o'z guruhlari

---

## 3. DAVOMAT MODULI (Attendance)

### Model va Hisob-Kitoblar

#### AttendanceStatistics Model (`attendance/models.py:40`)
- **Hisob-kitob**: `calculate_statistics()`
  - `total_lessons`: Jami darslar soni
  - `present_count`: Kelganlar soni (status='present')
  - `late_count`: Kechikkanlar soni (status='late')
  - `absent_count`: Kelmaganlar soni (status='absent')
  - `attendance_percentage` = `((present_count + late_count) / total_lessons) * 100`

### View va Statistikalar

#### AttendanceListView (`attendance/views.py:13`)
- **Statistikalar**:
  - `present_count`: Kelganlar
  - `late_count`: Kechikkanlar
  - `absent_count`: Kelmaganlar
  - `attendance_percentage`: Davomat foizi

#### GroupAttendanceView (`attendance/views.py:65`)
- **Guruh bo'yicha davomat**: Har bir o'quvchi uchun oylik davomat statistikasi
- **Hisob-kitoblar**: Present, Late, Absent soni va foizlari

### Signals
- Attendance saqlanganda statistikalar avtomatik yangilanadi (`attendance/signals.py:9`)

---

## 4. IMTIHON MODULI (Exams)

### Model va Hisob-Kitoblar

#### ExamResult Model (`exams/models.py:86`)
- **Hisob-kitob**: `calculate_score(student_answers)`
  - Ball hisoblash: Single choice va Multiple choice savollar
  - `percentage` = `(earned_points / total_points) * 100`
  - `is_passed`: Guruh o'rtacha ballidan yuqori bo'lsa o'tdi

### View va Statistikalar

#### ExamListView (`exams/views.py:13`)
- **Statistikalar**:
  - `total_exams`: Jami imtihonlar
  - `upcoming_exams`: Kutilayotgan imtihonlar (date >= today)

#### ExamResultsView (`exams/views.py:222`)
- **Statistikalar**:
  - `avg_score`: O'rtacha ball (Avg('score'))
  - `passed_count`: O'tganlar soni (is_passed=True)
  - `total_count`: Jami o'quvchilar

---

## 5. VAZIFALAR MODULI (Homework)

### Model va Hisob-Kitoblar

#### Homework Model (`homework/models.py:8`)
- **Hisob-kitoblar**:
  - `is_overdue`: Deadline o'tib ketganmi? (property)
  - `is_late`: Kechikkanmi? (save() metodida avtomatik)

### View va Statistikalar

#### HomeworkListView (`homework/views.py:13`)
- **Statistikalar**:
  - `total_homeworks`: Jami vazifalar
  - `submitted_count`: Topshirilgan (is_submitted=True)
  - `pending_count`: Kutilmoqda (is_submitted=False, deadline >= today)
  - `overdue_count`: Kechikkan (is_submitted=False, deadline < today)
  - `graded_count`: Baholangan (grade__isnull=False)

---

## 6. FOLLOW-UPLAR MODULI (CRM)

### Model va Hisob-Kitoblar

#### FollowUp Model (`crm/models.py:164`)
- **Hisob-kitoblar**:
  - `is_overdue`: Kechikkanmi? (save() metodida)
  - `calculate_work_hours_due_date()`: Ish vaqti ichida bo'lgan due_date hisoblash

#### SalesKPI Model (`crm/models.py:653`)
- **Hisob-kitob**: `calculate_kpi()`
  - `total_kpi_score` = 
    - Follow-up completion rate * 30%
    - Conversion rate * 30%
    - Response time score * 20%
    - Overdue follow-ups score * 10%
    - Enrolled leads rate * 10%

#### DailyKPI Model (`crm/models.py:618`)
- Kunlik KPI statistikalar

### View va Statistikalar

#### FollowUpListView (`crm/views.py:785`)
- Filterlar: Status, Sales, Lead

#### FollowUpTodayView (`crm/views.py`)
- Bugungi follow-uplar

#### FollowUpOverdueView (`crm/views.py`)
- Kechikkan follow-uplar

#### CRMAnalyticsView (`crm/views.py:1533`)
- **Umumiy statistika**:
  - `total_leads`: Jami lidlar
  - `enrolled_leads`: Yozilgan lidlar
  - `lost_leads`: Yo'qotilgan lidlar
  - `trial_leads`: Trial lidlar
  - `conversion_rate`: Konversiya foizi
- **Bugungi statistika**:
  - `today_leads`: Bugungi yangi lidlar
  - `today_followups`: Bugungi follow-uplar
  - `overdue_followups`: Kechikkan follow-uplar
- **Sotuvchilar statistikasi**: Top 10 sotuvchi (enrolled_count bo'yicha)
- **Manbalar bo'yicha**: Har bir manba uchun lidlar soni
- **Cache**: Statistikalar cache'lanadi (1 soat)

#### SalesKPIDetailView (`crm/views.py:1658`)
- **Statistikalar**:
  - `total_leads`: Jami lidlar
  - `enrolled_leads`: Yozilgan lidlar
  - `conversion_rate`: Konversiya foizi
  - `trial_lessons_count`: Sinov darslari
  - `lost_leads`: Yo'qotilgan lidlar
  - `overdue_followups`: Kechikkan follow-uplar
  - `today_followups`: Bugungi follow-uplar

### Celery Tasks

#### `calculate_daily_kpi` (`crm/tasks.py:435`)
- **Vazifa**: Kunlik KPI hisoblash
- **Vaqt**: Har kuni 23:55
- **Logic**: Har bir sotuvchi uchun kunlik KPI yaratadi/yangilaydi

#### `calculate_monthly_kpi` (`crm/tasks.py:513`)
- **Vazifa**: Oylik KPI hisoblash
- **Vaqt**: Har oyning 1-kuni 5:00
- **Logic**: Har bir sotuvchi uchun oylik KPI yaratadi/yangilaydi

#### `check_overdue_followups` (`crm/tasks.py:256`)
- **Vazifa**: Overdue follow-uplarni tekshirish
- **Vaqt**: Har 5 daqiqada

#### `send_followup_reminders` (`crm/tasks.py:224`)
- **Vazifa**: Follow-up eslatmalarini yuborish
- **Vaqt**: Har 30 daqiqada

#### `create_contacted_followups` (`crm/tasks.py:684`)
- **Vazifa**: 'Contacted' statusidagi lidlar uchun ketma-ket follow-up'lar yaratish
- **Vaqt**: Har 2 soatda

---

## 7. GAMIFICATION MODULI

### Model va Hisob-Kitoblar

#### StudentPoints Model (`gamification/models.py:54`)
- **Hisob-kitob**: `calculate_total_points()`
  - Guruh bo'yicha jami ballarni hisoblash
  - PointTransaction'lardan ball yig'ish (guruhga tegishli)

#### PointTransaction Model
- **Ball turlari**:
  - Attendance present: +5
  - Attendance late: +3
  - Homework on time: +10
  - Homework late: +3
  - Attendance absent: -5
  - Exam high score: +20

#### Rankings
- **GroupRanking**: Guruh bo'yicha reyting
- **BranchRanking**: Filial bo'yicha reyting
- **OverallRanking**: Markaz bo'yicha reyting
- **MonthlyRanking**: Oylik reyting (Top 10/25/50/100)

### View va Statistikalar

#### StudentRankingView (`gamification/views.py:191`)
- **Hisob-kitob**: Har bir student uchun jami ballarni yig'ish (Sum(total_points))
- **Saralash**: Ball bo'yicha teskari tartib
- **Rank qo'shish**: 1, 2, 3...

#### GroupsRankingView (`gamification/views.py:232`)
- **Hisob-kitob**: Har bir guruh uchun o'rtacha ball (Avg(total_points))

#### MonthlyRankingView (`gamification/views.py:141`)
- **Hisob-kitob**: Oylik reyting (Top 10/25/50/100)

### Celery Tasks

#### `update_group_rankings` (`gamification/tasks.py`)
- **Vazifa**: Guruh reytinglarini yangilash
- **Vaqt**: Har 2 soatda

#### `update_branch_rankings` (`gamification/tasks.py`)
- **Vazifa**: Filial reytinglarini yangilash
- **Vaqt**: Har 4 soatda

#### `update_overall_rankings` (`gamification/tasks.py`)
- **Vazifa**: Umumiy reytinglarni yangilash
- **Vaqt**: Har 6 soatda

#### `update_monthly_rankings` (`gamification/tasks.py`)
- **Vazifa**: Oylik reytinglarni yangilash
- **Vaqt**: Har oyning 1-kuni

### Signals
- Attendance saqlanganda avtomatik ball beriladi (present: +5, late: +3, absent: -5)
- Homework topshirilganda ball beriladi (vaqtida: +10, kech: +3)
- Exam natijasi saqlanganda ball beriladi (yuqori ball: +20)
- Badge berish shartlari tekshiriladi (`gamification/signals.py`)

---

## 8. MENTOR KPI MODULI

### Model va Hisob-Kitoblar

#### MentorKPI Model (`mentors/models.py`)
- **Hisob-kitob**: 7 ta mezon bo'yicha KPI hisoblash:
  1. Dars sifati (o'quvchilar bahosi 1-5) - 20% vazn
  2. Davomatni vaqtida kiritish - 15% vazn
  3. Uy vazifalarini o'z vaqtida baholash - 15% vazn
  4. O'quvchilarning rivojlanish dinamikasi - 15% vazn
  5. Guruh reytingidagi o'rtacha ball - 15% vazn
  6. Ota-onalar feedbacklari - 10% vazn
  7. Oylik hisobotlarni to'ldirish - 10% vazn

### Celery Tasks

#### `calculate_mentor_kpi` (`mentors/tasks.py:20`)
- **Vazifa**: Mentor KPI hisoblash
- **Vaqt**: Har oyning 1-kuni 2:00

#### `calculate_all_mentors_kpi` (`mentors/tasks.py`)
- **Vazifa**: Barcha mentorlar uchun KPI hisoblash
- **Vaqt**: Har oyning 1-kuni 2:00

---

## 9. ANALYTICS MODULI

### View va Statistikalar

#### StatisticsDashboardView (`analytics/views.py:18`)
- **Umumiy statistika**:
  - O'quvchilar, Mentorlar, Kurslar, Guruhlar soni
  - Davomat statistikasi (bu oy)
  - Uy vazifalari va imtihonlar statistikasi
  - Filiallar statistikasi
  - CRM statistikasi
  - Mentor KPI statistikasi
  - Gamification statistikasi
  - Finance statistikasi

#### BranchStatisticsView (`analytics/views.py:157`)
- Filial bo'yicha batafsil statistika
- O'quvchilar, kurslar, guruhlar soni
- Davomat statistikasi
- Reytinglar (Top 20)

#### CourseStatisticsView (`analytics/views.py:244`)
- Kurs bo'yicha batafsil statistika
- Guruhlar va o'quvchilar soni
- Progress statistikasi
- Guruhlar statistikasi

---

## 10. AUTOMATIK HISOB-KITOBLAR (Celery Beat Schedule)

### Finance Tasks
- `create-payment-reminders`: Har kuni (to'lov eslatmalari)
- `check-overdue-payments`: Har kuni (qarzlar tekshirish)
- `generate-monthly-financial-report`: Har oyning 1-kuni (oylik hisobot)

### CRM Tasks
- `assign-leads-to-sales`: Har 10 daqiqada (yangi lidlarni taqsimlash)
- `check-overdue-followups`: Har 5 daqiqada (kechikkan follow-uplar)
- `send-followup-reminders`: Har 30 daqiqada (eslatmalar yuborish)
- `send-trial-reminders`: Har 15 daqiqada (sinov darsi eslatmalari)
- `calculate-daily-kpi`: Har kuni 23:55 (kunlik KPI)
- `calculate-sales-kpi`: Har oyning 1-kuni 5:00 (oylik KPI)
- `check-reactivation`: Har kuni 9:00 (qayta aktivlashtirish)
- `check-leave-expiry`: Har kuni 22:00 (ruxsatlar tugashi)
- `create-contacted-followups`: Har 2 soatda (ketma-ket follow-up'lar)
- `send-daily-statistics`: Har kuni 20:00 (kunlik statistika)
- `import-google-sheets`: Har 30 daqiqada (Google Sheets import)

### Gamification Tasks
- `update-group-rankings`: Har 2 soatda (guruh reytinglari)
- `update-branch-rankings`: Har 4 soatda (filial reytinglari)
- `update-overall-rankings`: Har 6 soatda (umumiy reytinglar)
- `update-monthly-rankings`: Har oyning 1-kuni (oylik reytinglar)

### Mentor Tasks
- `calculate-all-mentors-kpi`: Har oyning 1-kuni 2:00 (barcha mentorlar KPI)
- `update-mentor-rankings`: Har oyning 1-kuni 3:00 (mentorlar reytingi)

### Parents Tasks
- `generate-monthly-parent-reports`: Har oyning 1-kuni 4:00 (ota-onalarga oylik hisobot)

### Telegram Bot Tasks
- `send-lesson-reminders`: Har 5 daqiqada (dars eslatmalari)
- `send-homework-deadline-reminders`: Har kuni 9:00 (uy vazifasi eslatmalari)
- `send-attendance-notifications`: Har kuni 20:00 (davomat xabarlari)

---

## XULOSA

### Mavjud Funksionalliklar

1. **Moliya**: To'liq shartnoma, to'lov, qarz tracking va hisobotlar
   - Avtomatik to'lov rejasi yaratish
   - To'lov eslatmalari
   - Qarzlar tracking
   - Moliya hisobotlari (kunlik, haftalik, oylik, yillik)

2. **Darslar**: Progress tracking, guruh statistikasi
   - O'quvchi progress hisoblash (topiclar bo'yicha)
   - Guruh to'lish darajasi

3. **Davomat**: Avtomatik statistika hisoblash
   - Real-time statistika yangilanish (signals)
   - O'quvchi va guruh bo'yicha davomat foizi

4. **Imtihon**: Ball hisoblash, natijalar statistikasi
   - Avtomatik ball hisoblash
   - O'rtacha ball va o'tish statistikasi

5. **Vazifalar**: Deadline tracking, status statistikasi
   - Kechikkan vazifalar tracking
   - Topshirish statistikasi

6. **Follow-uplar**: KPI hisoblash, avtomatik yaratish
   - Kunlik va oylik KPI hisoblash
   - Avtomatik follow-up yaratish
   - Eslatmalar yuborish

7. **Gamification**: Avtomatik ball berish, reytinglar
   - Real-time ball berish (signals)
   - Guruh, filial, umumiy va oylik reytinglar
   - Badge berish

8. **Mentor KPI**: 7 mezon bo'yicha KPI hisoblash
   - Oylik KPI avtomatik hisoblash
   - Mentorlar reytingi

9. **Analytics**: Umumiy statistikalar
   - Markaz, filial va kurs bo'yicha statistikalar

### Avtomatiklashtirish

- **Django Signals**: Real-time yangilanishlar
  - Attendance → Statistics yangilanish
  - Payment → Contract yangilanish
  - Attendance/Homework/Exam → Ball berish
  - Shartnoma → To'lov rejasi yaratish

- **Celery Tasks**: Background processing
  - Periodic hisob-kitoblar
  - Eslatmalar yuborish
  - KPI hisoblash

- **Celery Beat**: Periodic tasks (kunlik, oylik)
  - 20+ turli tasklar
  - Har daqiqa, soat, kun, oy davriylik bilan

### Optimizatsiya

- **Database Indexes**: Tez qidiruv uchun
  - Barcha model'larda indexlar mavjud
  - Foreign key va filter maydonlarida indexlar

- **Caching**: Analytics statistikalar cache'lanadi
  - CRMAnalyticsView: 1 soat cache

- **Select Related/Prefetch**: Query optimizatsiyasi
  - Ko'p view'larda select_related va prefetch_related ishlatilgan

### Ishlash Jarayoni

1. **Real-time hisob-kitoblar**: Signals orqali darhol yangilanadi
2. **Periodic hisob-kitoblar**: Celery Beat orqali avtomatik bajariladi
3. **Statistikalar**: View'larda dinamik hisoblanadi
4. **Hisobotlar**: Celery task'lari orqali generatsiya qilinadi

### Umumiy Holat

Loyihadagi barcha modullar to'liq funksional va avtomatlashtirilgan. Hisob-kitoblar real-time va periodic tarzda avtomatik bajariladi. Statistikalar ham real-time, ham cache orqali optimallashtirilgan.

