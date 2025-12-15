# GEEKS CRM - Color Palette va Dizayn Tizimi

## 🎨 Asosiy Rang Sxemasi (Dark Theme)

### Primary Colors (Asosiy ranglar)
```css
Navbar & Main UI: Slate-800, Slate-900
Accent: Indigo-600, Indigo-700, Indigo-800
Hover States: Indigo-50 backgrounds
```

### Module-Specific Colors (Modul ranglari)

| Modul | Rang | Icon Color | Hover BG | Ishlatish |
|-------|------|------------|----------|-----------|
| **Dashboard** | Indigo-600 | indigo-600 | indigo-50 | Umumiy dashboard |
| **Analytics** | Indigo-600 | indigo-600 | indigo-50 | Statistika va hisobotlar |
| **CRM** | Purple-700 | purple-700 | purple-50 | Lead management |
| **Finance** | Emerald-700 | emerald-700 | emerald-50 | Moliyaviy operatsiyalar |
| **Courses** | Blue-700 | blue-700 | blue-50 | Kurslar va o'quv dasturlari |
| **Attendance** | Teal-700 | teal-700 | teal-50 | Davomat kiritish |
| **Homework** | Orange-700 | orange-700 | orange-50 | Uy vazifalari |
| **Exams** | Rose-700 | rose-700 | rose-50 | Imtihonlar |
| **Mentors** | Violet-700 | violet-700 | violet-50 | Mentor KPI |
| **Parents** | Cyan-700 | cyan-700 | cyan-50 | Ota-onalar kabineti |
| **Gamification** | Amber-600 | amber-600 | amber-50 | Reytinglar va badgelar |

### Functional Colors (Funksional ranglar)

#### Success (Muvaffaqiyat)
```css
Primary: Emerald-600 (#059669)
Light: Emerald-50
Usage: Muvaffaqiyatli operatsiyalar, "Keldi" status, to'lovlar
```

#### Warning (Ogohlantirish)
```css
Primary: Amber-600 (#d97706)
Light: Amber-50
Usage: Kechikishlar, "Kech qoldi" status, muddatli vazifalar
```

#### Danger (Xato)
```css
Primary: Rose-600 (#e11d48)
Light: Rose-50
Usage: Xatolar, "Kelmadi" status, muammoli holatlar
```

#### Info (Ma'lumot)
```css
Primary: Sky-600 (#0284c7)
Light: Sky-50
Usage: Bildirishnomalar, ma'lumot ko'rsatish
```

### Neutral Colors (Neytral ranglar)

```css
Background: Gray-50 (#f9fafb)
Card Background: White (#ffffff)
Text Primary: Gray-900 (#111827)
Text Secondary: Gray-600 (#4b5563)
Border: Gray-200, Gray-300
Navbar: Slate-800, Slate-900
Footer: Slate-900
```

## 🎯 Rang Ishlatish Qoidalari

### 1. Navbar va Header
- **Background:** `bg-gradient-to-r from-slate-800 to-slate-900`
- **Text:** `text-white`
- **Hover:** `hover:bg-slate-700`
- **Logo:** White version

### 2. Sidebar Links
```html
<!-- Template -->
<a href="#" class="flex items-center space-x-3 px-3 py-2 rounded-lg 
              hover:bg-[MODULE-COLOR]-50 text-gray-700 hover:text-[MODULE-COLOR]-700 
              transition group">
    <i class="fas fa-icon text-[MODULE-COLOR]-600"></i>
    <span>Module Name</span>
</a>
```

### 3. Dashboard Cards
```html
<!-- Primary Card -->
<div class="bg-gradient-to-br from-[COLOR]-500 to-[COLOR]-600 text-white rounded-xl shadow-lg p-6">
    <!-- Content -->
</div>
```

### 4. Buttons

#### Primary Button (Asosiy amallar)
```html
<button class="bg-gradient-to-r from-indigo-600 to-indigo-700 
               hover:from-indigo-700 hover:to-indigo-800 
               text-white px-6 py-3 rounded-lg shadow-lg">
    Action
</button>
```

#### Secondary Button (Ikkilamchi)
```html
<button class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-lg">
    Cancel
</button>
```

#### Success Button
```html
<button class="bg-gradient-to-r from-emerald-600 to-emerald-700 text-white">
    Save
</button>
```

### 5. Status Badges

```html
<!-- Success -->
<span class="bg-emerald-100 text-emerald-800 border-emerald-500 px-3 py-1 rounded-full">
    Keldi
</span>

<!-- Warning -->
<span class="bg-amber-100 text-amber-800 border-amber-500 px-3 py-1 rounded-full">
    Kech qoldi
</span>

<!-- Danger -->
<span class="bg-rose-100 text-rose-800 border-rose-500 px-3 py-1 rounded-full">
    Kelmadi
</span>
```

### 6. Form Elements

#### Input Fields
```html
<input class="w-full px-4 py-3 border-2 border-gray-300 rounded-lg 
              focus:outline-none focus:ring-2 focus:ring-indigo-500 
              focus:border-transparent transition-all">
```

#### Select Dropdowns
```html
<select class="w-full px-4 py-3 border-2 border-gray-300 rounded-lg 
               focus:ring-2 focus:ring-indigo-500">
```

## 🚫 Ranglar Ishlatishda Qilmaslik Kerak

1. ❌ Bright colors (Yorqin ranglar) - Faqatgina aksentlar uchun
2. ❌ Too many colors in one component - Har bir komponentda 2-3 ta rang
3. ❌ Inconsistent shades - Bir modulda bir xil shadeni ishlating
4. ❌ Low contrast text - Text va background orasida yetarli kontrast bo'lishi kerak

## ✅ Best Practices

1. ✅ Dark navbar (slate-800/900) + Light content area (white/gray-50)
2. ✅ Module-specific colors faqat o'sha modul ichida
3. ✅ Functional colors (success, warning, danger) barcha joyda bir xil
4. ✅ Gradient'lar faqat asosiy UI elementlarda (buttons, cards)
5. ✅ Hover effects har doim subtil (50-100 opacity backgrounds)

## 🔄 Migration Summary

| Element | Old Color | New Color |
|---------|-----------|-----------|
| Navbar | blue-600 | slate-800/900 |
| Primary Actions | blue-600 | indigo-600/700 |
| Success | green-500 | emerald-600 |
| Warning | yellow-500 | amber-600 |
| Danger | red-500 | rose-600 |
| Footer | gray-900 | slate-900 |

## 📝 Qo'shimcha Eslatmalar

- Barcha ranglar **Tailwind CSS** standart ranglaridan olingan
- Dark theme uchun `800, 900` shadelardan foydalaniladi
- Light backgrounds uchun `50, 100` shadelar ishlatiladi
- Iconlar `600, 700` shadelar bilan
- Hover states uchun `700, 800` shadelar

---

**Last Updated:** 2024
**Maintained by:** GEEKS ANDIJAN Development Team

