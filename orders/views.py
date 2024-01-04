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


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':  # если форма первый раз отображается то метод будет None, и тогда мы перейдем в else для отображения новой формы
        form = OrderCreateForm(request.POST)
        # отправка данных на сервер
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            cart.clear_cart()
            send_mail('Заказ Оформлен',
                      'Войдите в админ панель, что бы просмотреть новый заказ.',
                      'zubastikbro915@gmail.com',
                      ['zubastikbro915@gmail.com'],
                      fail_silently=True)  # ошибка будет игнорироваться, программа продолжит работу
        return render(request, 'orders/created.html', {'order': order})
    else:
        form = OrderCreateForm()
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
