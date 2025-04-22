from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Project, ProjectCategory, Testimonial, ProjectsBanner

def project_list(request):
    categories = ProjectCategory.objects.all()
    selected_category = request.GET.get('category')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q')
    
    projects = Project.objects.all()
    banner = ProjectsBanner.objects.first()
    
    if selected_category:
        projects = projects.filter(category__slug=selected_category)
    
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(client__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    paginator = Paginator(projects, 9)
    page = request.GET.get('page')
    projects = paginator.get_page(page)
    
    context = {
        'projects': projects,
        'banner': banner,
        'categories': categories,
        'selected_category': selected_category,
        'status_filter': status_filter,
        'search_query': search_query
    }
    return render(request, 'projects/project_list.html', context)

def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    related_projects = Project.objects.filter(category=project.category).exclude(id=project.id)[:3]
    testimonials = project.testimonials.all()
    
    context = {
        'project': project,
        'related_projects': related_projects,
        'testimonials': testimonials
    }
    return render(request, 'projects/project_detail.html', context)

def category_projects(request, slug):
    category = get_object_or_404(ProjectCategory, slug=slug)
    projects = Project.objects.filter(category=category)
    
    paginator = Paginator(projects, 9)
    page = request.GET.get('page')
    projects = paginator.get_page(page)
    
    context = {
        'category': category,
        'projects': projects
    }
    return render(request, 'projects/category_projects.html', context)

def testimonials(request):
    testimonials = Testimonial.objects.all().order_by('-date')
    
    context = {
        'testimonials': testimonials
    }
    return render(request, 'projects/testimonials.html', context)
