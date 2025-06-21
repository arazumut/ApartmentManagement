from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from buildings.models import Building, Apartment
from users.models import User


class Dues(models.Model):
    """Monthly dues for the building"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='dues')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    month = models.PositiveSmallIntegerField(_('month'))
    year = models.PositiveSmallIntegerField(_('year'))
    due_date = models.DateField(_('due date'))
    late_fee_percentage = models.DecimalField(_('late fee percentage'), max_digits=5, decimal_places=2, default=Decimal('1.50'))
    description = models.TextField(_('description'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_dues')
    
    def __str__(self):
        return f"{self.building.name} - {self.month}/{self.year} - {self.amount}₺"
    
    class Meta:
        verbose_name = _('Dues')
        verbose_name_plural = _('Dues')
        unique_together = ['building', 'month', 'year']
        ordering = ['-year', '-month']
    
    def save(self, *args, **kwargs):
        # Auto-generate due date if not provided
        if not self.due_date:
            self.due_date = timezone.datetime(self.year, self.month, 5).date()
            
            # If creating dues for past month, set due date to 5 days from now
            if self.due_date < timezone.now().date():
                self.due_date = timezone.now().date() + timezone.timedelta(days=5)
        
        super().save(*args, **kwargs)
        
        # Create individual apartment dues
        apartments = Apartment.objects.filter(building=self.building)
        for apartment in apartments:
            ApartmentDues.objects.get_or_create(
                dues=self,
                apartment=apartment,
                defaults={
                    'amount': self.amount,
                    'due_date': self.due_date
                }
            )


class ApartmentDues(models.Model):
    """Individual apartment dues derived from the building dues"""
    UNPAID = 'unpaid'
    PAID = 'paid'
    PARTIAL = 'partial'
    OVERDUE = 'overdue'
    
    STATUS_CHOICES = (
        (UNPAID, _('Unpaid')),
        (PAID, _('Paid')),
        (PARTIAL, _('Partially Paid')),
        (OVERDUE, _('Overdue')),
    )
    
    dues = models.ForeignKey(Dues, on_delete=models.CASCADE, related_name='apartment_dues')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='dues')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(_('paid amount'), max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(_('due date'))
    status = models.CharField(_('status'), max_length=10, choices=STATUS_CHOICES, default=UNPAID)
    late_fee = models.DecimalField(_('late fee'), max_digits=10, decimal_places=2, default=0)
    last_payment_date = models.DateField(_('last payment date'), null=True, blank=True)
    
    def __str__(self):
        return f"{self.apartment} - {self.dues.month}/{self.dues.year} - {self.status}"
    
    class Meta:
        verbose_name = _('Apartment Dues')
        verbose_name_plural = _('Apartment Dues')
        unique_together = ['dues', 'apartment']
    
    def save(self, *args, **kwargs):
        # Update status based on payment
        if self.paid_amount >= self.amount:
            self.status = self.PAID
        elif self.paid_amount > 0:
            self.status = self.PARTIAL
        elif timezone.now().date() > self.due_date:
            self.status = self.OVERDUE
            
            # Calculate late fee
            days_late = (timezone.now().date() - self.due_date).days
            if days_late > 0:
                monthly_rate = self.dues.late_fee_percentage / 100
                months_late = days_late // 30
                self.late_fee = self.amount * monthly_rate * months_late
        else:
            self.status = self.UNPAID
            
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment records for dues"""
    CASH = 'cash'
    BANK_TRANSFER = 'bank_transfer'
    CREDIT_CARD = 'credit_card'
    OTHER = 'other'
    
    PAYMENT_METHOD_CHOICES = (
        (CASH, _('Cash')),
        (BANK_TRANSFER, _('Bank Transfer')),
        (CREDIT_CARD, _('Credit Card')),
        (OTHER, _('Other')),
    )
    
    apartment_dues = models.ForeignKey(ApartmentDues, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    payment_date = models.DateField(_('payment date'), default=timezone.now)
    payment_method = models.CharField(_('payment method'), max_length=20, choices=PAYMENT_METHOD_CHOICES, default=CASH)
    transaction_id = models.CharField(_('transaction ID'), max_length=100, blank=True, null=True)
    receipt_image = models.ImageField(_('receipt image'), upload_to='receipts/', blank=True, null=True)
    notes = models.TextField(_('notes'), blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.apartment_dues.apartment} - {self.amount}₺ - {self.payment_date}"
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-payment_date']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update the apartment dues with this payment
        apartment_dues = self.apartment_dues
        apartment_dues.paid_amount += self.amount
        apartment_dues.last_payment_date = self.payment_date
        apartment_dues.save()


class Expense(models.Model):
    """Building expenses"""
    UTILITIES = 'utilities'
    MAINTENANCE = 'maintenance'
    REPAIR = 'repair'
    SALARY = 'salary'
    CLEANING = 'cleaning'
    INSURANCE = 'insurance'
    OTHER = 'other'
    
    CATEGORY_CHOICES = (
        (UTILITIES, _('Utilities')),
        (MAINTENANCE, _('Maintenance')),
        (REPAIR, _('Repair')),
        (SALARY, _('Salary')),
        (CLEANING, _('Cleaning')),
        (INSURANCE, _('Insurance')),
        (OTHER, _('Other')),
    )
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(_('title'), max_length=255)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    category = models.CharField(_('category'), max_length=20, choices=CATEGORY_CHOICES)
    expense_date = models.DateField(_('expense date'))
    invoice_number = models.CharField(_('invoice number'), max_length=50, blank=True, null=True)
    invoice_image = models.ImageField(_('invoice image'), upload_to='invoices/', blank=True, null=True)
    description = models.TextField(_('description'), blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.building.name} - {self.title} - {self.amount}₺"
    
    class Meta:
        verbose_name = _('Expense')
        verbose_name_plural = _('Expenses')
        ordering = ['-expense_date']
