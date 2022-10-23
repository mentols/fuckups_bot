# Generated by Django 4.1.2 on 2022-10-22 01:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_alter_room_admins_alter_room_persons'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='tittle',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='room',
            name='admins',
            field=models.ManyToManyField(related_name='admins', to='bot.person'),
        ),
        migrations.AlterField(
            model_name='room',
            name='persons',
            field=models.ManyToManyField(related_name='persons', to='bot.person'),
        ),
        migrations.AlterField(
            model_name='room',
            name='tittle',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
