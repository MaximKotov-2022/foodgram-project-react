# Generated by Django 3.2 on 2023-08-14 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_alter_shoppingcart_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(blank=True, default=None, null=True, upload_to=''),
        ),
    ]
