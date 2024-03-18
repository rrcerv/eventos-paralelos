from django.shortcuts import render, redirect
from django.contrib.auth import logout

def logout_admin(request):
    logout(request)
    return redirect('/auth/login/')


def teste(request):
    return render(request,'login2.html')