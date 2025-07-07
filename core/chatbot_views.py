from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
import re
from datetime import datetime, timedelta

from buildings.models import Building, Apartment
from payments.models import ApartmentDues, Payment
from complaints.models import Complaint
from announcements.models import Announcement
from notifications.models import create_notification


class ApartmentChatbot:
    """AI Chatbot for apartment management assistance"""
    
    def __init__(self, user):
        self.user = user
        self.context = {}
        
    def process_message(self, message):
        """Process user message and return response"""
        message = message.lower().strip()
        
        # Intent detection
        intent = self.detect_intent(message)
        
        # Route to appropriate handler
        if intent == 'greeting':
            return self.handle_greeting()
        elif intent == 'payment_inquiry':
            return self.handle_payment_inquiry(message)
        elif intent == 'complaint_submit':
            return self.handle_complaint_submission(message)
        elif intent == 'announcement_check':
            return self.handle_announcement_check()
        elif intent == 'help':
            return self.handle_help()
        elif intent == 'contact_info':
            return self.handle_contact_info(message)
        elif intent == 'building_info':
            return self.handle_building_info(message)
        elif intent == 'maintenance_request':
            return self.handle_maintenance_request(message)
        else:
            return self.handle_unknown_intent(message)
    
    def detect_intent(self, message):
        """Detect user intent from message"""
        
        # Greeting patterns
        greeting_patterns = [
            r'merhaba', r'selam', r'günaydın', r'iyi akşamlar', r'hey', r'hello'
        ]
        
        # Payment patterns
        payment_patterns = [
            r'aidat', r'ödeme', r'borç', r'fatura', r'ücret', r'para',
            r'kaç para', r'ne kadar', r'ödeyeceğim', r'borcum'
        ]
        
        # Complaint patterns
        complaint_patterns = [
            r'şikayet', r'sorun', r'problem', r'arıza', r'bozuk',
            r'çalışmıyor', r'şikayetim var', r'sorunum var'
        ]
        
        # Announcement patterns
        announcement_patterns = [
            r'duyuru', r'haber', r'bilgi', r'toplantı', r'etkinlik',
            r'ne var ne yok', r'neler oluyor'
        ]
        
        # Help patterns
        help_patterns = [
            r'yardım', r'help', r'nasıl', r'ne yapabilirim',
            r'komutlar', r'özellikler'
        ]
        
        # Contact patterns
        contact_patterns = [
            r'iletişim', r'telefon', r'email', r'adres', r'yönetici',
            r'kapıcı', r'güvenlik'
        ]
        
        # Building info patterns
        building_patterns = [
            r'bina', r'apartman', r'blok', r'kat', r'daire',
            r'asansör', r'otopark'
        ]
        
        # Maintenance patterns
        maintenance_patterns = [
            r'bakım', r'tamir', r'onarım', r'tadilat', r'maintenance',
            r'elektrik', r'su', r'ısıtma', r'klima'
        ]
        
        # Check patterns
        if any(re.search(pattern, message) for pattern in greeting_patterns):
            return 'greeting'
        elif any(re.search(pattern, message) for pattern in payment_patterns):
            return 'payment_inquiry'
        elif any(re.search(pattern, message) for pattern in complaint_patterns):
            return 'complaint_submit'
        elif any(re.search(pattern, message) for pattern in announcement_patterns):
            return 'announcement_check'
        elif any(re.search(pattern, message) for pattern in help_patterns):
            return 'help'
        elif any(re.search(pattern, message) for pattern in contact_patterns):
            return 'contact_info'
        elif any(re.search(pattern, message) for pattern in building_patterns):
            return 'building_info'
        elif any(re.search(pattern, message) for pattern in maintenance_patterns):
            return 'maintenance_request'
        else:
            return 'unknown'
    
    def handle_greeting(self):
        """Handle greeting messages"""
        greetings = [
            f"Merhaba {self.user.first_name}! Size nasıl yardımcı olabilirim?",
            f"Selam {self.user.first_name}! Bugün sizin için ne yapabilirim?",
            f"İyi günler {self.user.first_name}! Apartman yönetimi konusunda yardımcı olabilirim."
        ]
        
        import random
        greeting = random.choice(greetings)
        
        quick_replies = [
            "💰 Aidat durumumu öğren",
            "📢 Duyuruları göster",
            "🔧 Şikayet bildirimi",
            "ℹ️ Yardım"
        ]
        
        return {
            'message': greeting,
            'quick_replies': quick_replies,
            'type': 'greeting'
        }
    
    def handle_payment_inquiry(self, message):
        """Handle payment related inquiries"""
        if not self.user.is_resident:
            return {
                'message': "Üzgünüm, ödeme bilgilerine sadece sakinler erişebilir.",
                'type': 'error'
            }
        
        # Get user's apartments
        apartments = self.user.get_apartments()
        
        if not apartments:
            return {
                'message': "Kayıtlı bir daireniz bulunamadı. Lütfen yönetici ile iletişime geçin.",
                'type': 'error'
            }
        
        total_debt = 0
        payment_info = []
        
        for apartment in apartments:
            unpaid_dues = ApartmentDues.objects.filter(
                apartment=apartment,
                status__in=['unpaid', 'partial', 'overdue']
            )
            
            for due in unpaid_dues:
                total_debt += due.amount - due.paid_amount
                payment_info.append({
                    'apartment': apartment.apartment_number,
                    'month': f"{due.dues.month}/{due.dues.year}",
                    'amount': due.amount - due.paid_amount,
                    'due_date': due.due_date.strftime('%d.%m.%Y'),
                    'status': due.get_status_display()
                })
        
        if total_debt == 0:
            return {
                'message': f"🎉 Harika! Tüm aidatlarınız ödenmiş durumda.",
                'type': 'success'
            }
        
        message_text = f"💰 Toplam borcunuz: {total_debt:.2f}₺\n\n"
        message_text += "📋 Detaylar:\n"
        
        for info in payment_info:
            message_text += f"• {info['apartment']} - {info['month']}: {info['amount']:.2f}₺ (Vade: {info['due_date']})\n"
        
        quick_replies = [
            "💳 Online ödeme yap",
            "📄 Ödeme geçmişi",
            "📞 Yönetici ile iletişim"
        ]
        
        return {
            'message': message_text,
            'quick_replies': quick_replies,
            'type': 'payment_info',
            'data': payment_info
        }
    
    def handle_complaint_submission(self, message):
        """Handle complaint submission"""
        if not self.user.is_resident:
            return {
                'message': "Şikayet bildirimi için sakin olmanız gerekiyor.",
                'type': 'error'
            }
        
        # Extract complaint details from message
        complaint_categories = {
            'asansör': 'elevator',
            'su': 'water',
            'elektrik': 'electrical',
            'ısıtma': 'heating',
            'temizlik': 'cleanliness',
            'gürültü': 'noise',
            'güvenlik': 'security',
            'otopark': 'parking'
        }
        
        detected_category = 'other'
        for keyword, category in complaint_categories.items():
            if keyword in message:
                detected_category = category
                break
        
        # Get user's first apartment
        apartment = self.user.get_apartments().first()
        
        if not apartment:
            return {
                'message': "Kayıtlı daireniz bulunamadı. Lütfen yönetici ile iletişime geçin.",
                'type': 'error'
            }
        
        return {
            'message': f"Şikayetinizi anlıyorum. Kategori: {complaint_categories.get(detected_category, 'Diğer')}\n\n"
                      f"Şikayetinizi daha detaylı açıklayabilir misiniz?",
            'type': 'complaint_form',
            'data': {
                'category': detected_category,
                'apartment_id': apartment.id
            },
            'awaiting_input': 'complaint_details'
        }
    
    def handle_announcement_check(self):
        """Handle announcement inquiries"""
        apartments = self.user.get_apartments()
        
        if not apartments:
            return {
                'message': "Kayıtlı daireniz bulunamadı.",
                'type': 'error'
            }
        
        buildings = [apt.building for apt in apartments]
        
        recent_announcements = Announcement.objects.filter(
            building__in=buildings,
            is_active=True,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:5]
        
        if not recent_announcements:
            return {
                'message': "📢 Son 7 günde yeni duyuru bulunmuyor.",
                'type': 'info'
            }
        
        message_text = "📢 Son duyurular:\n\n"
        
        for announcement in recent_announcements:
            urgency = "🚨 ACİL: " if announcement.is_urgent else ""
            message_text += f"{urgency}{announcement.title}\n"
            message_text += f"📅 {announcement.created_at.strftime('%d.%m.%Y')}\n"
            message_text += f"📄 {announcement.content[:100]}...\n\n"
        
        quick_replies = [
            "📄 Tüm duyuruları göster",
            "🔔 Bildirim ayarları"
        ]
        
        return {
            'message': message_text,
            'quick_replies': quick_replies,
            'type': 'announcements'
        }
    
    def handle_help(self):
        """Handle help requests"""
        help_text = """
🤖 Apartman Asistanı Yardım

Size şu konularda yardımcı olabilirim:

💰 **Ödeme İşlemleri**
• Aidat borcunu sorgula
• Ödeme geçmişini görüntüle
• Online ödeme yap

🔧 **Şikayet & Bakım**
• Şikayet bildir
• Bakım talebi oluştur
• Şikayet durumu sorgula

📢 **Duyuru & Bilgi**
• Son duyuruları göster
• Bina bilgileri
• İletişim bilgileri

❓ **Örnek Sorular:**
• "Aidat borcum ne kadar?"
• "Asansör bozuk, şikayet etmek istiyorum"
• "Son duyurular neler?"
• "Yöneticinin telefonu nedir?"

💡 **İpucu:** Doğal dille konuşabilirsiniz!
        """
        
        return {
            'message': help_text,
            'type': 'help'
        }
    
    def handle_contact_info(self, message):
        """Handle contact information requests"""
        apartments = self.user.get_apartments()
        
        if not apartments:
            return {
                'message': "Kayıtlı daireniz bulunamadı.",
                'type': 'error'
            }
        
        building = apartments.first().building
        
        contact_text = f"📞 **{building.name} İletişim Bilgileri**\n\n"
        
        if building.admin:
            contact_text += f"👨‍💼 **Yönetici:** {building.admin.get_full_name()}\n"
            contact_text += f"📧 Email: {building.admin.email}\n"
            if building.admin.phone_number:
                contact_text += f"📱 Telefon: {building.admin.phone_number}\n"
        
        if building.caretaker:
            contact_text += f"\n🔧 **Kapıcı:** {building.caretaker.get_full_name()}\n"
            if building.caretaker.phone_number:
                contact_text += f"📱 Telefon: {building.caretaker.phone_number}\n"
        
        contact_text += f"\n🏢 **Adres:** {building.address}\n"
        
        return {
            'message': contact_text,
            'type': 'contact_info'
        }
    
    def handle_building_info(self, message):
        """Handle building information requests"""
        apartments = self.user.get_apartments()
        
        if not apartments:
            return {
                'message': "Kayıtlı daireniz bulunamadı.",
                'type': 'error'
            }
        
        building = apartments.first().building
        
        info_text = f"🏢 **{building.name} Bilgileri**\n\n"
        info_text += f"📍 Adres: {building.address}\n"
        info_text += f"🏗️ Yapım Yılı: {building.build_year}\n"
        info_text += f"🏠 Toplam Daire: {building.apartment_count}\n"
        info_text += f"📊 Kat Sayısı: {building.floor_count}\n"
        
        if building.elevator_count:
            info_text += f"🛗 Asansör: {building.elevator_count} adet\n"
        
        if building.parking_spaces:
            info_text += f"🚗 Otopark: {building.parking_spaces} araçlık\n"
        
        # Add current user's apartment info
        user_apartment = apartments.first()
        info_text += f"\n🏠 **Sizin Daireniz:** {user_apartment.apartment_number}\n"
        info_text += f"📊 Kat: {user_apartment.floor}\n"
        info_text += f"🛏️ Oda Sayısı: {user_apartment.room_count}\n"
        info_text += f"📐 Alan: {user_apartment.area}m²\n"
        
        return {
            'message': info_text,
            'type': 'building_info'
        }
    
    def handle_maintenance_request(self, message):
        """Handle maintenance requests"""
        return {
            'message': "🔧 Bakım talebi oluşturmak için şikayet sistemini kullanabilirsiniz.\n\n"
                      "Hangi konuda bakım talep ediyorsunuz?",
            'quick_replies': [
                "⚡ Elektrik sorunu",
                "💧 Su/Tesisat sorunu", 
                "🔥 Isıtma sorunu",
                "🛗 Asansör sorunu",
                "🚪 Kapı/Pencere sorunu",
                "🎨 Boyama/Tadilat"
            ],
            'type': 'maintenance_request'
        }
    
    def handle_unknown_intent(self, message):
        """Handle unknown or unclear messages"""
        responses = [
            "Üzgünüm, tam olarak anlayamadım. Daha açık ifade edebilir misiniz?",
            "Bu konuda size nasıl yardımcı olabileceğimi anlayamadım. 'Yardım' yazarak neler yapabileceğimi öğrenebilirsiniz.",
            "Anlamadığım bir soru sordunuz. Lütfen daha detaylı açıklayın veya 'yardım' yazın."
        ]
        
        import random
        response = random.choice(responses)
        
        quick_replies = [
            "💰 Aidat sorgula",
            "🔧 Şikayet bildir",
            "📢 Duyurular",
            "ℹ️ Yardım"
        ]
        
        return {
            'message': response,
            'quick_replies': quick_replies,
            'type': 'clarification'
        }


@login_required
@csrf_exempt
def chatbot_api(request):
    """API endpoint for chatbot"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Initialize chatbot
        chatbot = ApartmentChatbot(request.user)
        
        # Process message
        response = chatbot.process_message(message)
        
        # Log conversation (optional)
        from .models import ChatbotConversation
        ChatbotConversation.objects.create(
            user=request.user,
            user_message=message,
            bot_response=response['message'],
            intent=response.get('type', 'unknown')
        )
        
        return JsonResponse({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
