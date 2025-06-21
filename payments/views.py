from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from .models import Dues, ApartmentDues, Expense
from buildings.models import Building, Apartment
from users.models import User

# Admin Views
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class DuesListView(AdminRequiredMixin, ListView):
    model = Dues
    template_name = 'payments/dues_list.html'
    context_object_name = 'dues_list'
    
    def get_queryset(self):
        return Dues.objects.all().order_by('-year', '-month')

class DuesDetailView(AdminRequiredMixin, DetailView):
    model = Dues
    template_name = 'payments/dues_detail.html'
    context_object_name = 'dues'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['apartment_dues'] = ApartmentDues.objects.filter(dues=self.object)
        return context

class DuesCreateView(AdminRequiredMixin, CreateView):
    model = Dues
    template_name = 'payments/dues_form.html'
    fields = ['building', 'amount', 'month', 'year', 'due_date', 'late_fee_percentage', 'description']
    success_url = reverse_lazy('dues_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Aidat başarıyla oluşturuldu.')
        return super().form_valid(form)

class DuesUpdateView(AdminRequiredMixin, UpdateView):
    model = Dues
    template_name = 'payments/dues_form.html'
    fields = ['building', 'amount', 'month', 'year', 'due_date', 'late_fee_percentage', 'description']
    success_url = reverse_lazy('dues_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Aidat başarıyla güncellendi.')
        return super().form_valid(form)

class ExpenseListView(AdminRequiredMixin, ListView):
    model = Expense
    template_name = 'payments/expense_list.html'
    context_object_name = 'expenses'
    
    def get_queryset(self):
        return Expense.objects.all().order_by('-date')

class ExpenseDetailView(AdminRequiredMixin, DetailView):
    model = Expense
    template_name = 'payments/expense_detail.html'
    context_object_name = 'expense'

class ExpenseCreateView(AdminRequiredMixin, CreateView):
    model = Expense
    template_name = 'payments/expense_form.html'
    fields = ['building', 'title', 'category', 'amount', 'expense_date', 'description', 'invoice_number', 'invoice_image']
    success_url = reverse_lazy('expense_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Gider başarıyla oluşturuldu.')
        return super().form_valid(form)

class ExpenseUpdateView(AdminRequiredMixin, UpdateView):
    model = Expense
    template_name = 'payments/expense_form.html'
    fields = ['building', 'title', 'category', 'amount', 'expense_date', 'description', 'invoice_number', 'invoice_image']
    success_url = reverse_lazy('expense_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Gider başarıyla güncellendi.')
        return super().form_valid(form)

class FinancialReportView(AdminRequiredMixin, TemplateView):
    template_name = 'payments/financial_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        building_id = self.request.GET.get('building')
        start_date = self.request.GET.get('start_date', timezone.now().replace(day=1).date())
        end_date = self.request.GET.get('end_date', timezone.now().date())
        
        # Filter buildings
        buildings = Building.objects.all()
        if building_id:
            buildings = buildings.filter(id=building_id)
        
        # Get total income and expenses
        income_filter = Q(payment_date__range=[start_date, end_date])
        expense_filter = Q(expense_date__range=[start_date, end_date])
        
        if building_id:
            income_filter &= Q(apartment__building_id=building_id)
            expense_filter &= Q(building_id=building_id)
            
        total_income = ApartmentDues.objects.filter(income_filter, status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses = Expense.objects.filter(expense_filter).aggregate(Sum('amount'))['amount__sum'] or 0
        
        context.update({
            'buildings': buildings,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': total_income - total_expenses,
            'selected_building': building_id,
            'start_date': start_date,
            'end_date': end_date,
        })
        return context

# Resident Views
class ResidentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == User.RESIDENT

class ResidentDuesListView(ResidentRequiredMixin, ListView):
    model = ApartmentDues
    template_name = 'payments/resident_dues_list.html'
    context_object_name = 'dues_list'
    
    def get_queryset(self):
        user_apartments = Apartment.objects.filter(
            Q(owner=self.request.user) | Q(tenant=self.request.user)
        )
        return ApartmentDues.objects.filter(apartment__in=user_apartments).order_by('-dues__year', '-dues__month')

class PayDuesView(ResidentRequiredMixin, UpdateView):
    model = ApartmentDues
    template_name = 'payments/pay_dues.html'
    fields = ['payment_method', 'payment_reference']
    success_url = reverse_lazy('resident_dues_list')
    
    def get_queryset(self):
        user_apartments = Apartment.objects.filter(
            Q(owner=self.request.user) | Q(tenant=self.request.user)
        )
        return ApartmentDues.objects.filter(apartment__in=user_apartments)
    
    def form_valid(self, form):
        form.instance.status = 'paid'
        form.instance.payment_date = timezone.now().date()
        messages.success(self.request, 'Ödeme başarıyla kaydedildi.')
        return super().form_valid(form)
