from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from buildings.models import Building, Apartment
from payments.models import Dues, ApartmentDues
from faker import Faker
import random
from datetime import datetime, timedelta

User = get_user_model()
fake = Faker('tr_TR')  # Turkish locale


class Command(BaseCommand):
    help = 'Create sample data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users to create',
        )
        parser.add_argument(
            '--buildings',
            type=int,
            default=5,
            help='Number of buildings to create',
        )
        parser.add_argument(
            '--apartments-per-building',
            type=int,
            default=20,
            help='Number of apartments per building',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.create_sample_data(options)
                self.stdout.write(
                    self.style.SUCCESS('Sample data created successfully!')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sample data: {str(e)}')
            )

    def create_sample_data(self, options):
        # Create admin user
        admin_user = self.create_admin_user()
        
        # Create buildings
        buildings = self.create_buildings(options['buildings'], admin_user)
        
        # Create residents
        residents = self.create_residents(options['users'] - 1)  # -1 for admin
        
        # Create apartments and assign residents
        apartments = self.create_apartments(buildings, options['apartments_per_building'], residents)
        
        # Create caretakers
        caretakers = self.create_caretakers(len(buildings))
        
        # Assign caretakers to buildings
        self.assign_caretakers_to_buildings(buildings, caretakers)
        
        # Create dues
        self.create_dues(buildings)
        
        # Create sample complaints
        self.create_sample_complaints(apartments)
        
        # Create sample announcements
        self.create_sample_announcements(buildings, admin_user)
        
        # Create sample expenses
        self.create_sample_expenses(buildings, admin_user)

    def create_admin_user(self):
        """Create an admin user"""
        admin_email = 'admin@apartman.com'
        if not User.objects.filter(email=admin_email).exists():
            admin = User.objects.create_user(
                email=admin_email,
                password='admin123',
                first_name='Sistem',
                last_name='Yöneticisi',
                role=User.ADMIN,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(f'Admin user created: {admin_email}')
            return admin
        else:
            return User.objects.get(email=admin_email)

    def create_buildings(self, count, admin_user):
        """Create sample buildings"""
        buildings = []
        building_names = [
            'Güneş Apartmanı', 'Yıldız Sitesi', 'Çiçek Apartmanı', 
            'Anadolu Sitesi', 'Marmara Apartmanı', 'Boğaz Sitesi',
            'Palmiye Apartmanı', 'Çınar Sitesi', 'Lale Apartmanı',
            'Orkide Sitesi'
        ]
        
        for i in range(count):
            building = Building.objects.create(
                name=building_names[i % len(building_names)],
                address=fake.address(),
                admin=admin_user,
                floor_count=random.randint(5, 12),
                apartment_count=random.randint(20, 50),
                build_year=random.randint(1990, 2020),
                elevator_count=random.randint(1, 3),
                parking_spaces=random.randint(10, 30)
            )
            buildings.append(building)
            self.stdout.write(f'Building created: {building.name}')
        
        return buildings

    def create_residents(self, count):
        """Create sample residents"""
        residents = []
        for i in range(count):
            resident = User.objects.create_user(
                email=fake.email(),
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone_number=fake.phone_number()[:15],
                role=User.RESIDENT,
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80)
            )
            residents.append(resident)
            
        self.stdout.write(f'{count} residents created')
        return residents

    def create_caretakers(self, count):
        """Create sample caretakers"""
        caretakers = []
        for i in range(count):
            caretaker = User.objects.create_user(
                email=f'kapici{i+1}@apartman.com',
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone_number=fake.phone_number()[:15],
                role=User.CARETAKER,
                hire_date=fake.date_between(start_date='-2y', end_date='today'),
                salary=random.randint(3000, 5000)
            )
            caretakers.append(caretaker)
            
        self.stdout.write(f'{count} caretakers created')
        return caretakers

    def create_apartments(self, buildings, apartments_per_building, residents):
        """Create apartments and assign residents"""
        apartments = []
        resident_index = 0
        
        for building in buildings:
            for floor in range(1, building.floor_count + 1):
                apartments_per_floor = random.randint(2, 4)
                for apt_num in range(1, apartments_per_floor + 1):
                    apartment_number = f"{floor}{apt_num:02d}"
                    
                    # Assign resident (some apartments may be empty)
                    resident = None
                    if resident_index < len(residents) and random.random() > 0.1:  # 90% occupancy
                        resident = residents[resident_index]
                        resident_index += 1
                    
                    apartment = Apartment.objects.create(
                        building=building,
                        apartment_number=apartment_number,
                        floor=floor,
                        resident=resident,
                        owner=resident,  # Assume resident is also owner
                        room_count=random.randint(1, 4),
                        area=random.randint(50, 150),
                        is_occupied=resident is not None
                    )
                    apartments.append(apartment)
                    
                    if len(apartments) >= apartments_per_building:
                        break
                if len(apartments) >= apartments_per_building:
                    break
            
            self.stdout.write(f'Apartments created for {building.name}')
        
        return apartments

    def assign_caretakers_to_buildings(self, buildings, caretakers):
        """Assign caretakers to buildings"""
        for i, building in enumerate(buildings):
            if i < len(caretakers):
                building.caretaker = caretakers[i]
                building.save()

    def create_dues(self, buildings):
        """Create sample dues for the last 6 months"""
        from datetime import datetime
        
        current_date = datetime.now()
        
        for building in buildings:
            for months_back in range(6):
                month_date = current_date - timedelta(days=30 * months_back)
                
                # Skip if dues already exist
                if Dues.objects.filter(
                    building=building,
                    month=month_date.month,
                    year=month_date.year
                ).exists():
                    continue
                
                dues = Dues.objects.create(
                    building=building,
                    amount=random.randint(200, 500),
                    month=month_date.month,
                    year=month_date.year,
                    due_date=month_date.date().replace(day=5),
                    created_by=building.admin
                )
                
                # Create apartment dues and randomly mark some as paid
                apartment_dues = ApartmentDues.objects.filter(dues=dues)
                for apt_dues in apartment_dues:
                    if random.random() > 0.2:  # 80% payment rate
                        apt_dues.paid_amount = apt_dues.amount
                        apt_dues.status = ApartmentDues.PAID
                        apt_dues.save()
        
        self.stdout.write('Sample dues created')

    def create_sample_complaints(self, apartments):
        """Create sample complaints"""
        from complaints.models import Complaint
        
        complaint_titles = [
            'Asansör Arızası',
            'Su Kesintisi',
            'Gürültü Sorunu',
            'Temizlik Problemi',
            'Isıtma Sorunu',
            'Otopark Sorunu',
            'Güvenlik Sorunu',
            'Elektrik Kesintisi'
        ]
        
        complaint_descriptions = [
            'Asansör çalışmıyor, tamir edilmesi gerekiyor.',
            'Dairemde su kesintisi var.',
            'Üst kattaki komşudan gürültü geliyor.',
            'Ortak alanlar temizlenmiyor.',
            'Kalorifer yeterince ısıtmıyor.',
            'Otopark alanında sorun var.',
            'Güvenlik konusunda eksiklik var.',
            'Elektrik kesintisi yaşanıyor.'
        ]
        
        for i in range(min(30, len(apartments))):
            apartment = random.choice(apartments)
            if apartment.resident:
                Complaint.objects.create(
                    building=apartment.building,
                    apartment=apartment,
                    title=random.choice(complaint_titles),
                    description=random.choice(complaint_descriptions),
                    category=random.choice(['maintenance', 'noise', 'cleanliness', 'security']),
                    priority=random.randint(1, 5),
                    created_by=apartment.resident,
                    status=random.choice(['new', 'in_progress', 'resolved'])
                )
        
        self.stdout.write('Sample complaints created')

    def create_sample_announcements(self, buildings, admin_user):
        """Create sample announcements"""
        from announcements.models import Announcement
        
        announcement_titles = [
            'Genel Kurul Toplantısı',
            'Bakım Çalışması',
            'Yeni Düzenlemeler',
            'Güvenlik Uyarısı',
            'Temizlik Duyurusu',
            'Otopark Düzenlemesi'
        ]
        
        for building in buildings:
            for i in range(random.randint(2, 5)):
                Announcement.objects.create(
                    building=building,
                    title=random.choice(announcement_titles),
                    content=fake.text(max_nb_chars=500),
                    created_by=admin_user,
                    is_urgent=random.random() > 0.8,
                    is_active=True
                )
        
        self.stdout.write('Sample announcements created')

    def create_sample_expenses(self, buildings, admin_user):
        """Create sample expenses"""
        from payments.models import Expense
        
        expense_categories = ['maintenance', 'utilities', 'security', 'cleaning', 'other']
        expense_titles = [
            'Asansör Bakımı',
            'Elektrik Faturası',
            'Güvenlik Sistemi',
            'Temizlik Malzemeleri',
            'Genel Bakım'
        ]
        
        for building in buildings:
            for i in range(random.randint(5, 10)):
                Expense.objects.create(
                    building=building,
                    title=random.choice(expense_titles),
                    description=fake.text(max_nb_chars=200),
                    amount=random.randint(100, 2000),
                    category=random.choice(expense_categories),
                    expense_date=fake.date_between(start_date='-3m', end_date='today'),
                    created_by=admin_user
                )
        
        self.stdout.write('Sample expenses created')
