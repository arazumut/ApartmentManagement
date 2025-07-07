from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q, F, Count
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import csv
import datetime
from dateutil.relativedelta import relativedelta
from .models import Dues, ApartmentDues, Expense, Payment
from buildings.models import Building, Apartment
from users.models import User
from notifications.models import create_notification, NotificationGroup, send_building_notification

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
        
        # Enhanced filtering
        building_id = self.request.GET.get('building')
        status = self.request.GET.get('status')
        date_range = self.request.GET.get('date_range')
        search = self.request.GET.get('search')
        
        if building_id:
            queryset = queryset.filter(apartment__building_id=building_id)
            
        if status:
            queryset = queryset.filter(status=status)
            
        if search:
            queryset = queryset.filter(
                Q(apartment__apartment_number__icontains=search) |
                Q(apartment__resident__first_name__icontains=search) |
                Q(apartment__resident__last_name__icontains=search)
            )
            
        if date_range:
            try:
                start_str, end_str = date_range.split(' - ')
                start_date = datetime.datetime.strptime(start_str, '%d/%m/%Y').date()
                end_date = datetime.datetime.strptime(end_str, '%d/%m/%Y').date()
                queryset = queryset.filter(due_date__range=[start_date, end_date])
            except ValueError:
                pass
                
        return queryset.order_by('-dues__year', '-dues__month', 'apartment__apartment_number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings'] = Building.objects.filter(admin=self.request.user)
        
        # Summary statistics
        queryset = self.get_queryset()
        context['summary'] = {
            'total_amount': queryset.aggregate(total=Sum('amount'))['total'] or 0,
            'paid_amount': queryset.aggregate(total=Sum('paid_amount'))['total'] or 0,
            'unpaid_count': queryset.filter(status__in=['unpaid', 'partial', 'overdue']).count(),
            'overdue_count': queryset.filter(status='overdue').count(),
        }
        
        return context


