#!/bin/bash

# Apartment Management System Setup Script
# This script sets up the development environment

echo "🏢 Apartment Management System Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 is not installed. Please install pip3.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 and pip3 are installed${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOF
# Django Settings
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@apartmentmanagement.com

# Redis Settings (Optional, for caching)
REDIS_URL=redis://127.0.0.1:6379/1

# SMS Settings (Optional)
SMS_API_KEY=your-sms-api-key
SMS_API_SECRET=your-sms-api-secret
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo -e "${YELLOW}Creating superuser...${NC}"
echo "Please create a superuser account:"
python manage.py createsuperuser

# Create sample data
echo -e "${YELLOW}Would you like to create sample data? (y/n)${NC}"
read -r create_sample
if [[ $create_sample == "y" || $create_sample == "Y" ]]; then
    echo -e "${YELLOW}Creating sample data...${NC}"
    python manage.py create_sample_data
    echo -e "${GREEN}✓ Sample data created${NC}"
fi

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --noinput

echo -e "${GREEN}======================================"
echo -e "🎉 Setup completed successfully!"
echo -e "======================================"
echo -e "To start the development server:"
echo -e "  1. Activate virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  2. Run server: ${YELLOW}python manage.py runserver${NC}"
echo -e "  3. Open browser: ${YELLOW}http://127.0.0.1:8000/${NC}"
echo -e ""
echo -e "Admin panel: ${YELLOW}http://127.0.0.1:8000/admin/${NC}"
echo -e "API documentation: ${YELLOW}http://127.0.0.1:8000/api-auth/${NC}"
echo -e ""
echo -e "Happy coding! 🚀${NC}"
