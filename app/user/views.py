from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token

@csrf_exempt
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        print(username,email)
        
        if not (username and password and email):
            return JsonResponse({'error': 'Please provide all required fields'})
        
        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already taken'})
        
        # Create the user
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        return JsonResponse({'success': 'User created successfully'})
        
    return JsonResponse({'error': 'Invalid Request'})

# @csrf_exempt
# def Login(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         print(username,password)
#         if not (username and password):
#             return JsonResponse({'error': 'Please provide all required fields'})
        
#         user = authenticate(request, username=username, password=password)
#         print(user)
#         if user:
#             login(request, user)
#             Token.create(user=user)
#             return JsonResponse({'success': 'Login successful'})
#         else:
#             return JsonResponse({'error': 'Invalid credentials'})
        
#     return JsonResponse({'error': 'Invalid Request'})
