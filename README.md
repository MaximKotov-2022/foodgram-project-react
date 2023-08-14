# foodgram-project-react
Дипломный проект. Приложение «Продуктовый помощник»: сайт, на котором
пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и
подписываться на публикации других авторов. Сервис «Список покупок» позволит
пользователям создавать список продуктов, которые нужно купить для
приготовления выбранных блюд.

## Технологии
+ Python
+ Django
+ Django REST Framework
+ PostgreSQL
+ Docker
+ Github Actions

## Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/MaximKotov-2022/foodgram-project-react
```

```
cd foodgram-project-react
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/Scripts/activate
```

```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py makemigrations
```
```
python3 manage.py migrate
```

## Для запуска на собственном сервере:
1. Скопируйте из репозитория файлы, расположенные в директории infra:
    - docker-compose.yml
    - nginx.conf
2. На сервере создайте директорию foodgram;
3. В директории foodgram создайте директорию infra и поместите в неё файлы:
    - docker-compose.yml
    - nginx.conf
    - .env (пустой)

4. В директории infra следует выполнить команды:
```
docker-compose up -d
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
```

5. Для создания суперпользователя, выполните команду:
```
docker-compose exec backend python manage.py createsuperuser
```

6. Для добавления ингредиентов в базу данных, выполните команду:
```
docker-compose exec backend python manage.py add_data ingredients.csv tags_ingr_ingredient
```
После выполнения этих действий проект будет запущен и доступен по адресам:
- Главная страница: http://<ip-адрес>/recipes/
- API проекта: http://<ip-адрес>/api/
- Admin-зона: http://<ip-адрес>/admin/

7. Теги вручную добавляются в админ-зоне в модель Tags;
8. Проект запущен и готов к регистрации пользователей и добавлению рецептов.

## Файл .env должен быть заполнен следующими данными:
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=databasee
DB_PORT=1111

## Автор
Котов Максим