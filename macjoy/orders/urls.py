from django.urls import path
from . import views

urlpatterns = [
    path('new/', views.new_order, name='new_order'),
    path('all/', views.attendant_orders, name='attendant_orders'),
    path('owner/', views.owner_orders, name='owner_orders'),
    path('clients/', views.clients, name='clients'),
    path('clients/<uuid:customer_id>/', views.client_detail, name='client_detail'),
    path('search-customer/', views.search_customer, name='search_customer'),
    path('detail/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('update/<uuid:order_id>/', views.update_order_status, name='update_order_status'),
    path('payment/<uuid:order_id>/', views.update_payment_status, name='update_payment_status'),
]