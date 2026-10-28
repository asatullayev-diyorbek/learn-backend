"""
Seed demo catalog content: `python manage.py seed_courses`.

Idempotent (get_or_create keyed on slug / full_name), so running it again
never duplicates rows and never overwrites edits made later in admin. It is
a manual command on purpose and is NOT wired into migrations.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.courses.models import Category, Course, Instructor

CATEGORIES = [
    ("Backend", "backend"),
    ("Frontend", "frontend"),
    ("Ma'lumotlar bazalari", "malumotlar-bazalari"),
    ("Mobil dasturlash", "mobil-dasturlash"),
]

INSTRUCTORS = [
    {
        "full_name": "Diyorbek Asatullayev",
        "title": "Backend dasturchi",
        "bio": "Python va Django bo'yicha 6 yillik tajribaga ega, yuqori yuklamali API'lar quradi.",
    },
    {
        "full_name": "Malika Karimova",
        "title": "Frontend dasturchi",
        "bio": "React va zamonaviy veb-interfeyslar bo'yicha mutaxassis, mentorlik qiladi.",
    },
    {
        "full_name": "Jasur Toshmatov",
        "title": "Ma'lumotlar bazasi muhandisi",
        "bio": "PostgreSQL va SQL optimizatsiyasi bo'yicha ko'p yillik amaliy tajriba.",
    },
    {
        "full_name": "Nodira Yusupova",
        "title": "Mobil dasturchi",
        "bio": "Flutter va Kotlin'da o'nlab ilovalarni ishlab chiqqan.",
    },
]

# (slug, title, category slug, instructor full_name, level, summary, description)
COURSES = [
    (
        "python-asoslari",
        "Python asoslari",
        "backend",
        "Diyorbek Asatullayev",
        Course.LEVEL_BEGINNER,
        "Dasturlashni noldan boshlang: o'zgaruvchilar, shartlar, sikllar va funksiyalar.",
        "Ushbu kurs dasturlash bilan endi tanishayotganlar uchun mo'ljallangan. "
        "Python sintaksisi, ma'lumot turlari, shart operatorlari, sikllar, funksiyalar "
        "va fayllar bilan ishlashni amaliy mashqlar orqali o'rganasiz. Kurs oxirida "
        "kichik konsol ilovasini mustaqil yozib chiqasiz.",
    ),
    (
        "django-bilan-veb-dasturlash",
        "Django bilan veb-dasturlash",
        "backend",
        "Diyorbek Asatullayev",
        Course.LEVEL_INTERMEDIATE,
        "Django yordamida to'liq veb-ilova yarating: modellar, view'lar, shablonlar va admin.",
        "Kursda Django loyihasini noldan quramiz: modellar va migratsiyalar, ORM so'rovlari, "
        "view va URL marshrutlash, shablonlar, formalar hamda admin panel. Har bir mavzu "
        "real loyiha ustida mustahkamlanadi va oxirida ilovani serverga joylashtiramiz.",
    ),
    (
        "rest-api-loyihalash",
        "REST API loyihalash",
        "backend",
        "Diyorbek Asatullayev",
        Course.LEVEL_ADVANCED,
        "Django REST Framework bilan xavfsiz, tez va hujjatlashtirilgan API'lar quring.",
        "Serializer'lar, ruxsatlar, autentifikatsiya, sahifalash, throttling va API "
        "versiyalash kabi mavzularni chuqur ko'rib chiqamiz. N+1 so'rovlar muammosini "
        "aniqlash va bartaraf etish, testlar yozish hamda API'ni hujjatlashtirishni "
        "amalda o'rganasiz.",
    ),
    (
        "html-va-css-asoslari",
        "HTML va CSS asoslari",
        "frontend",
        "Malika Karimova",
        Course.LEVEL_BEGINNER,
        "Birinchi veb-sahifangizni yarating: semantik HTML, Flexbox va Grid.",
        "Kurs veb-sahifa qanday tuzilishini tushuntirishdan boshlanadi. Semantik HTML "
        "teglari, CSS selektorlari, Flexbox va Grid yordamida joylashuv, moslashuvchan "
        "(responsive) dizayn tamoyillarini o'rganib, shaxsiy portfolio sahifasini "
        "yasaysiz.",
    ),
    (
        "javascript-chuqur",
        "JavaScript: chuqur o'rganish",
        "frontend",
        "Malika Karimova",
        Course.LEVEL_INTERMEDIATE,
        "Closure, prototiplar, asinxron kod va DOM bilan ishlashni puxta o'zlashtiring.",
        "JavaScript'ning ichki ishlash mexanizmlarini tushunib olamiz: scope va closure, "
        "this va prototiplar, Promise va async/await, hodisalar sikli (event loop). "
        "Har bir bo'lim brauzerda ishlaydigan amaliy topshiriqlar bilan yakunlanadi.",
    ),
    (
        "react-bilan-ilovalar",
        "React bilan zamonaviy ilovalar",
        "frontend",
        "Malika Karimova",
        Course.LEVEL_ADVANCED,
        "Komponentlar, hook'lar va holat boshqaruvi bilan murakkab interfeyslar yarating.",
        "React komponentlari, props va state, hook'lar (useState, useEffect, useMemo), "
        "marshrutlash, server bilan ishlash va holatni boshqarish usullarini o'rganasiz. "
        "Kurs davomida backend API'ga ulangan to'liq ilova quriladi.",
    ),
    (
        "sql-asoslari",
        "SQL asoslari",
        "malumotlar-bazalari",
        "Jasur Toshmatov",
        Course.LEVEL_BEGINNER,
        "Ma'lumotlarni so'rash, saralash va guruhlashni oddiy misollar orqali o'rganing.",
        "Relatsion ma'lumotlar bazasi nima ekanini tushunib, SELECT, WHERE, ORDER BY, "
        "GROUP BY va JOIN so'rovlarini yozishni o'rganasiz. Har bir dars real hayotga "
        "yaqin jadval va vazifalar bilan mustahkamlanadi.",
    ),
    (
        "postgresql-optimizatsiya",
        "PostgreSQL: unumdorlik va optimizatsiya",
        "malumotlar-bazalari",
        "Jasur Toshmatov",
        Course.LEVEL_ADVANCED,
        "Indekslar, EXPLAIN tahlili va tranzaksiyalar bilan sekin so'rovlarni tezlashtiring.",
        "Indeks turlari, so'rov rejasini EXPLAIN ANALYZE orqali o'qish, tranzaksiyalar va "
        "izolyatsiya darajalari, bloklanishlar hamda sxemani to'g'ri loyihalashni chuqur "
        "o'rganamiz. Kurs ishlab chiqarishdagi real muammolar tahliliga asoslangan.",
    ),
    (
        "flutter-boshlovchilar-uchun",
        "Flutter: boshlovchilar uchun",
        "mobil-dasturlash",
        "Nodira Yusupova",
        Course.LEVEL_BEGINNER,
        "Bitta kod bazasidan Android va iOS uchun chiroyli ilovalar yarating.",
        "Dart tilining asoslaridan boshlab, Flutter vidjetlari, sahifalar orasida "
        "o'tish, formalar va oddiy holat boshqaruvini o'rganasiz. Kurs oxirida "
        "telefoningizda ishlaydigan vazifalar ro'yxati ilovasini yaratasiz.",
    ),
    (
        "kotlin-android",
        "Kotlin bilan Android dasturlash",
        "mobil-dasturlash",
        "Nodira Yusupova",
        Course.LEVEL_INTERMEDIATE,
        "Jetpack Compose va zamonaviy arxitektura bilan native Android ilovalar yozing.",
        "Kotlin tili imkoniyatlari, Jetpack Compose bilan interfeys yaratish, ViewModel, "
        "korutinlar va tarmoq bilan ishlashni o'rganasiz. Ilovani tuzilmaviy va "
        "test qilinadigan qilib loyihalash amaliyotlariga alohida e'tibor beriladi.",
    ),
]


class Command(BaseCommand):
    help = "Idempotently seed demo categories, instructors and courses for the catalog."

    @transaction.atomic
    def handle(self, *args, **options):
        created = {"categories": 0, "instructors": 0, "courses": 0}

        categories = {}
        for name, slug in CATEGORIES:
            category, was_created = Category.objects.get_or_create(
                slug=slug, defaults={"name": name}
            )
            categories[slug] = category
            created["categories"] += was_created

        instructors = {}
        for data in INSTRUCTORS:
            instructor, was_created = Instructor.objects.get_or_create(
                full_name=data["full_name"],
                defaults={"title": data["title"], "bio": data["bio"]},
            )
            instructors[data["full_name"]] = instructor
            created["instructors"] += was_created

        for slug, title, category_slug, instructor_name, level, summary, description in COURSES:
            _, was_created = Course.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "category": categories[category_slug],
                    "instructor": instructors[instructor_name],
                    "level": level,
                    "summary": summary,
                    "description": description,
                },
            )
            created["courses"] += was_created

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete: created {categories} categories, {instructors} instructors, "
                "{courses} courses (existing rows left untouched).".format(**created)
            )
        )
