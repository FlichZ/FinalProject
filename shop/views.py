from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from loguru import logger

from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, FormView, DetailView, DeleteView, UpdateView
from .forms import RegisterUserForm, LoginUserForm, FeedbackForm, ReviewForm, ProductForm, CategoryForm, TagForm
from .models import *
from .permissions import IsStaffOrReadOnly
from .serializers import FiltersSerializer, CategorySerializer, TagSerializer, ProductSerializer, ReviewSerializer
from .utils import DataMixin
from cart.forms import CartAddProductForm
from rest_framework import viewsets

logger.add("debug.log", format="{time} {level} {message}", level="DEBUG", rotation="10 MB")


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


def is_employee(user):
    return user.is_staff


class ShopHome(DataMixin, ListView):
    model = Product
    template_name = 'shop/product/list.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = Filters.objects.all()
        selected_tags = self.request.GET.getlist('tag')
        if selected_tags:
            # Получаем теги, связанные с товарами на текущей странице
            tags_on_page = Tag.objects.filter(product__in=context['products']).distinct()
        else:
            tags_on_page = Tag.objects.all()

        # Добавляем теги в контекст, сгруппированные по фильтру
        tags_by_filter = {}
        for f in filters:
            tags_by_filter[f.name] = tags_on_page.filter(filters=f)

        context['tags_by_filter'] = tags_by_filter

        # Определяем уникальные фильтры и проверяем, есть ли только один товар
        unique_filters = set()
        for product in context['products']:
            unique_filters.update(product.tags.values_list('filters__name', flat=True))

        context['unique_filters'] = unique_filters
        if selected_tags:
            context['hide_filter_panel'] = len(context['products']) <= 1 or len(unique_filters) == 1

        # Определяем фильтры, в которых теги полностью соответствуют тегам у всех товаров
        matched_filters = set(tags_by_filter.keys())
        for filter_name, tags in tags_by_filter.items():
            for product in context['products']:
                product_tags = set(product.tags.filter(filters__name=filter_name))
                if product_tags != set(tags):
                    matched_filters.discard(filter_name)
                    break

        context['matched_filters'] = matched_filters

        # Если выбраны теги, фильтруем товары
        if selected_tags:
            # Фильтр для товаров с выбранными тегами
            tagged_products = Product.objects.filter(tags__id__in=selected_tags).distinct()

            # Фильтруем товары, чтобы оставить только те, которые содержат все выбранные теги
            for tag_id in selected_tags:
                tagged_products = tagged_products.filter(tags__id=tag_id)

            context['products'] = tagged_products

            # Скрываем панель тегов, если выбран только один товар
            context['hide_filter_panel'] = len(tagged_products) <= 1

        # Передаем выбранные теги в контекст
        context['selected_tags'] = selected_tags
        context['selected_tags_objects'] = Tag.objects.filter(id__in=selected_tags)
        context['remove_tag'] = self.remove_tag
        all_tags = Tag.objects.all()

        context['all_tags'] = all_tags
        return context

    def post(self, request, *args, **kwargs):
        tag_id = request.POST.get('tag_id')
        if tag_id:
            selected_tags = request.session.get('selected_tags', [])
            tag = Tag.objects.get(id=tag_id)  # Получаем объект тега
            if tag_id in selected_tags:
                selected_tags.remove(tag_id)
                request.session['selected_tags'] = selected_tags
        return redirect(request.path)

    def get_queryset(self):
        queryset = super().get_queryset()
        selected_tags = self.request.GET.getlist('tag')

        if selected_tags:
            queryset = queryset.filter(tags__id__in=selected_tags)

            # Сохраняем выбранные теги в сессии
            self.request.session['selected_tags'] = selected_tags

        return queryset

    def remove_tag(self, tag):
        selected_tags = self.request.session.get('selected_tags', [])
        if tag.id in selected_tags:
            selected_tags.remove(tag.id)
            self.request.session['selected_tags'] = selected_tags


class ProductCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product/crud/add_product_view.html'
    success_url = reverse_lazy('shop:product_list')


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product/crud/update_product.html'
    success_url = reverse_lazy('shop:product_list')


