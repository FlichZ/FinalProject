from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import OrderItem, Order
from .forms import OrderCreateForm
from cart.views import *
from cart.cart_services import Cart
from rest_framework import viewsets
from .serializers import OrderSerializer, OrderItemSerializer
from .permissions import IsStaffOrReadOnly


@login_required
def order_create(request):
    cart = Cart(request)

    # Получение данных о пользователе из профиля или сеанса
    user_profile = request.user  # Предполагается, что у пользователя есть профиль

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)

            # Заполнение данных из профиля или сеанса
            order.user = request.user
            order.first_name = user_profile.first_name
            order.last_name = user_profile.last_name
            order.email = user_profile.email
            order.user = request.user
            # Добавьте другие поля по необходимости

            order.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )

            item['product'].available = False
            item['product'].save()

            cart.clear_cart()

            send_mail('Заказ оформлен',
                      'Войдите в админ-панель, чтобы просмотреть новый заказ.',
                      'zubastikbro915@gmail.com',
                      ['zubastikbro915@gmail.com'],
                      fail_silently=True)

            return render(request, 'orders/created.html', {'order': order})
    else:
        form = OrderCreateForm(instance=user_profile, initial={
            'first_name': user_profile.first_name,
            'last_name': user_profile.last_name,
            'email': user_profile.email,
            # Добавьте другие поля по необходимости
        })

    return render(request, 'orders/create.html', {'form': form})


class OrderListView(ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    permission_classes = [IsStaffOrReadOnly]


class OrderDetailView(DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    permission_classes = [IsStaffOrReadOnly]


class OrderCreateView(CreateView):
    model = Order
    template_name = 'orders/order_form.html'
    fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']
    success_url = reverse_lazy('shop:product_list')
    permission_classes = [IsStaffOrReadOnly]


class OrderUpdateView(UpdateView):
    model = Order
    template_name = 'orders/order_form.html'
    fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']
    success_url = reverse_lazy('orders:order_list')
    permission_classes = [IsStaffOrReadOnly]


class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'orders/order_confirm_delete.html'
    success_url = reverse_lazy('orders:order_list')
    permission_classes = [IsStaffOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsStaffOrReadOnly]


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsStaffOrReadOnly]
