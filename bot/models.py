from django.db import models


class Person(models.Model):
    tg_id = models.SmallIntegerField(null=True, unique=True)
    username = models.CharField(max_length=255, null=False)
    current_room_id = models.PositiveIntegerField(null=True)

    def __str__(self):
        return f'{self.username}'


class Room(models.Model):
    admins = models.ManyToManyField(Person, related_name='admins')
    persons = models.ManyToManyField(Person, related_name='persons')
    tittle = models.CharField(max_length=255, null=False, unique=True)

    def __str__(self):
        return f'{self.tittle}'


class Category(models.Model):
    tittle = models.CharField(max_length=255, null=False, unique=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.tittle}'


class Fuckup(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=False)
    category = models.ForeignKey(Category, on_delete=models.SET_DEFAULT, null=False, default="Косяк")
    content = models.CharField(max_length=455, null=False)
    author = models.ForeignKey(Person, on_delete=models.CASCADE, null=False)
    status = models.BooleanField(default=0)

    def __str__(self):
        return f'{self.content}'


class RoomRequest(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=False)
    required_user = models.ForeignKey(Person, on_delete=models.CASCADE, null=False)
    # is_required = models.BooleanField(default=0)

    def __str__(self):
        return f'{self.required_user} запрошен в  {self.room.tittle}'
