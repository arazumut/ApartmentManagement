from django.urls import path
from .views import (
    DuesListView, DuesDetailView, DuesCreateView, DuesUpdateView,
    ExpenseListView, ExpenseDetailView, ExpenseCreateView, ExpenseUpdateView,
    ResidentDuesListView, PayDuesView, FinancialReportView
)

urlpatterns = [
    # Admin routes
    path('dues/', DuesListView.as_view(), name='dues_list'),
    path('dues/<int:pk>/', DuesDetailView.as_view(), name='dues_detail'),
    path('dues/create/', DuesCreateView.as_view(), name='dues_create'),
    path('dues/<int:pk>/update/', DuesUpdateView.as_view(), name='dues_update'),
    
    path('expenses/', ExpenseListView.as_view(), name='expense_list'),
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense_detail'),
    path('expenses/create/', ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/update/', ExpenseUpdateView.as_view(), name='expense_update'),
    
    path('reports/', FinancialReportView.as_view(), name='financial_reports'),
    
    # Resident routes
    path('my-dues/', ResidentDuesListView.as_view(), name='resident_dues_list'),
    path('my-dues/<int:pk>/pay/', PayDuesView.as_view(), name='pay_dues'),
]
