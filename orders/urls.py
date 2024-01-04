from django.urls import path, include
from rest_framework import routers

from .views import order_create, OrderListView, OrderDetailView, OrderCreateView, OrderUpdateView, OrderDeleteView, OrderViewSet, OrderItemViewSet

router = routers.DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)

app_name = 'orders'

urlpatterns = [
    path('create/', order_create, name='order_create_default'),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/new/', OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/edit/', OrderUpdateView.as_view(), name='order_edit'),
    path('orders/<int:pk>/delete/', OrderDeleteView.as_view(), name='order_delete'),
    path('api/', include(router.urls)),

]