class DuesCreateView(AdminRequiredMixin, CreateView):
    model = Dues
    template_name = 'payments/dues_form.html'
    fields = ['building', 'amount', 'month', 'year', 'due_date', 'late_fee_percentage', 'description']
    success_url = reverse_lazy('payments:dues_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['building'].queryset = Building.objects.filter(admin=self.request.user)
        return form
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Send notifications to all residents
        building = form.instance.building
        notification_title = f"Yeni Aidat Duyurusu - {form.instance.month}/{form.instance.year}"
        notification_message = f"""
        {building.name} için {form.instance.month}/{form.instance.year} ayı aidatı belirlendi.
        Aidat tutarı: {form.instance.amount}₺
        Son ödeme tarihi: {form.instance.due_date.strftime('%d/%m/%Y')}
        """
        
        send_building_notification(
            building=building,
            title=notification_title,
            message=notification_message,
            notification_type='info',
            exclude_user=self.request.user
        )
        
        messages.success(self.request, 'Aidat başarıyla oluşturuldu ve tüm sakinlere bildirim gönderildi.')
        return response


class ExpenseListView(AdminRequiredMixin, ListView):
    model = Expense
    template_name = 'payments/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Expense.objects.all().select_related('building', 'created_by')
        
        # Filter by buildings managed by current admin
        admin_buildings = Building.objects.filter(admin=self.request.user)
        queryset = queryset.filter(building__in=admin_buildings)
        
        # Additional filtering
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
            except ValueError:
                pass
                
        return queryset.order_by('-expense_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings'] = Building.objects.filter(admin=self.request.user)
        context['categories'] = Expense.CATEGORY_CHOICES
        
        # Summary statistics
        queryset = self.get_queryset()
        context['total_expenses'] = queryset.aggregate(total=Sum('amount'))['total'] or 0
        
        # Monthly breakdown
        current_month = timezone.now().month
        current_year = timezone.now().year
        context['monthly_expenses'] = queryset.filter(
            expense_date__month=current_month,
            expense_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return context


class ExpenseCreateView(AdminRequiredMixin, CreateView):
    model = Expense
    template_name = 'payments/expense_form.html'
    fields = ['building', 'title', 'description', 'amount', 'category', 'expense_date', 'receipt']
    success_url = reverse_lazy('payments:expense_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['building'].queryset = Building.objects.filter(admin=self.request.user)
        return form
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Send notification to residents about major expenses
        if form.instance.amount > 1000:  # Major expense threshold
            building = form.instance.building
            notification_title = f"Büyük Gider Bildirimi - {form.instance.title}"
            notification_message = f"""
            {building.name} için büyük bir gider kaydedildi.
            Gider: {form.instance.title}
            Tutar: {form.instance.amount}₺
            Kategori: {form.instance.get_category_display()}
            Tarih: {form.instance.expense_date.strftime('%d/%m/%Y')}
            """
            
            send_building_notification(
                building=building,
                title=notification_title,
                message=notification_message,
                notification_type='info',
                exclude_user=self.request.user
            )
        
        messages.success(self.request, 'Gider başarıyla kaydedildi.')
        return response


class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    template_name = 'payments/payment_form.html'
    fields = ['apartment_dues', 'amount', 'payment_method', 'payment_date', 'description']
    success_url = reverse_lazy('payments:resident_payments')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Residents can only pay for their own apartments
        if self.request.user.is_resident:
            user_apartments = Apartment.objects.filter(
                Q(resident=self.request.user) | Q(owner=self.request.user)
            )
            form.fields['apartment_dues'].queryset = ApartmentDues.objects.filter(
                apartment__in=user_apartments,
                status__in=['unpaid', 'partial', 'overdue']
            )
        
        return form
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Send payment confirmation notification
        apartment_dues = form.instance.apartment_dues
        notification_title = "Ödeme Alındı"
        notification_message = f"""
        {apartment_dues.apartment} için ödemeniz alındı.
        Tutar: {form.instance.amount}₺
        Ödeme Yöntemi: {form.instance.get_payment_method_display()}
        Tarih: {form.instance.payment_date.strftime('%d/%m/%Y')}
        """
        
        create_notification(
            user=self.request.user,
            title=notification_title,
            message=notification_message,
            notification_type='success',
            apartment=apartment_dues.apartment
        )
        
        # Send notification to admin
        if apartment_dues.apartment.building.admin:
            admin_notification_title = f"Yeni Ödeme Alındı - {apartment_dues.apartment}"
            admin_notification_message = f"""
            {apartment_dues.apartment} için ödeme alındı.
            Tutar: {form.instance.amount}₺
            Ödeme Yöntemi: {form.instance.get_payment_method_display()}
            Ödeme Yapan: {self.request.user.get_full_name()}
            """
            
            create_notification(
                user=apartment_dues.apartment.building.admin,
                title=admin_notification_title,
                message=admin_notification_message,
                notification_type='info',
                apartment=apartment_dues.apartment
            )
        
        messages.success(self.request, 'Ödemeniz başarıyla kaydedildi.')
        return response


class ResidentPaymentsView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/resident_payments.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        user_apartments = Apartment.objects.filter(
            Q(resident=self.request.user) | Q(owner=self.request.user)
        )
        
        return Payment.objects.filter(
            apartment_dues__apartment__in=user_apartments
        ).select_related('apartment_dues', 'apartment_dues__apartment').order_by('-payment_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_apartments = Apartment.objects.filter(
            Q(resident=self.request.user) | Q(owner=self.request.user)
        )
        
        # Unpaid dues
        context['unpaid_dues'] = ApartmentDues.objects.filter(
            apartment__in=user_apartments,
            status__in=['unpaid', 'partial', 'overdue']
        ).select_related('dues', 'apartment')
        
        # Payment summary
        context['payment_summary'] = {
            'total_paid': self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0,
            'total_unpaid': context['unpaid_dues'].aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        return context


class SendPaymentReminderView(AdminRequiredMixin, TemplateView):
    """Send payment reminders to residents with unpaid dues"""
    template_name = 'payments/send_reminders.html'
    
    def post(self, request, *args, **kwargs):
        building_id = request.POST.get('building_id')
        reminder_type = request.POST.get('reminder_type', 'gentle')
        
        if not building_id:
            messages.error(request, 'Lütfen bir bina seçin.')
            return redirect('payments:send_reminders')
        
        building = get_object_or_404(Building, id=building_id, admin=request.user)
        
        # Get unpaid dues for the building
        unpaid_dues = ApartmentDues.objects.filter(
            apartment__building=building,
            status__in=['unpaid', 'partial', 'overdue']
        ).select_related('apartment', 'apartment__resident')
        
        # Send reminders
        reminder_count = 0
        for apartment_due in unpaid_dues:
            if apartment_due.apartment.resident:
                self._send_payment_reminder(apartment_due, reminder_type)
                reminder_count += 1
        
        messages.success(request, f'{reminder_count} adet ödeme hatırlatması gönderildi.')
        return redirect('payments:send_reminders')
    
    def _send_payment_reminder(self, apartment_due, reminder_type='gentle'):
        """Send payment reminder to resident"""
        resident = apartment_due.apartment.resident
        
        # Determine message tone based on reminder type
        if reminder_type == 'gentle':
            title = "Aidat Ödeme Hatırlatması"
            message = f"""
            Merhaba {resident.get_full_name()},
            
            {apartment_due.apartment} için {apartment_due.dues.month}/{apartment_due.dues.year} ayı aidatınız henüz ödenmemiş.
            
            Aidat tutarı: {apartment_due.amount}₺
            Son ödeme tarihi: {apartment_due.due_date.strftime('%d/%m/%Y')}
            
            Lütfen ödemenizi en kısa sürede yapınız.
            """
        elif reminder_type == 'urgent':
            title = "ACİL: Aidat Ödeme Hatırlatması"
            message = f"""
            Sayın {resident.get_full_name()},
            
            {apartment_due.apartment} için {apartment_due.dues.month}/{apartment_due.dues.year} ayı aidatınız vadesi geçmiş durumda.
            
            Aidat tutarı: {apartment_due.amount}₺
            Gecikme ücreti: {apartment_due.late_fee}₺
            Toplam: {apartment_due.amount + apartment_due.late_fee}₺
           