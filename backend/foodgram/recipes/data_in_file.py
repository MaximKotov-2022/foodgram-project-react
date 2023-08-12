import csv

from django.core.management.base import BaseCommand

from .models import Ingredient


class Command(BaseCommand):
    """
    Команда загрузки данных из файла backend/data/ingredients.csv.
    """

    help = "Загрузка данных из файла backend/data/ingredients.csv"

    def handle(self, *args, **kwargs):
        """
        Обрабатывает команду загрузки данных из файла CSV. Использует данные
        из файла "data/ingredients.csv" для создания объектов Ingredient
        в базе данных, если данные еще не загружены.
        """
        try:
            if Ingredient.objects.exists():
                self.stdout.write("Данные уже загружены в базу данных.")
                return

            csv_file_path = "data/ingredients.csv"
            self._load_ingredients(csv_file_path)

            self.stdout.write("Данные успешно загружены в базу данных.")
        except FileNotFoundError:
            error_message = """Файл ingredients.csv не найден. Пожалуйста,
            убедитесь, что файл существует."""
            self.stdout.write(self.style.ERROR(error_message))
        except Exception as e:
            error_message = f"Произошла ошибка: {str(e)}"
            self.stdout.write(self.style.ERROR(error_message))

    @staticmethod
    def _load_ingredients(csv_file_path):
        """
        Загружает данные из CSV-файла и создает
        объекты Ingredient в базе данных.
        """
        with open(csv_file_path, encoding="utf-8") as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)
            for row in csvreader:
                name = row[0]
                measurement_unit = row[1]

                existing_ingredient = Ingredient.objects.filter(
                    name=name
                ).first()

                if existing_ingredient:
                    existing_ingredient.measurement_unit = measurement_unit
                    existing_ingredient.save()
                else:
                    Ingredient.objects.create(
                        name=name, measurement_unit=measurement_unit
                    )
