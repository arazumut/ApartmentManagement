# Apartment Management System

Django-based apartment management system. Includes features such as dues tracking, announcements, complaints, and caretaker task management.

## Features

- Role-based user system (Administrator, Resident, Caretaker)
- Building and apartment management
- Dues tracking and payment system
- Expense records and reporting
- Announcement system
- Complaint and request management
- Caretaker task tracking
- Package and visitor registration

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/apartment-management.git
   cd apartment-management
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Migrate the database:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the application:
   ```
   python manage.py runserver
   ```

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
