# views.py

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from .forms import CustomUserCreationForm

class RegisterView(View):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to login page, assuming you have a URL named 'login'
            return redirect(reverse_lazy('login'))
        return render(request, self.template_name, {'form': form})
