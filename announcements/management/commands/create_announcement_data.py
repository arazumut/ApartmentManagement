from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth.models import Group
from announcements.models import (
    AnnouncementCategory, AnnouncementTemplate, Announcement,
    create_announcement_from_template
)
from buildings.models import Building
from users.models import User
import random


class Command(BaseCommand):
    help = 'Create sample announcement data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing announcement data before creating new data',
        )
        parser.add_argument(
            '--categories',
            type=int,
            default=6,
            help='Number of categories to create',
        )
        parser.add_argument(
            '--templates',
            type=int,
            default=10,
            help='Number of templates to create',
        )
        parser.add_argument(
            '--announcements',
            type=int,
            default=20,
            help='Number of announcements to create',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing announcement data...')
            Announcement.objects.all().delete()
            AnnouncementTemplate.objects.all().delete()
            AnnouncementCategory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))
        
        # Create categories
        self.create_categories(options['categories'])
        
        # Create templates
        self.create_templates(options['templates'])
        
        # Create announcements
        self.create_announcements(options['announcements'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample announcement data:\n'
                f'- {options["categories"]} categories\n'
                f'- {options["templates"]} templates\n'
                f'- {options["announcements"]} announcements'
            )
        )
    
    def create_categories(self, count):
        """Create sample announcement categories"""
        categories_data = [
            {
                'name': 'Genel Duyurular',
                'slug': 'genel-duyurular',
                'description': 'Genel bilgilendirme duyuruları',
                'color': '#007bff',
                'icon': 'ri-notification-line'
            },
            {
                'name': 'Bakım ve Onarım',
                'slug': 'bakim-onarim',
                'description': 'Bakım ve onarım çalışmaları ile ilgili duyurular',
                'color': '#ffc107',
                'icon': 'ri-tools-line'
            },
            {
                'name': 'Güvenlik',
                'slug': 'guvenlik',
                'description': 'Güvenlik ile ilgili duyurular',
                'color': '#dc3545',
                'icon': 'ri-shield-line'
            },
            {
                'name': 'Mali İşler',
                'slug': 'mali-isler',
                'description': 'Aidat ve mali konular ile ilgili duyurular',
                'color': '#28a745',
                'icon': 'ri-money-dollar-circle-line'
            },
            {
                'name': 'Sosyal Etkinlikler',
                'slug': 'sosyal-etkinlikler',
                'description': 'Sosyal etkinlik ve organizasyonlar',
                'color': '#17a2b8',
                'icon': 'ri-calendar-event-line'
            },
            {
                'name': 'Acil Durumlar',
                'slug': 'acil-durumlar',
                'description': 'Acil durum bildirimleri',
                'color': '#e83e8c',
                'icon': 'ri-alarm-warning-line'
            }
        ]
        
        for i in range(min(count, len(categories_data))):
            category_data = categories_data[i]
            category, created = AnnouncementCategory.objects.get_or_create(
                slug=category_data['slug'],
                defaults=category_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        self.stdout.write(f'Categories created: {min(count, len(categories_data))}')
    
    def create_templates(self, count):
        """Create sample announcement templates"""
        categories = list(AnnouncementCategory.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR('No categories found. Create categories first.'))
            return
        
        templates_data = [
            {
                'name': 'Genel Kurul Toplantısı',
                'title_template': '{{ building.name }} - Genel Kurul Toplantısı',
                'content_template': 'Sayın {{ building.name }} sakinleri,\n\nYıllık genel kurul toplantımız {{ meeting_date }} tarihinde saat {{ meeting_time }} de {{ meeting_location }} da yapılacaktır.\n\nKatılımınızı rica ederiz.',
                'priority': 'high'
            },
            {
                'name': 'Bakım Çalışması Bildirimi',
                'title_template': 'Bakım Çalışması - {{ work_type }}',
                'content_template': 'Sayın sakinler,\n\n{{ work_date }} tarihinde {{ work_type }} bakım çalışması yapılacaktır.\n\nÇalışma saatleri: {{ work_hours }}\n\nBu süre zarfında {{ affected_areas }} etkilenecektir.\n\nAnlayışınız için teşekkürler.',
                'priority': 'normal'
            },
            {
                'name': 'Aidat Hatırlatması',
                'title_template': '{{ month }} Ayı Aidat Hatırlatması',
                'content_template': 'Sayın {{ building.name }} sakinleri,\n\n{{ month }} ayı aidatlarınızın son ödeme tarihi {{ due_date }} dir.\n\nAidat tutarı: {{ amount }} TL\n\nZamanında ödemenizi rica ederiz.',
                'priority': 'normal'
            },
            {
                'name': 'Su Kesintisi',
                'title_template': 'Su Kesintisi Bildirimi',
                'content_template': 'Sayın sakinler,\n\n{{ cut_date }} tarihinde saat {{ start_time }} - {{ end_time }} arasında su kesintisi yaşanacaktır.\n\nKesinti nedeni: {{ reason }}\n\nÖnceden hazırlık yapmanızı öneririz.',
                'priority': 'urgent'
            },
            {
                'name': 'Elektrik Kesintisi',
                'title_template': 'Elektrik Kesintisi Bildirimi',
                'content_template': 'Sayın sakinler,\n\n{{ cut_date }} tarihinde saat {{ start_time }} - {{ end_time }} arasında elektrik kesintisi yaşanacaktır.\n\nKesinti nedeni: {{ reason }}\n\nAsansörler bu sürede çalışmayacaktır.',
                'priority': 'urgent'
            },
            {
                'name': 'Sosyal Etkinlik',
                'title_template': '{{ event_name }} Etkinliği',
                'content_template': 'Sayın sakinler,\n\n{{ event_date }} tarihinde {{ event_name }} etkinliği düzenlenecektir.\n\nEtkinlik yeri: {{ event_location }}\nEtkinlik saati: {{ event_time }}\n\nKatılım için: {{ contact_info }}',
                'priority': 'low'
            },
            {
                'name': 'Güvenlik Uyarısı',
                'title_template': 'Güvenlik Uyarısı',
                'content_template': 'Sayın sakinler,\n\n{{ warning_type }} konusunda dikkatli olmanızı rica ederiz.\n\n{{ warning_details }}\n\nHerhangi bir şüpheli durum gözlemlediğinizde güvenlik görevlisini bilgilendiriniz.',
                'priority': 'high'
            },
            {
                'name': 'Temizlik Bildirimi',
                'title_template': 'Temizlik Çalışması',
                'content_template': 'Sayın sakinler,\n\n{{ cleaning_date }} tarihinde {{ cleaning_areas }} temizlik çalışması yapılacaktır.\n\nÇalışma saatleri: {{ cleaning_hours }}\n\nBu alanlarda geçici olarak sıkıntı yaşanabilir.',
                'priority': 'low'
            },
            {
                'name': 'Yönetici Değişikliği',
                'title_template': 'Yönetici Değişikliği',
                'content_template': 'Sayın sakinler,\n\n{{ effective_date }} tarihinden itibaren site yöneticiliği {{ old_manager }} den {{ new_manager }} e devredilmiştir.\n\nYeni iletişim bilgileri:\nTelefon: {{ new_phone }}\nE-posta: {{ new_email }}',
                'priority': 'normal'
            },
            {
                'name': 'Acil Durum Bildirimi',
                'title_template': 'ACİL: {{ emergency_type }}',
                'content_template': 'ACİL DURUM BİLDİRİMİ\n\n{{ emergency_details }}\n\nYapmanız gerekenler:\n{{ instructions }}\n\nAcil iletişim: {{ emergency_contact }}',
                'priority': 'urgent'
            }
        ]
        
        created_count = 0
        for i in range(min(count, len(templates_data))):
            template_data = templates_data[i]
            template_data['category'] = random.choice(categories)
            
            template, created = AnnouncementTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created template: {template.name}')
        
        self.stdout.write(f'Templates created: {created_count}')
    
    def create_announcements(self, count):
        """Create sample announcements"""
        buildings = list(Building.objects.all())
        if not buildings:
            self.stdout.write(self.style.ERROR('No buildings found. Create buildings first.'))
            return
        
        categories = list(AnnouncementCategory.objects.all())
        templates = list(AnnouncementTemplate.objects.all())
        
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_staff=True).first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found.'))
            return
        
        # Sample announcement data
        announcement_titles = [
            'Site Yönetimi Genel Kurul Toplantısı',
            'Asansör Bakım Çalışması',
            'Mart Ayı Aidat Bildirimi',
            'Su Deposu Temizliği',
            'Elektrik Pano Bakımı',
            'Bahçe Düzenleme Çalışması',
            'Güvenlik Kamerası Kurulumu',
            'Sosyal Tesis Tadilat Çalışması',
            'Otopark Çizgi Çekimi',
            'İtfaiye Sistemleri Kontrolü',
            'Çatı Su Yalıtımı',
            'Kalorifer Sistemi Kontrolü',
            'Merdiven Temizliği',
            'Çevre Düzenleme Çalışması',
            'Güvenlik Görevlisi Değişikliği',
            'Paket Teslim Alanı Düzenlemesi',
            'Çocuk Oyun Alanı Yenileme',
            'Spor Aletleri Kurulumu',
            'Ses İzolasyon Çalışması',
            'Yangın Merdiveni Kontrolü'
        ]
        
        announcement_contents = [
            'Bu duyuru site sakinlerinin bilgisi için yayınlanmıştır. Detaylı bilgi için site yönetimi ile iletişime geçebilirsiniz.',
            'Çalışma sırasında yaşanabilecek geçici rahatsızlıklar için özür dileriz. Anlayışınız için teşekkürler.',
            'Belirtilen tarih ve saatlerde lütfen gerekli önlemleri alınız. Herhangi bir sorunuz için yönetim ile iletişime geçiniz.',
            'Bu süre zarfında normal hayat akışında geçici kesintiler olabilir. Sabır ve anlayışınız için teşekkür ederiz.',
            'Güvenliğiniz için gerekli olan bu çalışma, uzman ekip tarafından gerçekleştirilecektir.',
            'Çalışma süresince gürültü ve toz oluşabilir. Bu konuda anlayışınızı rica ederiz.',
            'Modern ve güvenli bir yaşam alanı için yapılan bu yatırım tüm sakinlerimizin yararına olacaktır.',
            'Kalite ve konforunuzu artırmak amacıyla yapılan bu çalışma için desteğinizi bekliyoruz.'
        ]
        
        priorities = ['low', 'normal', 'high', 'urgent']
        announcement_types = ['general', 'maintenance', 'security', 'financial', 'social']
        
        created_count = 0
        for i in range(count):
            building = random.choice(buildings)
            category = random.choice(categories) if categories else None
            
            # Create announcement
            announcement_data = {
                'building': building,
                'category': category,
                'title': random.choice(announcement_titles),
                'content': random.choice(announcement_contents),
                'short_description': 'Bu duyuru site sakinlerinin bilgisi için paylaşılmıştır.',
                'announcement_type': random.choice(announcement_types),
                'priority': random.choice(priorities),
                'status': random.choice(['published', 'published', 'published', 'draft']),  # More published
                'is_pinned': random.random() < 0.1,  # 10% chance
                'is_urgent': random.random() < 0.05,  # 5% chance
                'allow_comments': random.random() < 0.7,  # 70% chance
                'send_notification': True,
                'created_by': admin_user,
                'publish_at': timezone.now() - timezone.timedelta(days=random.randint(0, 30)),
                'tags': random.sample(['bilgilendirme', 'önemli', 'dikkat', 'hatırlatma', 'acil'], 
                                    random.randint(1, 3))
            }
            
            # Random expiry date (30% chance)
            if random.random() < 0.3:
                announcement_data['expires_at'] = timezone.now() + timezone.timedelta(
                    days=random.randint(7, 60)
                )
            
            announcement = Announcement.objects.create(**announcement_data)
            created_count += 1
            
            if i % 5 == 0:
                self.stdout.write(f'Created {created_count} announcements...')
        
        self.stdout.write(f'Announcements created: {created_count}')
    
    def create_sample_reads(self):
        """Create sample read records"""
        announcements = Announcement.objects.filter(status='published')
        users = User.objects.filter(apartment__isnull=False)
        
        from announcements.models import AnnouncementRead
        
        created_count = 0
        for announcement in announcements:
            # Random users read the announcement
            readers = random.sample(
                list(users.filter(apartment__building=announcement.building)),
                min(random.randint(1, 10), users.filter(apartment__building=announcement.building).count())
            )
            
            for user in readers:
                read_obj, created = AnnouncementRead.objects.get_or_create(
                    announcement=announcement,
                    user=user,
                    defaults={
                        'device_type': random.choice(['web', 'mobile']),
                        'read_at': timezone.now() - timezone.timedelta(
                            days=random.randint(0, 10)
                        )
                    }
                )
                if created:
                    created_count += 1
        
        self.stdout.write(f'Read records created: {created_count}')
