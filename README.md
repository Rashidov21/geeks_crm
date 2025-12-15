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

## 🔄 Keyingi Fazalar

- Faza 4: Mentor KPI
- Faza 5: Ota-onalar Moduli
- Faza 6: Telegram Bot (handlers)
- Faza 7: CRM - Lead Management
- Faza 8: Moliya Moduli
- Faza 9: Frontend va UI
- Faza 10: Analitika
- Faza 11: Testing va Optimizatsiya

