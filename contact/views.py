from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Contact, ContactPageContent
from .forms import ContactForm
from core.models import SocialLink

def contact_view(request):
    page_content = ContactPageContent.objects.first()
    social_links = SocialLink.objects.all()
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact:contact')
    else:
        form = ContactForm()
    
    context = {
        'page_content': page_content,
        'form': form,
        'social_links': social_links,
    }
    return render(request, 'contact/contact.html', context)

def success_view(request):
    return render(request, 'contact/success.html')
