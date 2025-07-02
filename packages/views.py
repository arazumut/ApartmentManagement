from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.http import HttpResponseForbidden
from .models import Package, Visitor
from buildings.models import Building, Apartment
from users.models import User
from .forms import PackageForm, PackageDeliveryForm, VisitorForm


@login_required
def package_list(request):
    """List all packages for caretakers"""
    if not request.user.is_caretaker and not request.user.is_admin:
        return HttpResponseForbidden("Bu sayfaya erişim izniniz yok.")
    
    # Get buildings where the user is caretaker
    if request.user.is_caretaker:
        buildings = Building.objects.filter(caretaker=request.user)
    else:  # Admin can see all
        buildings = Building.objects.all()
    
    packages = Package.objects.filter(building__in=buildings).order_by('-received_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        packages = packages.filter(status=status)
        
    # Filter by building if provided
    building_id = request.GET.get('building')
    if building_id:
        packages = packages.filter(building_id=building_id)
    
    context = {
        'packages': packages,
        'buildings': buildings,
    }
    return render(request, 'packages/package_list.html', context)


@login_required
def resident_package_list(request):
    """List packages for a resident"""
    if not request.user.is_resident:
        return HttpResponseForbidden("Bu sayfaya erişim izniniz yok.")
    
    # Get apartments where the user is resident or owner
    apartments = Apartment.objects.filter(Q(resident=request.user) | Q(owner=request.user))
    
    packages = Package.objects.filter(apartment__in=apartments).order_by('-received_at')
    
    context = {
        'packages': packages,
    }
    return render(request, 'packages/resident_package_list.html', context)


@login_required
def package_detail(request, pk):
    """View package details"""
    package = get_object_or_404(Package, pk=pk)
    
    # Check permissions
    if request.user.is_caretaker:
        if package.building.caretaker != request.user:
            return HttpResponseForbidden("Bu pakete erişim izniniz yok.")
    elif request.user.is_resident:
        apartments = Apartment.objects.filter(Q(resident=request.user) | Q(owner=request.user))
        if package.apartment not in apartments:
            return HttpResponseForbidden("Bu pakete erişim izniniz yok.")
    elif not request.user.is_admin:
        return HttpResponseForbidden("Bu pakete erişim izniniz yok.")
    
    context = {
        'package': package,
    }
    return render(request, 'packages/package_detail.html', context)


@login_required
def package_create(request):
    """Create a new package record"""
    if not request.user.is_caretaker and not request.user.is_admin:
        return HttpResponseForbidden("Bu işlemi gerçekleştirme izniniz yok.")
    
    if request.method == 'POST':
        form = PackageForm(request.POST, request.FILES)
        if form.is_valid():
            package = form.save(commit=False)
            package.received_by = request.user
            package.save()
            messages.success(request, "Paket kaydı başarıyla oluşturuldu.")
            return redirect('package_list')
    else:
        # Limit buildings to those where user is caretaker
        if request.user.is_caretaker:
            buildings = Building.objects.filter(caretaker=request.user)
            initial = {'received_by': request.user}
        else:  # Admin can see all
            buildings = Building.objects.all()
            initial = {}
            
        form = PackageForm(initial=initial)
        # Update form querysets
        form.fields['building'].queryset = buildings
    
    context = {
        'form': form,
    }
    return render(request, 'packages/package_form.html', context)


@login_required
def package_update(request, pk):
    """Update an existing package record"""
    package = get_object_or_404(Package, pk=pk)
    
    # Check permissions
    if request.user.is_caretaker:
        if package.building.caretaker != request.user:
            return HttpResponseForbidden("Bu paketi düzenleme izniniz yok.")
    elif not request.user.is_admin:
        return HttpResponseForbidden("Bu paketi düzenleme izniniz yok.")
    
    if request.method == 'POST':
        form = PackageForm(request.POST, request.FILES, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, "Paket bilgileri başarıyla güncellendi.")
            return redirect('package_detail', pk=package.pk)
    else:
        form = PackageForm(instance=package)
        
        # Limit buildings to those where user is caretaker
        if request.user.is_caretaker:
            form.fields['building'].queryset = Building.objects.filter(caretaker=request.user)
    
    context = {
        'form': form,
        'package': package,
    }
    return render(request, 'packages/package_form.html', context)


@login_required
def package_deliver(request, pk):
    """Mark a package as delivered"""
    package = get_object_or_404(Package, pk=pk)
    
    # Check permissions
    if request.user.is_caretaker:
        if package.building.caretaker != request.user:
            return HttpResponseForbidden("Bu paketi teslim etme izniniz yok.")
    elif not request.user.is_admin:
        return HttpResponseForbidden("Bu paketi teslim etme izniniz yok.")
    
    if request.method == 'POST':
        form = PackageDeliveryForm(request.POST, request.FILES)
        if form.is_valid():
            package.status = Package.DELIVERED
            package.delivered_to = form.cleaned_data['delivered_to']
            package.delivery_signature = form.cleaned_data.get('delivery_signature')
            package.notes = form.cleaned_data.get('notes')
            package.save()
            messages.success(request, "Paket başarıyla teslim edildi olarak işaretlendi.")
            return redirect('package_list')
    else:
        form = PackageDeliveryForm()
    
    context = {
        'form': form,
        'package': package,
    }
    return render(request, 'packages/package_delivery_form.html', context)


@login_required
def visitor_list(request):
    """List all visitors"""
    if not request.user.is_caretaker and not request.user.is_admin:
        return HttpResponseForbidden("Bu sayfaya erişim izniniz yok.")
    
    # Get buildings where the user is caretaker
    if request.user.is_caretaker:
        buildings = Building.objects.filter(caretaker=request.user)
    else:  # Admin can see all
        buildings = Building.objects.all()
    
    visitors = Visitor.objects.filter(building__in=buildings).order_by('-arrival_time')
    
    # Filter by building if provided
    building_id = request.GET.get('building')
    if building_id:
        visitors = visitors.filter(building_id=building_id)
    
    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        visitors = visitors.filter(arrival_time__date__range=[start_date, end_date])
    
    context = {
        'visitors': visitors,
        'buildings': buildings,
    }
    return render(request, 'packages/visitor_list.html', context)


@login_required
def visitor_create(request):
    """Record a new visitor"""
    if not request.user.is_caretaker and not request.user.is_admin:
        return HttpResponseForbidden("Bu işlemi gerçekleştirme izniniz yok.")
    
    if request.method == 'POST':
        form = VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.recorded_by = request.user
            visitor.save()
            messages.success(request, "Ziyaretçi kaydı başarıyla oluşturuldu.")
            return redirect('visitor_list')
    else:
        # Limit buildings to those where user is caretaker
        if request.user.is_caretaker:
            buildings = Building.objects.filter(caretaker=request.user)
        else:  # Admin can see all
            buildings = Building.objects.all()
            
        form = VisitorForm()
        # Update form querysets
        form.fields['building'].queryset = buildings
    
    context = {
        'form': form,
    }
    return render(request, 'packages/visitor_form.html', context)


@login_required
def visitor_update(request, pk):
    """Update visitor information"""
    visitor = get_object_or_404(Visitor, pk=pk)
    
    # Check permissions
    if request.user.is_caretaker:
        if visitor.building.caretaker != request.user:
            return HttpResponseForbidden("Bu ziyaretçi kaydını düzenleme izniniz yok.")
    elif not request.user.is_admin:
        return HttpResponseForbidden("Bu ziyaretçi kaydını düzenleme izniniz yok.")
    
    if request.method == 'POST':
        form = VisitorForm(request.POST, instance=visitor)
        if form.is_valid():
            form.save()
            messages.success(request, "Ziyaretçi bilgileri başarıyla güncellendi.")
            return redirect('visitor_list')
    else:
        form = VisitorForm(instance=visitor)
        
        # Limit buildings to those where user is caretaker
        if request.user.is_caretaker:
            form.fields['building'].queryset = Building.objects.filter(caretaker=request.user)
    
    context = {
        'form': form,
        'visitor': visitor,
    }
    return render(request, 'packages/visitor_form.html', context)


@login_required
def visitor_checkout(request, pk):
    """Record visitor departure"""
    visitor = get_object_or_404(Visitor, pk=pk)
    
    # Check permissions
    if request.user.is_caretaker:
        if visitor.building.caretaker != request.user:
            return HttpResponseForbidden("Bu ziyaretçi kaydını güncelleme izniniz yok.")
    elif not request.user.is_admin:
        return HttpResponseForbidden("Bu ziyaretçi kaydını güncelleme izniniz yok.")
    
    # Set departure time
    visitor.departure_time = timezone.now()
    visitor.save()
    
    messages.success(request, "Ziyaretçi çıkışı başarıyla kaydedildi.")
    return redirect('visitor_list')
