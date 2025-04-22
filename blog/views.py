from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Post, Category, Tag, BlogBanner
from .forms import CommentForm

def blog_list(request):
    posts = Post.objects.filter(status='published')
    categories = Category.objects.all()
    tags = Tag.objects.all()
    featured_posts = Post.objects.filter(is_featured=True, status='published')[:3]
    
    # Get active banner
    banner = BlogBanner.objects.filter(is_active=True).first()
   
    # Search functionality
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        )
   
    # Pagination
    paginator = Paginator(posts, 6)  # 6 posts per page
    page = request.GET.get('page')
    posts = paginator.get_page(page)
   
    context = {
        'posts': posts,
        'categories': categories,
        'tags': tags,
        'featured_posts': featured_posts,
        'banner': banner
    }
    return render(request, 'blog/blog_list.html', context)

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')
    comments = post.comments.filter(is_approved=True)
    related_posts = Post.objects.filter(category=post.category).exclude(id=post.id)[:3]
   
    # Increment view count
    post.views += 1
    post.save()
   
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.save()
    else:
        comment_form = CommentForm()
   
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'related_posts': related_posts
    }
    return render(request, 'blog/post_detail.html', context)

def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, status='published')
    
    # Get active banner
    banner = BlogBanner.objects.filter(is_active=True).first()
   
    paginator = Paginator(posts, 6)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
   
    context = {
        'category': category,
        'posts': posts,
        'banner': banner
    }
    return render(request, 'blog/category_posts.html', context)

def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(tags=tag, status='published')
    
    # Get active banner
    banner = BlogBanner.objects.filter(is_active=True).first()
   
    paginator = Paginator(posts, 6)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
   
    context = {
        'tag': tag,
        'posts': posts,
        'banner': banner
    }
    return render(request, 'blog/tag_posts.html', context)
