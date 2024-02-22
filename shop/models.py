import uuid

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class Filters(models.Model):
    """Модель для фильтров товаров"""
    name = models.CharField(max_length=255, verbose_name='Имя фильтра')
    slug = models.SlugField(unique=True, default=None)

    class Meta:
        """Используем для задания параметров в админке, без необходимости добавления новых полей в саму модель. """
        ordering = ('name',)  # сортировка применяется и в отображении в админке и в шаблонах
        verbose_name = 'Фильтры'
        verbose_name_plural = 'Фильтры'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_filters', args=[self.slug])


class Category(models.Model):
    """Модель для категорий товаров"""
    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)

    class Meta:
        """Используем для задания параметров в админке, без необходимости добавления новых полей в саму модель. """
        ordering = ('name',)  # сортировка применяется и в отображении в админке и в шаблонах
        verbose_name = 'Категории'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Tag(models.Model):
    """Модель для тегов товаров"""
    name = models.CharField(max_length=255, verbose_name='Имя тега')
    slug = models.SlugField(unique=True)
    filters = models.ForeignKey(Filters, verbose_name='Фильтр', on_delete=models.CASCADE, default=None)

    class Meta:
        """Используем для задания параметров в админке, без необходимости добавления новых полей в саму модель. """
        ordering = ('name',)  # сортировка применяется и в отображении в админке и в шаблонах
        verbose_name = 'Теги'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_tag', args=[self.slug])


class Object(models.Model):
    """Модель оьъектов"""
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание', null=True)
    description2 = models.TextField(verbose_name='Описание', null=True)
    available = models.BooleanField(default=True, verbose_name='Доступность')
    address = models.TextField(verbose_name='Адрес')
    date = models.DateTimeField(verbose_name='Заселение до')

    class Meta:
        verbose_name = 'Объекты'  # отображение названия в админке
        verbose_name_plural = 'Объекты'  # отображение названия в админке
        ordering = ('title',)

    def __str__(self):
        return self.title

    # self ссылка на ЭК модели. Через self обращаемся к нужному атрибуту для формирования динамического url и
    # использования в шаблонах.
    def get_absolute_url(self):
        return reverse('shop:search_list_project', args=[self.slug])


class Frame(models.Model):
    """Модель копусов"""
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    number = models.FloatField(verbose_name='Номер корпуса')
    floors = models.IntegerField(verbose_name='Этажность', validators=[MaxValueValidator(50), MinValueValidator(1)])
    available = models.BooleanField(default=True, verbose_name='Доступность')
    ceiling_height = models.FloatField(verbose_name='Высота потолков')
    object = models.ForeignKey(Object, verbose_name='Объект', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Корпусы'  # отображение названия в админке
        verbose_name_plural = 'Корпусы'  # отображение названия в админке
        ordering = ('title',)

    def __str__(self):
        return self.title

    # self ссылка на ЭК модели. Через self обращаемся к нужному атрибуту для формирования динамического url и
    # использования в шаблонах.
    def get_absolute_url(self):
        return reverse('shop:frame_detail', args=[self.category.slug,
                                                  self.slug])


class Product(models.Model):
    """Модель квартир"""
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    frame = models.ForeignKey(Frame, verbose_name='Корпус', on_delete=models.CASCADE, null=True)
    floors = models.IntegerField(verbose_name='Этажность', validators=[MaxValueValidator(50), MinValueValidator(1)],
                                 null=True)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    area = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Площадь', null=True)
    image = models.ImageField(verbose_name='Изображение')
    price = models.IntegerField(verbose_name='Цена')
    available = models.BooleanField(default=True, verbose_name='Доступность')
    article = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Артикул', null=True)

    class Meta:
        verbose_name = 'Квартиры'  # отображение названия в админке
        verbose_name_plural = 'Квартиры'  # отображение названия в админке
        ordering = ('title',)

    def __str__(self):
        return self.title

    # self ссылка на ЭК модели. Через self обращаемся к нужному атрибуту для формирования динамического url и
    # использования в шаблонах.
    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.category.slug,
                                                    self.slug])  # c помощью reverse формируем маршурут с именем
        # shop:product_detail, для этого дополнитнительно  передаем нужные параметры


class Review(models.Model):
    """Модель отзывов."""
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE, verbose_name='Продукт')
    author = models.CharField(max_length=50, verbose_name='Автор')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='Рейтинг')
    text = models.TextField(blank=True, verbose_name='Текст')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ('-created',)

    def save(self, *args, **kwargs):
        if self.rating > 5 or self.rating < 1:
            raise ValidationError("Неверный рейтинг")
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Добавьте дополнительные поля профиля, если необходимо
    # ...

    def __str__(self):
        return self.user.username
