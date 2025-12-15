# GEEKS CRM — LMS + CRM Tizimi

GEEKS ANDIJAN o'quv markazi uchun yagona LMS + CRM tizimi.

## 🚀 Texnologiyalar

- **Backend**: Django 5.0.1
- **Database**: SQLite
- **Task Queue**: Celery + Redis
- **Frontend**: HTML + TailwindCSS
- **Integrations**: Telegram Bot API

## 📦 O'rnatish

1. Virtual environment yaratish:
```bash
python -m venv venv
```

2. Virtual environmentni faollashtirish:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Paketlarni o'rnatish:
```bash
pip install -r requirements.txt
```

4. Migratsiyalarni bajarish:
```bash
python manage.py migrate
```

5. Superuser yaratish:
```bash
python manage.py createsuperuser
```

6. Serverni ishga tushirish:
```bash
python manage.py runserver
```

## 📁 Loyiha Strukturasi

```
geeks_crm/
├── accounts/          # User, Branch, StudentProfile, ParentProfile
├── courses/           # Course, Module, Topic, Group, Room, Lesson
├── attendance/        # Davomat tizimi
├── homework/          # Uy vazifalari
├── exams/             # Imtihonlar
├── gamification/      # Gamifikatsiya (ball, badge, reyting)
├── mentors/           # Mentor KPI
├── parents/           # Ota-onalar moduli
├── crm/               # Lead management
├── finance/           # Moliya moduli
└── telegram_bot/      # Telegram bot integratsiyasi
```

## 🔐 Rollar

- **Admin**: To'liq nazorat
- **Manager**: Mentorlar, guruhlar, lead management
- **Mentor**: Dars, attendance, homework baholash
- **Student**: Kurs materiallari, vazifalar
- **Parent**: Farzandining progressini ko'rish
- **Accountant**: To'lovlar, hisob-kitob
- **Sales**: Lead management
- **Sales Manager**: Sotuvchilar boshqaruvi

## 📝 Faza 1: Asosiy Infrastruktura ✅

- [x] Django loyihasini yaratish
- [x] Authentication va Authorization
- [x] Asosiy modellar (User, Branch, Course, Module, Topic, Group, Room)
- [x] Admin panel asoslari
- [x] Celery konfiguratsiyasi
- [x] URL routing (barcha applar)
- [x] Views va funksiyalar
- [x] Django signals (avtomatik yangilanishlar)
- [x] Database indexlar optimizatsiyasi
- [x] Model validators va xavfsizlik

## 📝 Faza 2: LMS Asosiy Funksiyalar ✅

- [x] Kurslar va mavzular (materiallar, progress tracking)
- [x] Darslar moduli
- [x] Davomat tizimi (Keldi/Kelmadi/Kech qoldi)
- [x] Uy vazifalari (deadline, baholash)
- [x] Imtihonlar (Test, Yozma, Amaliy)

## 📝 Faza 3: Gamifikatsiya ✅

- [x] Ball tizimi (PointTransaction, StudentPoints)
- [x] Avtomatik ball berish (signals):
  - Darsga qatnashish: +5
  - Uy vazifani vaqtida topshirish: +10
  - Kech topshirish: +3
  - Darsni qoldirish: -5
  - Imtihondan yuqori ball: +20
- [x] Badge tizimi (Badge, StudentBadge)
- [x] Reytinglar:
  - Guruh bo'yicha (GroupRanking)
  - Filial bo'yicha (BranchRanking)
  - Markaz bo'yicha (OverallRanking)
  - Oylik (MonthlyRanking - Top 10/25/50/100)
- [x] Celery tasks (avtomatik reyting yangilanish)

## 📝 Faza 4: Mentor KPI ✅

