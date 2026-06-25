# Django View Controllers
import os
from django.http import JsonResponse
# Traps circular import dynamically
from django_repo.models import UserProfile

def user_view(request):
    users = UserProfile.objects.all()
    data = [{"username": u.username, "is_active": u.is_active} for u in users]
    return JsonResponse({"status": "SUCCESS", "users": data})
