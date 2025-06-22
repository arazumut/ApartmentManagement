from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from django.utils import timezone
from .models import Dues, ApartmentDues, Payment, Expense


class ApartmentDuesInline(TabularInline):
    model = ApartmentDues
    extra = 0
    readonly_fields = ('apartment', 'status', 'paid_amount', 'late_fee', 'last_payment_date')
    can_delete = False
    show_change_link = True


class PaymentInline(TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_date', 'amount', 'payment_method', 'created_by')
    can_delete = False
    show_change_link = True


@admin.register(Dues)
class DuesAdmin(ModelAdmin):
    list_display = ('building', 'month', 'year', 'amount', 'due_date', 'payment_status')
    list_filter = ('building', 'year', 'month')
    search_fields = ('building__name', 'description')
    readonly_fields = ('created_at', 'created_by')
    autocomplete_fields = ['building']
    
    fieldsets = (
        (None, {
            'fields': ('building', 'amount', 'month', 'year', 'due_date')
        }),
        (_('Additional Information'), {
            'fields': ('late_fee_percentage', 'description', 'created_at', 'created_by')
        }),
    )
    
    inlines = [ApartmentDuesInline]
    
    def payment_status(self, obj):
        total_apartments = obj.apartment_dues.count()
        paid_apartments = obj.apartment_dues.filter(status='paid').count()
        return f"{paid_apartments}/{total_apartments} ({(paid_apartments/total_apartments*100) if total_apartments else 0:.1f}%)"
    payment_status.short_description = _('Payment Status')
    
    def save_model(self, request, obj, form, change):
        if not change:  # if creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ApartmentDues)
class ApartmentDuesAdmin(ModelAdmin):
    list_display = ('apartment', 'dues_info', 'amount', 'paid_amount', 'due_date', 'status', 'late_fee')
    list_filter = ('status', 'dues__month', 'dues__year', 'apartment__building')
    search_fields = ('apartment__number', 'apartment__resident__first_name', 'apartment__resident__last_name')
    readonly_fields = ('late_fee', 'status', 'last_payment_date')
    autocomplete_fields = ['apartment', 'dues']
    
    fieldsets = (
        (None, {
            'fields': ('dues', 'apartment', 'amount', 'due_date')
        }),
        (_('Payment Information'), {
            'fields': ('paid_amount', 'status', 'late_fee', 'last_payment_date')
        }),
    )
    
    inlines = [PaymentInline]
    
    def dues_info(self, obj):
        return f"{obj.dues.month}/{obj.dues.year}"
    dues_info.short_description = _('Period')
    
    actions = ['mark_as_paid', 'calculate_late_fees']
    
    @admin.action(description=_("Mark selected dues as paid"))
    def mark_as_paid(self, request, queryset):
        for due in queryset:
            due.status = ApartmentDues.PAID
            due.paid_amount = due.amount
            due.last_payment_date = timezone.now().date()
            due.save()
        self.message_user(request, _("Selected dues have been marked as paid."))
    
    @admin.action(description=_("Calculate late fees"))
    def calculate_late_fees(self, request, queryset):
        updated = 0
        for due in queryset:
            if timezone.now().date() > due.due_date and due.status != ApartmentDues.PAID:
                due.save()  # The save method calculates late fees
                updated += 1
        self.message_user(request, _("Late fees calculated for {} dues.").format(updated))


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('apartment_info', 'amount', 'payment_date', 'payment_method', 'created_by')
    list_filter = ('payment_method', 'payment_date', 'apartment_dues__apartment__building')
    search_fields = ('apartment_dues__apartment__number', 'transaction_id', 'notes')
    readonly_fields = ('created_at', 'created_by')
    autocomplete_fields = ['apartment_dues']
    
    fieldsets = (
        (None, {
            'fields': ('apartment_dues', 'amount', 'payment_date')
        }),
        (_('Payment Details'), {
            'fields': ('payment_method', 'transaction_id', 'receipt_image')
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'created_at', 'created_by')
        }),
    )
    
    def apartment_info(self, obj):
        return f"{obj.apartment_dues.apartment} - {obj.apartment_dues.dues.month}/{obj.apartment_dues.dues.year}"
    apartment_info.short_description = _('Apartment/Period')
    
    def save_model(self, request, obj, form, change):
        if not change:  # if creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Expense)
class ExpenseAdmin(ModelAdmin):
    list_display = ('building', 'title', 'amount', 'category', 'expense_date', 'created_by')
    list_filter = ('category', 'expense_date', 'building')
    search_fields = ('title', 'description', 'invoice_number')
    readonly_fields = ('created_at', 'created_by')
    autocomplete_fields = ['building']
    
    fieldsets = (
        (None, {
            'fields': ('building', 'title', 'amount', 'category')
        }),
        (_('Expense Details'), {
            'fields': ('expense_date', 'invoice_number', 'invoice_image', 'description')
        }),
        (_('Record Information'), {
            'fields': ('created_at', 'created_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # if creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
