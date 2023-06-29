from django.contrib.auth.models import User
User.objects.create_superuser(username='admin', email='admin@example.com', password='654321')