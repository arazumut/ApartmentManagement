from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Package, Visitor
from buildings.models import Building, Apartment
from users.models import User


class PackageForm(forms.ModelForm):
    """Form for creating and updating package records"""
    
    class Meta:
        model = Package
        fields = ['building', 'apartment', 'tracking_number', 'sender', 'description', 'image', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields required
        self.fields['building'].required = True
        self.fields['apartment'].required = True
        
        # If building is selected, filter apartments
        if 'building' in self.data:
            try:
                building_id = int(self.data.get('building'))
                self.fields['apartment'].queryset = Apartment.objects.filter(building_id=building_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.building:
            self.fields['apartment'].queryset = Apartment.objects.filter(building=self.instance.building)
        else:
            self.fields['apartment'].queryset = Apartment.objects.none()


class PackageDeliveryForm(forms.Form):
    """Form for marking a package as delivered"""
    delivered_to = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.RESIDENT),
        label=_('Teslim Alan'),
        required=True
    )
    delivery_signature = forms.ImageField(
        label=_('İmza'),
        required=False
    )
    notes = forms.CharField(
        label=_('Notlar'),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )


class VisitorForm(forms.ModelForm):
    """Form for creating and updating visitor records"""
    
    class Meta:
        model = Visitor
        fields = ['building', 'apartment', 'name', 'id_number', 'purpose', 'arrival_time', 
                  'departure_time', 'vehicle_plate', 'host', 'notes']
        widgets = {
            'arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields required
        self.fields['building'].required = True
        self.fields['apartment'].required = True
        self.fields['name'].required = True
        self.fields['purpose'].required = True
        
        # Limit host choices to residents
        self.fields['host'].queryset = User.objects.filter(role=User.RESIDENT)
        
        # If building is selected, filter apartments
        if 'building' in self.data:
            try:
                building_id = int(self.data.get('building'))
                self.fields['apartment'].queryset = Apartment.objects.filter(building_id=building_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.building:
            self.fields['apartment'].queryset = Apartment.objects.filter(building=self.instance.building)
        else:
            self.fields['apartment'].queryset = Apartment.objects.none() 