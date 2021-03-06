# Generated by Django 2.1.5 on 2019-02-09 18:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="FoodWeight",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("seq", models.IntegerField()),
                ("amount", models.DecimalField(decimal_places=3, max_digits=5)),
                ("desc", models.CharField(max_length=84)),
                ("weight", models.DecimalField(decimal_places=1, max_digits=7)),
                ("data_points", models.IntegerField(blank=True, null=True)),
                (
                    "deviation",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=7, null=True
                    ),
                ),
                (
                    "food",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.Food"
                    ),
                ),
            ],
        )
    ]