- [x] Mentor KPI modellari (MentorKPI, LessonQuality, MonthlyReport, ParentFeedback)
- [x] KPI hisoblash funksiyalari (7 ta mezon):
  - Dars sifati (o'quvchilar bahosi 1-5)
  - Davomatni vaqtida kiritish
  - Uy vazifalarini o'z vaqtida baholash
  - O'quvchilarning rivojlanish dinamikasi
  - Guruh reytingidagi o'rtacha ball
  - Ota-onalar feedbacklari
  - Oylik hisobotlarni to'ldirish
- [x] Oylik hisobotlar (xulq, davomat, o'zlashtirish, o'zgarish, izohlar)
- [x] Mentorlar reytingi
- [x] Celery tasks (avtomatik KPI hisoblash)
- [x] Telegram bot integratsiyasi (ota-onalarga hisobot yuborish)

## 📝 Faza 5: Ota-onalar Moduli ✅

- [x] Oylik avtomatik hisobotlar (MonthlyParentReport):
  - Davomat foizi va statistikasi
  - Uy vazifalarini bajarish darajasi
  - Test va imtihon natijalari
  - Kuchli va kuchsiz tomonlar
  - Progress va o'zgarish
  - Mentor oylik harakteristikasi
- [x] Ota-ona kabineti:
  - Dashboard (barcha farzandlar statistikasi)
  - Farzandning batafsil ma'lumotlari
  - Darslar tarixi
  - Uy vazifalari holati
  - Test va imtihon natijalari
  - Keldi/kelmadi ro'yxati
  - Mentor sharhlari (oylik hisobotlar)
- [x] Celery tasks (avtomatik hisobot generatsiya va Telegram yuborish)

## 📝 Faza 6: Telegram Bot ✅

- [x] Bot handlers va commands:
  - /start - Botni ishga tushirish
  - /help - Yordam
- [x] O'quvchilar uchun handlers:
  - /lessons - Darslar ro'yxati
  - /homework - Uy vazifalari
  - /exams - Imtihonlar
  - /points - Ballar va reyting
- [x] Ota-onalar uchun handlers:
  - /children - Farzandlar ro'yxati
  - /reports - Oylik hisobotlar
- [x] Mentorlar uchun handlers:
  - /schedule - Dars jadvali
  - /homework_grade - Baholash kerak bo'lgan vazifalar
- [x] Webhook va polling konfiguratsiyasi
- [x] Django management command (runbot)

## 📝 Faza 7: CRM - Lead Management ✅

- [x] Lead modellari:
  - Lead (statuslar bilan)
  - LeadStatus (Kanban board uchun)
  - LeadHistory (tarix)
- [x] Follow-up tizimi:
  - Avtomatik follow-up yaratish (Yangi → 5 daqiqada, Aloqa qilindi → 24s/3k/7k/14k)
  - Overdue tracking
  - Qayta rejalashtirish
- [x] Sinov darslari:
  - TrialLesson model
  - Sinovga yozish (guruh, xona, vaqt)
  - Sinov natijasini kiritish
  - Eslatmalar (8-10 soat va 2 soat oldin)
- [x] Sotuvchilar boshqaruvi:
  - SalesProfile
  - WorkSchedule (ish vaqti)
  - Leave (ruxsat boshqaruvi)
- [x] Avtomatik taqsimlash:
  - Ish vaqtida bo'lgan sotuvchilarga taqsimlash
  - Maksimal lidlar soni
- [x] KPI tizimi:
  - SalesKPI (5 ta mezon)
  - Sotuvchilar reytingi
- [x] Reaktivatsiya:
  - Yo'qotilgan lidlar uchun qayta aloqa (7/14/30 kun)
- [x] Xabarlar:
  - Manager/Admin dan sotuvchilarga xabarlar
- [x] Celery tasks (7 ta task)
- [x] Telegram integratsiyasi

## 📝 Qo'shimcha Ishlar (Bajarildi) ✅

- [x] Group Transfers:
  - GroupTransfer modeli
  - O'quvchini bir guruhdan boshqasiga ko'chirish
  - Progress avtomatik yangilanish
  - Transfer tarixi
- [x] Overall Statistics Dashboard:
  - Umumiy statistika (o'quvchilar, mentorlar, kurslar, guruhlar)
  - Davomat statistikasi
  - Uy vazifalari va imtihonlar statistikasi
  - Filiallar statistikasi
  - CRM statistikasi
  - Mentor KPI statistikasi
  - Gamification statistikasi
  - Filial va kurs bo'yicha batafsil statistika

## 📝 Faza 8: Moliya Moduli ✅

- [x] Shartnoma modellari:
  - ContractTemplate (shablonlar)
  - Contract (shartnomalar)
  - Shartnoma raqami avtomatik yaratish
  - Status boshqaruvi (draft, active, suspended, completed, cancelled)
  - Discount tizimi
- [x] To'lov modellari:
  - PaymentPlan (oylik to'lov rejasi)
  - Payment (to'lovlar)
  - PaymentHistory (to'lovlar tarixi)
  - To'lov raqami avtomatik yaratish
  - To'lov usullari (naqd, karta, o'tkazma)
- [x] Qarzlar va eslatmalar:
  - Debt (qarzlar)
  - PaymentReminder (to'lov eslatmalari)
  - Overdue tracking
  - Priority tizimi (low, medium, high, urgent)
- [x] Moliya hisobotlari:
  - FinancialReport (kunlik, haftalik, oylik, yillik)
  - Statistikalar (revenue, payments, debts, discounts)
- [x] Dashboard:
  - Umumiy statistika
  - Bu oy statistikasi
  - Qarzlar va eslatmalar
- [x] Celery tasks:
  - Avtomatik to'lov eslatmalari yaratish (3 kun, 1 kun, 0 kun oldin)
  - Overdue to'lovlarni tekshirish
  - Oylik moliya hisoboti generatsiya
- [x] Telegram integratsiyasi:
  - To'lov eslatmalari yuborish (o'quvchilar va ota-onalarga)
- [x] Django signals:
  - Shartnoma yaratilganda to'lov rejasi avtomatik yaratish
  - To'lov yaratilganda contract paid_amount yangilash
  - To'lovlar tarixi

## 🔄 Keyingi Fazalar

- Faza 9: Frontend va UI
- Faza 10: Testing va Optimizatsiya

