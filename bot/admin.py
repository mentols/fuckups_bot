from django.contrib import admin

from bot.models import Person, Room, Fuckup, Category, RoomRequest


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['id', 'username']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'tittle']


@admin.register(Fuckup)
class FuckupAdmin(admin.ModelAdmin):
    list_display = ['id', 'category']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'tittle']


@admin.register(RoomRequest)
class RoomRequest(admin.ModelAdmin):
    list_display = ['id', 'room']
