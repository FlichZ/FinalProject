from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'filters', FiltersViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'products', ProductViewSet)
router.register(r'reviews', ReviewViewSet)

# используем namespacing для удобства. Теперь, к примеру, the product_list URL будет доступен, как shop:product_list в других частях Django проекта.
app_name = 'shop'

urlpatterns = [
        path('', ShopHome.as_view(), name='product_list'),
        path('projects/', ObjectList.as_view(), name='projects'),
        path('search/', SearchList.as_view(), name='search'),
        path('object/<slug:object_slug>/', SearchListProject.as_view(), name='search_list_project'),
        path('profile/', profile, name='profile'),
        path('property/', my_objects, name='property'),
        path('booking/', booking, name='booking'),
        path('category/<slug:category_slug>/', ShopCategory.as_view(), name='product_list_by_category'),
        path('category/<slug:category_slug>/<slug:slug>', ProductDetailView.as_view(), name='product_detail'),
        path('add_category/', add_category, name='add_category'),
        path('about/', about, name='about'),
        path('add_product/', add_product, name='add_product'),
        path('login/', LoginUser.as_view(), name='login'),
        path('accounts/login/', LoginUser.as_view(), name='login'),
        path('logout/', logout_user, name='logout'),
        path('register/', RegisterUser.as_view(), name='register'),
        path('product/add/', ProductCreateView.as_view(), name='add_product_view'),
        path('product/<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
        path('product/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
        path('tag/add/', TagCreateView.as_view(), name='tag_add'),
        path('api/', include(router.urls)),
    ]