class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'shop/product/crud/delete_product.html'
    success_url = reverse_lazy('shop:product_list')

    def delete(self, request, *args, **kwargs):
        # Логическое удаление
        self.object = self.get_object()
        self.object.available = False
        self.object.save()
        return redirect(self.success_url)


class ProductDetailView(DataMixin, DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'shop/product/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        context['review_form'] = ReviewForm()
        context['cart_product_form'] = CartAddProductForm()
        context = self.get_user_context(**context)
        return context

    def post(self, request, category_slug, slug):
        product = self.get_object()
        review_form = ReviewForm(request.POST)

        if review_form.is_valid():
            cleaned_form = review_form.cleaned_data
            author_name = "Анонимный пользователь"
            Review.objects.create(
                product=product,
                author=author_name,
                rating=cleaned_form['rating'],
                text=cleaned_form['text']
            )
            return redirect('shop:product_detail', category_slug=category_slug, slug=slug)

        context = self.get_context_data()
        context['review_form'] = review_form
        return self.render_to_response(context)


class ShopCategory(DataMixin, ListView):
    model = Product
    template_name = 'shop/product/list.html'
    context_object_name = 'products'
    allow_empty = False  # генерация ошибки 404 если  нет товаров в категории

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = str(context['products'][0].category)
        return dict(list(context.items()))

    def get_queryset(self):
        return Product.objects.filter(category__slug=self.kwargs['category_slug'])


class RegisterUser(DataMixin, CreateView):
    form_class = RegisterUserForm
    template_name = 'shop/product/register.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_context = self.get_user_context(title='Регистрация')
        context['form_first'] = RegisterUser.form_class
        return dict(list(context.items()) + list(user_context.items()))

    def form_valid(self, form):
        """Встроенный метод который вызывается при успешной регистрации.
        Нужен чтобы зарегистрированного пользователя автоматически авторизовывали.
        Отличие от атрибута success_url в том, что через переменную мы не можем
        после успешной регистрации сразу авторизовать, а также  переменную можно только статический
        адрес указать. Если ссылка формируется динамически - только метод подойдет.
        К примеру, Если я например делаю сайт, где у зарегистрированного пользователя
        есть личная страница,  и я хочу что бы она была по адресу mysite/accounts/<никнейм пользователя>"""
        user = form.save()  # самостоятельно сохраняем пользователя в нашу модель в БД.
        login(self.request, user)  # функция для авторизации пользователя
        return redirect('shop:product_list')


class LoginUser(DataMixin, LoginView):
    form_class = LoginUserForm  # тут мы указываем свою кастомную форму. Изначально пользовались встроенной - класс AutenticationForm
    template_name = 'shop/product/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user_context = self.get_user_context(title='Войти')
        return dict(list(context.items()) + list(user_context.items()))

    def get_success_url(self):
        return reverse_lazy('shop:product_list')


class FeedbackFormView(DataMixin, FormView):
    form_class = FeedbackForm
    template_name = 'shop/product/feedback.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user_context = self.get_user_context(title='Обратная связь')
        context['form_feedback'] = FeedbackFormView.form_class
        return dict(list(context.items()) + list(user_context.items()))

    def form_valid(self, form):
        logger.debug(form.cleaned_data)  # если форма заполнена корректно, то при отправке логируем данные из формы
        return redirect('shop:product_list')


def about(request):
    return render(request, 'shop/product/about.html')


def logout_user(request):
    logout(request)  # стандартная ф-ия Джанго для выхода из авторизации
    return redirect('shop:login')


@user_passes_test(is_employee, login_url='/')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('shop:product_list')  # Замените 'shop:product_list' на URL вашего списка товаров
    else:
        form = ProductForm()

    return render(request, 'shop/product/add_product.html', {'form': form})


@user_passes_test(is_employee, login_url='/')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shop:category_list')  # Исправьте на имя вашего списка категорий
    else:
        form = CategoryForm()

    return render(request, 'shop/product/add_category.html', {'form': form})


# Классы для модели Tag
class TagCreateView(StaffRequiredMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = 'shop/product/crud/tag_form.html'
    success_url = reverse_lazy('shop:product_list')


class FiltersViewSet(viewsets.ModelViewSet):
    queryset = Filters.objects.all()
    serializer_class = FiltersSerializer
    permission_classes = [IsStaffOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsStaffOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsStaffOrReadOnly]
