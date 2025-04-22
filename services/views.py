from django.shortcuts import render, get_object_or_404
from .models import Service, ServicesBanner

def service_list(request):
    services = Service.objects.filter(is_active=True)
    banner = ServicesBanner.objects.first()
    
    context = {
        'services': services,
        'banner': banner,
    }
    return render(request, 'services/service_list.html', context)

def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    services = Service.objects.filter(is_active=True)
    
    context = {
        'service': service,
        'services': services,
    }
    return render(request, 'services/service_detail.html', context)

