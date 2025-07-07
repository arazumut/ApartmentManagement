# 🏢 Apartment Management System

Modern, feature-rich apartment management system built with Django. Manage buildings, residents, payments, complaints, and much more with an intuitive interface and powerful API.

## ✨ Features

### 🏠 **Building & Apartment Management**
- Multi-building support with detailed information
- Apartment tracking with residents and owners
- Floor plans and occupancy management
- Building-specific settings and customization

### 💰 **Financial Management**
- Automated monthly dues generation
- Payment tracking and history
- Expense recording and categorization
- Financial reports and analytics
- Late fee calculations
- Payment reminders and notifications

### 📢 **Communication & Announcements**
- Building-wide announcements
- Urgent notifications system
- Email and SMS integration
- Read receipts and engagement tracking
- Category-based filtering

### 🔧 **Complaint Management**
- Comprehensive complaint tracking
- Photo attachments and documentation
- Status updates and resolution tracking
- Satisfaction surveys
- Priority-based handling
- Assignment to caretakers

### 🔔 **Advanced Notifications**
- Real-time notification system
- Email and SMS channels
- User preferences and quiet hours
- Notification templates
- Delivery tracking and logs

### 👥 **User Management**
- Role-based access control (Admin, Resident, Caretaker, Security)
- Detailed user profiles
- Activity tracking
- Permission management
- Multi-language support

### 📊 **Analytics & Reporting**
- Financial dashboards
- Payment collection analytics
- Complaint resolution metrics
- Occupancy statistics
- User engagement reports
- Export capabilities

### 🚀 **API & Integration**
- RESTful API for all features
- Token-based authentication
- Comprehensive documentation
- Mobile app ready
- Third-party integrations

## 🛠️ Technology Stack

- **Backend**: Django 4.2+, Django REST Framework
- **Database**: PostgreSQL (Production), SQLite (Development)
- **Caching**: Redis
- **Frontend**: Bootstrap 5, JavaScript
- **Email**: Django Email Backend
- **File Storage**: Local/Cloud Storage
- **Authentication**: Django Allauth, Token Auth

## 📦 Installation

### Quick Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/apartment-management.git
cd apartment-management

# Run setup script
chmod +x setup.sh
./setup.sh
```

### Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/apartment-management.git
   cd apartment-management
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Create sample data (optional):**
   ```bash
   python manage.py create_sample_data
   ```

8. **Run the server:**
   ```bash
   python manage.py runserver
   ```

## 🌐 Usage

### Web Interface
- **Homepage**: `http://127.0.0.1:8000/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`
- **Dashboard**: `http://127.0.0.1:8000/dashboard/`

### API Endpoints
- **API Root**: `http://127.0.0.1:8000/api/v1/`
- **Authentication**: `http://127.0.0.1:8000/api/v1/users/auth/`
- **Users**: `http://127.0.0.1:8000/api/v1/users/`
- **Buildings**: `http://127.0.0.1:8000/api/v1/buildings/`
- **Payments**: `http://127.0.0.1:8000/api/v1/payments/`
- **Complaints**: `http://127.0.0.1:8000/api/v1/complaints/`

### Default Credentials
- **Admin**: `admin@apartman.com` / `admin123`
- **Resident**: Created via sample data
- **Caretaker**: Created via sample data

## 📱 User Roles

### 🛡️ **Administrator**
- Full system access
- Building management
- User management
- Financial oversight
- Report generation
- System configuration

### 🏠 **Resident**
- View personal information
- Pay dues online
- Submit complaints
- View announcements
- Track payment history
- Update profile

### 🔧 **Caretaker**
- Manage assigned buildings
- Handle complaints
- Update maintenance records
- Create announcements
- View resident information

### 🛡️ **Security**
- Monitor building access
- Handle security complaints
- View resident directory
- Create incident reports

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@apartmentmanagement.com

# Redis (Optional)
REDIS_URL=redis://127.0.0.1:6379/1

# SMS Configuration (Optional)
SMS_API_KEY=your-sms-api-key
SMS_API_SECRET=your-sms-secret
```

### Database Setup

For production, use PostgreSQL:

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE apartment_management;
CREATE USER apartment_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE apartment_management TO apartment_user;
```

Update your `.env`:
```env
DATABASE_URL=postgres://apartment_user:your_password@localhost/apartment_management
```

## 🧪 Testing

Run tests with:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test payments
python manage.py test complaints

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Management Commands

### Create Sample Data
```bash
python manage.py create_sample_data --users 50 --buildings 5
```

### Generate Reports
```bash
python manage.py generate_monthly_reports
python manage.py send_payment_reminders
python manage.py cleanup_old_notifications
```

### Maintenance
```bash
python manage.py clearsessions
python manage.py collectstatic
python manage.py compress
```

## 🚀 Deployment

### Production Checklist

1. **Environment Setup**
   - Set `DEBUG=False`
   - Configure `ALLOWED_HOSTS`
   - Set up secure `SECRET_KEY`
   - Configure database
   - Set up Redis for caching

2. **Security**
   - Enable HTTPS
   - Configure CSRF settings
   - Set up proper headers
   - Configure firewall

3. **Performance**
   - Enable caching
   - Configure static file serving
   - Set up CDN
   - Database optimization

4. **Monitoring**
   - Set up logging
   - Configure error tracking
   - Monitor performance
   - Set up backups

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "apartment_project.wsgi:application"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django community for the amazing framework
- Contributors and testers
- Building managers who provided requirements
- Open source libraries used in this project

## 🆘 Support

- 📧 Email: support@apartmentmanagement.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/apartment-management/issues)
- 📖 Documentation: [Wiki](https://github.com/yourusername/apartment-management/wiki)

---

Made with ❤️ for better apartment management

## Usage

- To access the admin panel: `http://localhost:8000/admin/`
- To access the main page: `http://localhost:8000/`

## Technologies

- Python 3.11+
- Django 4.2+
- PostgreSQL (or SQLite for development)
- Django REST Framework
- Bootstrap 5 / Tailwind CSS

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
