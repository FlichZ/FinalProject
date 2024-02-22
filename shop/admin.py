from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Product, Category, Review, Tag, Filters, Object, Frame, UserProfile


class OrderReviewInline(admin.TabularInline):
    model = Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}  # cоздание слага на основе атрибута name


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'frame', 'floors', 'area', 'article', 'slug', 'price', 'available', 'get_html_photo']
    list_filter = ['available']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('title',)}  # cоздание слага на основе атрибута title
    search_fields = ['title']
    inlines = [OrderReviewInline]  # связываем отзывы с товарами

    #  метод для отображения миниатюр в админке
    def get_html_photo(self, object):  # object тут ссылается на запись из таблицы (ЭК модели Product)
        if object.image:
            return mark_safe(
                f"<img src='{object.image.url}' width=65>")  # ф-ия mark_safe позволяет не экранировать то, что мы в нее передаем

    get_html_photo.short_description = 'Миниатюра '


@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'description2', 'address', 'date', 'slug', 'available', 'get_html_photo']
    list_filter = ['available']
    list_editable = ['available']
    prepopulated_fields = {'slug': ('title',)}  # cоздание слага на основе атрибута title
    search_fields = ['title']

    #  метод для отображения миниатюр в админке
    def get_html_photo(self, object):  # object тут ссылается на запись из таблицы (ЭК модели Product)
        if object.image:
            return mark_safe(
                f"<img src='{object.image.url}' width=65>")  # ф-ия mark_safe позволяет не экранировать то, что мы в нее передаем

    get_html_photo.short_description = 'Миниатюра '


@admin.register(Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ['title', 'number', 'floors', 'slug']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user']
