from django import forms
from .models import Building, Apartment
from users.models import User


class BuildingForm(forms.ModelForm):
    """Form for creating and updating buildings"""
    
    class Meta:
        model = Building
        fields = ['name', 'address', 'block_count', 'floors_per_block', 'apartments_per_floor', 'caretaker', 'admin']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit caretaker choices to users with caretaker role
        self.fields['caretaker'].queryset = User.objects.filter(role=User.CARETAKER)
        # Limit admin choices to users with admin role
        self.fields['admin'].queryset = User.objects.filter(role=User.ADMIN)


class ApartmentForm(forms.ModelForm):
    """Form for creating and updating apartments"""
    
    class Meta:
        model = Apartment
        fields = ['building', 'block', 'floor', 'number', 'size_sqm', 'bedroom_count', 
                  'resident', 'resident_type', 'owner', 'is_occupied', 'occupant_count']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit resident choices to users with resident role
        self.fields['resident'].queryset = User.objects.filter(role=User.RESIDENT)
        # Limit owner choices to users with resident role
        self.fields['owner'].queryset = User.objects.filter(role=User.RESIDENT) 