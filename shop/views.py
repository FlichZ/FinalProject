from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Min, Count, Q
from loguru import logger
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, FormView, DetailView, DeleteView, UpdateView

from orders.models import OrderItem, Order
from .forms import RegisterUserForm, LoginUserForm, FeedbackForm, ReviewForm, ProductForm, CategoryForm, TagForm, \
    UserProfileForm, ObjectFilterForm
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
    model = Object
    template_name = 'shop/product/list.html'
    context_object_name = 'objects'

    def get_queryset(self):
        # Получаем объекты, у которых есть неоплаченные квартиры
        objects_with_apartments = Object.objects.filter(frame__product__isnull=False).distinct() \
            .exclude(frame__product__order_items__order__paid=True)

        # Вычисляем минимальную цену квартиры для каждого объекта
        objects_with_min_price = []
        for obj in objects_with_apartments:
            min_price = Product.objects.filter(frame__object=obj).aggregate(Min('price'))['price__min']
            obj.min_price = min_price
            objects_with_min_price.append(obj)

        return objects_with_min_price

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем минимальные цены в контекст
        context['objects'] = context['objects']
        return context


class ObjectList(ListView):
    model = Object
    template_name = 'shop/product/project_list.html'
    context_object_name = 'objects'

    def get_queryset(self):
        form = ObjectFilterForm(self.request.GET)
        objects_with_apartments = Object.objects.filter(frame__product__isnull=False).distinct()

        if form.is_valid():
            category = form.cleaned_data.get('category')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')

            if category:
                objects_with_apartments = objects_with_apartments.filter(frame__product__category__slug=category)

            objects_with_apartments = objects_with_apartments.exclude(frame__product__order_items__order__paid=True)

            if min_price:
                objects_with_apartments = objects_with_apartments.filter(frame__product__price__gte=min_price)

            if max_price:
                objects_with_apartments = objects_with_apartments.filter(frame__product__price__lte=max_price)

        objects_with_min_price = []
        for obj in objects_with_apartments:
            min_price = obj.frame_set.first().product_set.filter(available=True).aggregate(min_price=Min('price'))[
                'min_price']
            obj.min_price = min_price
            objects_with_min_price.append(obj)

        return objects_with_min_price

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ObjectFilterForm(self.request.GET)
        return context


class SearchList(ListView):
    model = Product
    template_name = 'shop/product/search_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        # Извлекаем параметры из запроса
        category = self.request.GET.get('category')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        # Фильтруем продукты, исключая оплаченные и находящиеся в заказах
        products = Product.objects.exclude(order_items__order__paid=True) \
            .annotate(order_count=Count('order_items', filter=Q(order_items__order__paid=True))) \
            .exclude(order_count__gt=0)

        # Применяем фильтры, если они переданы в запросе
        if category:
            products = products.filter(category__slug=category)

        if min_price:
            products = products.filter(price__gte=min_price)

        if max_price:
            products = products.filter(price__lte=max_price)

        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавьте любую дополнительную логику контекста, если необходимо

        return context


class SearchListProject(ListView):
    template_name = 'shop/product/search_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        object_slug = self.kwargs['object_slug']
        current_object = get_object_or_404(Object, slug=object_slug)

        # Извлекаем параметры из запроса
        category = self.request.GET.get('category')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        # Фильтруем продукты по текущему объекту и условиям
        products = Product.objects.filter(frame__object=current_object) \
            .exclude(order_items__order__paid=True) \
            .annotate(order_count=Count('order_items', filter=Q(order_items__order__paid=True))) \
            .exclude(order_count__gt=0)

        # Применяем фильтры, если они переданы в запросе
        if category:
            products = products.filter(category__slug=category)

        if min_price:
            products = products.filter(price__gte=min_price)

        if max_price:
            products = products.filter(price__lte=max_price)

        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = Object.objects.filter(slug=self.kwargs['object_slug']).first()

        # Группировка продуктов по корпусам
        grouped_products = {}
        for product in context['products']:
            frame_number = product.frame.number
            if frame_number not in grouped_products:
                grouped_products[frame_number] = {'frame': product.frame, 'apartments': []}
            grouped_products[frame_number]['apartments'].append(product)

        # Преобразование словаря в список для удобства отображения в шаблоне
        context['grouped_products'] = list(grouped_products.values())

        return context


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


@login_required
def profile(request):
    user_profile = request.user

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'shop/profile/profile.html', {'form': form})


@login_required
def my_objects(request):
    # Получите все забронированные, но не оплаченные квартиры
    propertys = OrderItem.objects.filter(order__user=request.user, order__paid=True)
    return render(request, 'shop/profile/my_object.html', {'propertys': propertys})


@login_required
def booking(request):
    # Получите все забронированные, но не оплаченные квартиры
    bookings = OrderItem.objects.filter(order__user=request.user, order__paid=False)

    if request.method == 'POST':
        # Обработка оплаты
        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id)

        # Ваша логика оплаты
        order.paid = True
        order.save()

        messages.success(request, 'Заказ успешно оплачен.')

        return redirect('shop:profile')  # Измените на URL, который вам нужен

    return render(request, 'shop/profile/booking.html', {'bookings': bookings})
