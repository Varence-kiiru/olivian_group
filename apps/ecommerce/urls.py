from django.urls import path
from . import views

app_name = 'ecommerce'

urlpatterns = [
    # Cart management
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.UpdateCartItemView.as_view(), name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/clear/', views.ClearCartView.as_view(), name='clear_cart'),
    path('cart/count/', views.CartCountView.as_view(), name='cart_count'),
    
    # Checkout and orders
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/<str:order_number>/pay/', views.ProcessPaymentView.as_view(), name='process_payment'),
    path('orders/<str:order_number>/receipt/', views.GenerateReceiptView.as_view(), name='generate_receipt'),
    path('orders/', views.OrderListView.as_view(), name='orders'),
    path('orders/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # M-Pesa endpoints
    path('mpesa/callback/', views.MPesaCallbackView.as_view(), name='mpesa_callback'),
    path('mpesa/status/<int:transaction_id>/', views.CheckTransactionStatusView.as_view(), name='check_transaction_status'),
    
    # Order tracking (Public)
    path('track/', views.OrderTrackingView.as_view(), name='track_order'),
    path('track/<str:order_number>/', views.OrderTrackingView.as_view(), name='track_order_direct'),
    path('api/track/<str:order_number>/', views.OrderTrackingAPIView.as_view(), name='api_track_order'),
    
    # Order management APIs (Management only)
    path('api/orders/', views.OrderManagementAPIView.as_view(), name='api_orders'),
    path('api/orders/<str:order_number>/status/', views.UpdateOrderStatusView.as_view(), name='update_order_status'),
    path('api/orders/<str:order_number>/history/', views.OrderStatusHistoryView.as_view(), name='order_status_history'),
]
