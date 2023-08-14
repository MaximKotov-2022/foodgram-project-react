import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV-файла'

    def add_arguments(self, parser):
        parser.add_argument("--path", type=str)
        parser.add_argument(
            "--delete-existing",
            action="store_true",
            dest="delete_existing",
            default=False,
            help="Удалить существующие записи перед загрузкой",
        )

    def handle(self, *args, **options):
        if options["delete_existing"]:
            for model in [Ingredient]:
                model.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    "Существующие ингредиенты удалены."
                )
            )
        csv_file = options['path']
        ingredients = []

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)

            for row in reader:
                ingredient = Ingredient(
                    name=row[0],
                    measurement_unit=row[1]
                )
                ingredients.append(ingredient)

        Ingredient.objects.bulk_create(ingredients)
        self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены.'))
