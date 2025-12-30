from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    # Budget URLs
    path('', views.BudgetListView.as_view(), name='list'),
    path('create/', views.BudgetCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BudgetDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='delete'),
    
    # Budget Category URLs
    path('categories/', views.BudgetCategoryListView.as_view(), name='category_list'),
    path('budget/<int:budget_id>/categories/', views.BudgetCategoryListView.as_view(), name='category_list'),
    path('budget/<int:budget_id>/categories/create/', views.BudgetCategoryCreateView.as_view(), name='category_create'),
    path('categories/create/', views.BudgetCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.BudgetCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.BudgetCategoryDeleteView.as_view(), name='category_delete'),
    
    # Payment Schedule URLs
    path('payment-schedules/', views.PaymentScheduleListView.as_view(), name='payment_schedule_list'),
    path('payment-schedules/create/', views.PaymentScheduleCreateView.as_view(), name='payment_schedule_create'),
    path('payment-schedules/<int:pk>/edit/', views.PaymentScheduleUpdateView.as_view(), name='payment_schedule_edit'),
    path('payment-schedules/<int:pk>/delete/', views.PaymentScheduleDeleteView.as_view(), name='payment_schedule_delete'),
    
    # Budget Approval URLs
    path('approvals/', views.BudgetApprovalListView.as_view(), name='approval_list'),
    path('approvals/<int:pk>/update/', views.BudgetApprovalUpdateView.as_view(), name='approval_update'),
    
    # Budget Revision URLs
    path('revisions/', views.BudgetRevisionListView.as_view(), name='revision_list'),
    path('revisions/create/', views.BudgetRevisionCreateView.as_view(), name='revision_create'),
    path('revisions/<int:pk>/approve/', views.BudgetRevisionUpdateView.as_view(), name='revision_approve'),
    
    # Expense Request URLs
    path('expense-requests/', views.ExpenseRequestListView.as_view(), name='expense_request_list'),
    path('expense-requests/create/', views.ExpenseRequestCreateView.as_view(), name='expense_request_create'),
    path('expense-requests/<int:pk>/edit/', views.ExpenseRequestUpdateView.as_view(), name='expense_request_edit'),
    path('expense-requests/<int:pk>/approve/', views.ExpenseRequestApprovalView.as_view(), name='expense_request_approve'),
    
    # Budget Report URLs
    path('reports/', views.BudgetReportListView.as_view(), name='report_list'),
    path('reports/create/', views.BudgetReportCreateView.as_view(), name='report_create'),
]
