from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q, F
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
import datetime
from dateutil.relativedelta import relativedelta
from .models import Dues, ApartmentDues, Expense, Payment
from buildings.models import Building, Apartment
from users.models import User
from notifications.models import create_notification, NotificationGroup

# Admin Views
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class DuesListView(AdminRequiredMixin, ListView):
    model = ApartmentDues
    template_name = 'payments/dues_list.html'
    context_object_name = 'apartment_dues_list'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ApartmentDues.objects.all().select_related(
            'dues', 'apartment', 'apartment__building', 'apartment__resident'
        )
        
        # Filtreleme işlemleri
        building_id = self.request.GET.get('building')
        status = self.request.GET.get('status')
        date_range = self.request.GET.get('date_range')
        
        if building_id:
            queryset = queryset.filter(apartment__building_id=building_id)
            
        if status:
            queryset = queryset.filter(status=status)
            
        if date_range:
            try:
                # "01/07/2023 - 03/07/2023" formatından tarihleri ayır
                start_str, end_str = date_range.split(' - ')
                start_date = datetime.datetime.strptime(start_str, '%d/%m/%Y').date()
                end_date = datetime.datetime.strptime(end_str, '%d/%m/%Y').date()
                queryset = queryset.filter(dues__due_date__range=[start_date, end_date])
            except (ValueError, IndexError):
                # Tarih ayrıştırma hatası durumunda varsayılan olarak son 3 ay
                end_date = timezone.now().date()
                start_date = end_date - relativedelta(months=3)
                queryset = queryset.filter(dues__due_date__range=[start_date, end_date])
        
        return queryset.order_by('-dues__year', '-dues__month', 'apartment__building', 'apartment__block', 'apartment__number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Tüm binaları ekle
        context['buildings'] = Building.objects.all()
        
        # Seçili filtreler
        context['selected_building'] = self.request.GET.get('building')
        context['selected_status'] = self.request.GET.get('status')
        context['date_range'] = self.request.GET.get('date_range')
        
        # İstatistikler
        queryset = self.get_queryset()
        context['total_amount'] = queryset.aggregate(total=Sum('amount'))['total'] or 0
        context['paid_amount'] = queryset.aggregate(total=Sum('paid_amount'))['total'] or 0
        context['unpaid_amount'] = context['total_amount'] - context['paid_amount']
        context['late_fee_amount'] = queryset.aggregate(total=Sum('late_fee'))['total'] or 0
        
        return context

class DuesDetailView(AdminRequiredMixin, DetailView):
    model = Dues
    template_name = 'payments/dues_detail.html'
    context_object_name = 'dues'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['apartment_dues'] = ApartmentDues.objects.filter(dues=self.object).select_related('apartment')
        
        # İstatistikler
        apartment_dues = context['apartment_dues']
        context['total_amount'] = apartment_dues.aggregate(total=Sum('amount'))['total'] or 0
        context['paid_amount'] = apartment_dues.aggregate(total=Sum('paid_amount'))['total'] or 0
        context['unpaid_amount'] = context['total_amount'] - context['paid_amount']
        context['payment_rate'] = (context['paid_amount'] / context['total_amount'] * 100) if context['total_amount'] > 0 else 0
        context['late_fee_amount'] = apartment_dues.aggregate(total=Sum('late_fee'))['total'] or 0
        
        # Ödeme durumu analizi
        context['paid_count'] = apartment_dues.filter(status='paid').count()
        context['unpaid_count'] = apartment_dues.filter(status='unpaid').count()
        context['partial_count'] = apartment_dues.filter(status='partial').count()
        context['overdue_count'] = apartment_dues.filter(status='overdue').count()
        
        return context

class DuesCreateView(AdminRequiredMixin, CreateView):
    model = Dues
    template_name = 'payments/dues_form.html'
    fields = ['building', 'amount', 'month', 'year', 'due_date', 'late_fee_percentage', 'description']
    success_url = reverse_lazy('dues_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Bildirim grubunu al veya oluştur
        notification_group, created = NotificationGroup.objects.get_or_create(
            category=NotificationGroup.PAYMENT,
            building=form.instance.building,
            defaults={'name': f"{form.instance.building.name} Aidat Bildirimleri"}
        )
        
        # Tüm daire sakinlerine bildirim gönder
        apartments = form.instance.building.apartments.filter(is_occupied=True).select_related('resident')
        for apartment in apartments:
            if apartment.resident:
                create_notification(
                    user=apartment.resident,
                    title="Yeni Aidat Tanımlandı",
                    message=f"{form.instance.month}/{form.instance.year} dönemi aidatı {form.instance.amount}₺ olarak tanımlandı. Son ödeme tarihi: {form.instance.due_date}",
                    notification_type='info',
                    group=notification_group,
                    apartment=apartment
                )
        
        messages.success(self.request, 'Aidat başarıyla oluşturuldu ve daire sakinlerine bildirimler gönderildi.')
        return response

class DuesUpdateView(AdminRequiredMixin, UpdateView):
    model = Dues
    template_name = 'payments/dues_form.html'
    fields = ['building', 'amount', 'month', 'year', 'due_date', 'late_fee_percentage', 'description']
    success_url = reverse_lazy('dues_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Daire aidatlarını güncelle
        for apartment_dues in ApartmentDues.objects.filter(dues=self.object):
            apartment_dues.amount = form.instance.amount
            apartment_dues.due_date = form.instance.due_date
            apartment_dues.save()
        
        # Bildirim grubu
        notification_group, created = NotificationGroup.objects.get_or_create(
            category=NotificationGroup.PAYMENT,
            building=form.instance.building,
            defaults={'name': f"{form.instance.building.name} Aidat Bildirimleri"}
        )
        
        # Bildirim gönder
        apartments = form.instance.building.apartments.filter(is_occupied=True).select_related('resident')
        for apartment in apartments:
            if apartment.resident:
                create_notification(
                    user=apartment.resident,
                    title="Aidat Bilgisi Güncellendi",
                    message=f"{form.instance.month}/{form.instance.year} dönemi aidatı {form.instance.amount}₺ olarak güncellendi. Son ödeme tarihi: {form.instance.due_date}",
                    notification_type='warning',
                    group=notification_group,
                    apartment=apartment
                )
                
        messages.success(self.request, 'Aidat başarıyla güncellendi ve daire sakinlerine bildirimler gönderildi.')
        return response

class ApartmentDuesDetailView(AdminRequiredMixin, DetailView):
    model = ApartmentDues
    template_name = 'payments/apartment_dues_detail.html'
    context_object_name = 'apartment_dues'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments'] = Payment.objects.filter(apartment_dues=self.object).order_by('-payment_date')
        return context

class RecordPaymentView(AdminRequiredMixin, CreateView):
    model = Payment
    template_name = 'payments/record_payment.html'
    fields = ['amount', 'payment_method', 'payment_date', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        apartment_dues_id = self.kwargs.get('pk')
        context['apartment_dues'] = get_object_or_404(ApartmentDues, pk=apartment_dues_id)
        return context
    
    def form_valid(self, form):
        apartment_dues_id = self.kwargs.get('pk')
        apartment_dues = get_object_or_404(ApartmentDues, pk=apartment_dues_id)
        
        form.instance.apartment_dues = apartment_dues
        form.instance.recorded_by = self.request.user
        
        # Ödeme miktarını kaydet ve ApartmentDues'u güncelle
        apartment_dues.paid_amount += form.instance.amount
        
        # Durumunu güncelle
        if apartment_dues.paid_amount >= apartment_dues.amount:
            apartment_dues.status = ApartmentDues.PAID
            apartment_dues.last_payment_date = form.instance.payment_date
        elif apartment_dues.paid_amount > 0:
            apartment_dues.status = ApartmentDues.PARTIAL
            apartment_dues.last_payment_date = form.instance.payment_date
        
        apartment_dues.save()
        
        # Sahibine bildirim gönder
        if apartment_dues.apartment.resident:
            create_notification(
                user=apartment_dues.apartment.resident,
                title="Aidat Ödemesi Alındı",
                message=f"{apartment_dues.dues.month}/{apartment_dues.dues.year} dönemi için {form.instance.amount}₺ ödeme kaydedildi.",
                notification_type='success',
                apartment=apartment_dues.apartment
            )
        
        messages.success(self.request, f'{form.instance.amount}₺ tutarında ödeme başarıyla kaydedildi.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('apartment_dues_detail', kwargs={'pk': self.kwargs.get('pk')})

class ExpenseListView(AdminRequiredMixin, ListView):
    model = Expense
    template_name = 'payments/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Expense.objects.all().select_related('building', 'created_by')
        
        # Filtreleme
        building_id = self.request.GET.get('building')
        category = self.request.GET.get('category')
        date_range = self.request.GET.get('date_range')
        
        if building_id:
            queryset = queryset.filter(building_id=building_id)
            
        if category:
            queryset = queryset.filter(category=category)
            
        if date_range:
            try:
                start_str, end_str = date_range.split(' - ')
                start_date = datetime.datetime.strptime(start_str, '%d/%m/%Y').date()
                end_date = datetime.datetime.strptime(end_str, '%d/%m/%Y').date()
                queryset = queryset.filter(expense_date__range=[start_date, end_date])
            except (ValueError, IndexError):
                end_date = timezone.now().date()
                start_date = end_date - relativedelta(months=3)
                queryset = queryset.filter(expense_date__range=[start_date, end_date])
        
        return queryset.order_by('-expense_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Tüm binaları ekle
        context['buildings'] = Building.objects.all()
        context['categories'] = dict(Expense.CATEGORY_CHOICES)
        
        # Seçili filtreler
        context['selected_building'] = self.request.GET.get('building')
        context['selected_category'] = self.request.GET.get('category')
        context['date_range'] = self.request.GET.get('date_range')
        
        # İstatistikler
        queryset = self.get_queryset()
        context['total_expense'] = queryset.aggregate(total=Sum('amount'))['total'] or 0
        
        # Kategori bazlı harcamalar
        category_expenses = {}
        for category, name in Expense.CATEGORY_CHOICES:
            category_expenses[category] = queryset.filter(category=category).aggregate(total=Sum('amount'))['total'] or 0
        
        context['category_expenses'] = category_expenses
        
        return context

def export_dues_excel(request):
    """Export dues to Excel format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dues_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Bina', 'Blok', 'Daire No', 'Dönem', 'Tutar', 'Ödenen', 'Son Ödeme Tarihi', 'Durumu', 'Gecikme Bedeli'])
    
    # Filtrele
    queryset = ApartmentDues.objects.all().select_related('dues', 'apartment', 'apartment__building')
    
    building_id = request.GET.get('building')
    status = request.GET.get('status')
    date_range = request.GET.get('date_range')
    
    if building_id:
        queryset = queryset.filter(apartment__building_id=building_id)
        
    if status:
        queryset = queryset.filter(status=status)
        
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_date = datetime.datetime.strptime(start_str, '%d/%m/%Y').date()
            end_date = datetime.datetime.strptime(end_str, '%d/%m/%Y').date()
            queryset = queryset.filter(dues__due_date__range=[start_date, end_date])
        except:
            pass
    
    for dues in queryset:
        status_text = {
            'unpaid': 'Ödenmedi',
            'paid': 'Ödendi',
            'partial': 'Kısmi Ödendi',
            'overdue': 'Gecikti'
        }.get(dues.status, dues.status)
        
        writer.writerow([
            dues.apartment.building.name,
            dues.apartment.block or '',
            dues.apartment.number,
            f"{dues.dues.month}/{dues.dues.year}",
            dues.amount,
            dues.paid_amount,
            dues.due_date,
            status_text,
            dues.late_fee
        ])
    
    return response

def export_dues_pdf(request):
    """Export dues to PDF format"""
    # PDF kütüphanesi kullanılarak gerçekleştirilebilir
    # Şimdilik aynı excel çıktısını döndürelim
    return export_dues_excel(request)
