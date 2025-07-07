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


class DuesDetailView(AdminRequiredMixin, DetailView):
    model = Dues
    template_name = 'payments/dues_detail.html'
    context_object_name = 'dues'
    
    def get_queryset(self):
        return Dues.objects.filter(building__admin=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dues = self.get_object()
        
        # Get apartment dues statistics
        apartment_dues = ApartmentDues.objects.filter(dues=dues)
        context['apartment_dues'] = apartment_dues
        context['total_apartments'] = apartment_dues.count()
        context['paid_apartments'] = apartment_dues.filter(is_paid=True).count()
        context['unpaid_apartments'] = apartment_dues.filter(is_paid=False).count()
        context['total_collected'] = apartment_dues.filter(is_paid=True).aggregate(
            total=Sum(F('amount') + F('late_fee'))
        )['total'] or 0
        context['total_expected'] = apartment_dues.aggregate(
            total=Sum(F('amount') + F('late_fee'))
        )['total'] or 0
        
        return context


class DuesUpdateView(AdminRequiredMixin, UpdateView):
    model = Dues
    template_name = 'payments/dues_form.html'
    fields = ['building', 'amount', 'month', 'year', 'due_date', 'late_fee_percentage', 'description']
    success_url = reverse_lazy('payments:dues_list')
    
    def get_queryset(self):
        return Dues.objects.filter(building__admin=self.request.user)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['building'].queryset = Building.objects.filter(admin=self.request.user)
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Aidat başarıyla güncellendi.')
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
    fields = ['building', 'title', 'description', 'amount', 'category', 'expense_date', 'receipt'
    ]
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


class ExpenseDetailView(AdminRequiredMixin, DetailView):
    model = Expense
    template_name = 'payments/expense_detail.html'
    context_object_name = 'expense'
    
    def get_queryset(self):
        return Expense.objects.filter(building__admin=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expense = self.get_object()
        
        # Add related expenses from the same building for context
        context['related_expenses'] = Expense.objects.filter(
            building=expense.building,
            category=expense.category
        ).exclude(id=expense.id).order_by('-expense_date')[:5]
        
        return context


class ExpenseUpdateView(AdminRequiredMixin, UpdateView):
    model = Expense
    template_name = 'payments/expense_form.html'
    fields = ['building', 'title', 'description', 'amount', 'category', 'expense_date', 'receipt']
    success_url = reverse_lazy('payments:expense_list')
    
    def get_queryset(self):
        return Expense.objects.filter(building__admin=self.request.user)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['building'].queryset = Building.objects.filter(admin=self.request.user)
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Gider başarıyla güncellendi.')
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


class ResidentDuesListView(LoginRequiredMixin, ListView):
    model = ApartmentDues
    template_name = 'payments/resident_dues_list.html'
    context_object_name = 'dues_list'
    paginate_by = 20
    
    def get_queryset(self):
        user_apartments = Apartment.objects.filter(
            Q(resident=self.request.user) | Q(owner=self.request.user)
        )
        
        return ApartmentDues.objects.filter(
            apartment__in=user_apartments
        ).select_related('dues', 'apartment').order_by('-dues__year', '-dues__month')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_apartments = Apartment.objects.filter(
            Q(resident=self.request.user) | Q(owner=self.request.user)
        )
        
        # Summary statistics
        all_dues = ApartmentDues.objects.filter(apartment__in=user_apartments)
        context['total_dues'] = all_dues.count()
        context['paid_dues'] = all_dues.filter(is_paid=True).count()
        context['unpaid_dues'] = all_dues.filter(is_paid=False).count()
        context['total_amount_paid'] = all_dues.filter(is_paid=True).aggregate(
            total=Sum(F('amount') + F('late_fee'))
        )['total'] or 0
        context['total_amount_unpaid'] = all_dues.filter(is_paid=False).aggregate(
            total=Sum(F('amount') + F('late_fee'))
        )['total'] or 0
        
        return context


class PayDuesView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/pay_dues.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the specific apartment dues
        apartment_dues = get_object_or_404(
            ApartmentDues, 
            pk=self.kwargs['pk'],
            apartment__in=Apartment.objects.filter(
                Q(resident=self.request.user) | Q(owner=self.request.user)
            )
        )
        
        context['apartment_dues'] = apartment_dues
        return context
    
    def post(self, request, *args, **kwargs):
        apartment_dues = get_object_or_404(
            ApartmentDues, 
            pk=self.kwargs['pk'],
            apartment__in=Apartment.objects.filter(
                Q(resident=request.user) | Q(owner=request.user)
            )
        )
        
        if apartment_dues.is_paid:
            messages.warning(request, 'Bu aidat zaten ödenmiş.')
            return redirect('payments:resident_dues_list')
        
        # Create payment record
        payment = Payment.objects.create(
            apartment_dues=apartment_dues,
            amount=apartment_dues.amount + apartment_dues.late_fee,
            payment_method='online',
            payment_date=timezone.now(),
            created_by=request.user,
            description=f'{apartment_dues.dues.month}/{apartment_dues.dues.year} ayı aidatı'
        )
        
        # Mark as paid
        apartment_dues.is_paid = True
        apartment_dues.paid_date = timezone.now()
        apartment_dues.save()
        
        # Send notification
        create_notification(
            user=request.user,
            title='Ödeme Onayı',
            message=f'{apartment_dues.apartment} için {apartment_dues.dues.month}/{apartment_dues.dues.year} ayı aidatı başarıyla ödendi.',
            notification_type='success',
            apartment=apartment_dues.apartment
        )
        
        messages.success(request, 'Ödemeniz başarıyla tamamlandı.')
        return redirect('payments:resident_dues_list')


class FinancialReportView(AdminRequiredMixin, TemplateView):
    template_name = 'payments/financial_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's buildings
        user_buildings = Building.objects.filter(admin=self.request.user)
        
        # Get date range from request
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')
        building_id = self.request.GET.get('building_id')
        
        # Set default date range (last 12 months)
        if not from_date:
            from_date = (timezone.now() - relativedelta(months=12)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = timezone.now().strftime('%Y-%m-%d')
        
        context['from_date'] = from_date
        context['to_date'] = to_date
        context['buildings'] = user_buildings
        context['selected_building'] = building_id
        
        # Filter data based on parameters
        dues_filter = Q(building__admin=self.request.user)
        expenses_filter = Q(building__admin=self.request.user)
        payments_filter = Q(apartment_dues__apartment__building__admin=self.request.user)
        
        if building_id:
            dues_filter &= Q(building_id=building_id)
            expenses_filter &= Q(building_id=building_id)
            payments_filter &= Q(apartment_dues__apartment__building_id=building_id)
        
        # Dues data
        dues_data = Dues.objects.filter(dues_filter).aggregate(
            total_expected=Sum('amount'),
            count=Count('id')
        )
        
        # Expenses data
        expenses_data = Expense.objects.filter(expenses_filter).filter(
            expense_date__range=[from_date, to_date]
        ).aggregate(
            total_expenses=Sum('amount'),
            count=Count('id')
        )
        
        # Payments data
        payments_data = Payment.objects.filter(payments_filter).filter(
            payment_date__range=[from_date, to_date]
        ).aggregate(
            total_collected=Sum('amount'),
            count=Count('id')
        )
        
        # Monthly breakdown
        monthly_data = []
        current_date = timezone.datetime.strptime(from_date, '%Y-%m-%d').date()
        end_date = timezone.datetime.strptime(to_date, '%Y-%m-%d').date()
        
        while current_date <= end_date:
            month_payments = Payment.objects.filter(payments_filter).filter(
                payment_date__year=current_date.year,
                payment_date__month=current_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            month_expenses = Expense.objects.filter(expenses_filter).filter(
                expense_date__year=current_date.year,
                expense_date__month=current_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_data.append({
                'month': current_date.strftime('%Y-%m'),
                'month_name': current_date.strftime('%B %Y'),
                'payments': month_payments,
                'expenses': month_expenses,
                'net': month_payments - month_expenses
            })
            
            current_date = current_date + relativedelta(months=1)
        
        context.update({
            'dues_data': dues_data,
            'expenses_data': expenses_data,
            'payments_data': payments_data,
            'monthly_data': monthly_data,
            'net_income': (payments_data['total_collected'] or 0) - (expenses_data['total_expenses'] or 0)
        })
        
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
            
            Lütfen ödemenizi derhal yapınız. Aksi takdirde yasal işlem başlatılacaktır.
            """
        
        # Send notification
        create_notification(
            user=resident,
            title=title,
            message=message,
            notification_type='warning' if reminder_type == 'urgent' else 'info',
            apartment=apartment_due.apartment
        )
           