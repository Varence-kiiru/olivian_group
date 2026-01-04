from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from .models import Post, Category, Tag, Comment, BlogBanner, PostLike, CommentLike
from .forms import CommentForm, PostForm, CategoryForm, TagForm, BlogBannerForm
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
def staff_check(user):
    """Check if user has blog management permissions"""
    return user.is_staff or user.role in ['super_admin', 'manager', 'director', 'sales_manager', 'content_manager']

@login_required
@user_passes_test(staff_check)
def blog_management_dashboard(request):
    """Blog management dashboard for staff"""
    # Post statistics
    total_posts = Post.objects.count()
    published_posts = Post.objects.filter(status='published').count()
    draft_posts = Post.objects.filter(status='draft').count()
    featured_posts = Post.objects.filter(is_featured=True).count()

    # Recent posts
    recent_posts = Post.objects.all()[:10]

    # Unapproved comments
    pending_comments = Comment.objects.filter(is_approved=False).count()

    # Categories and tags count
    categories_count = Category.objects.count()
    tags_count = Tag.objects.count()

    context = {
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'featured_posts': featured_posts,
        'recent_posts': recent_posts,
        'pending_comments': pending_comments,
        'categories_count': categories_count,
        'tags_count': tags_count,
    }

    return render(request, 'blog/management/dashboard.html', context)

@login_required
@user_passes_test(staff_check)
def post_management_list(request):
    """Staff view for managing blog posts"""
    posts = Post.objects.all().select_related('author', 'category').order_by('-created_at')

    # Filters
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    author_filter = request.GET.get('author')
    search = request.GET.get('search')

    if status_filter:
        posts = posts.filter(status=status_filter)
    if category_filter:
        posts = posts.filter(category_id=category_filter)
    if author_filter:
        posts = posts.filter(author_id=author_filter)
    if search:
        posts = posts.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(excerpt__icontains=search)
        )

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(posts, 25)
    page = request.GET.get('page')
    posts = paginator.get_page(page)

    # Get filter options
    categories = Category.objects.all()
    authors = Post.objects.values_list('author', flat=True).distinct()
    author_objects = []
    for author_id in authors:
        author = Post.objects.filter(author_id=author_id).first().author
        if author not in author_objects:
            author_objects.append(author)

    context = {
        'posts': posts,
        'categories': categories,
        'authors': author_objects,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'author_filter': author_filter,
        'search': search,
    }

    return render(request, 'blog/management/post_list.html', context)

@login_required
@user_passes_test(staff_check)
def post_create(request):
    """Create a new blog post"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # Ensure slug is generated if left blank
            if not post.slug and post.title:
                from django.utils.text import slugify
                post.slug = slugify(post.title)
                # Ensure uniqueness
                original_slug = post.slug
                counter = 1
                while Post.objects.filter(slug=post.slug).exists():
                    post.slug = f"{original_slug}-{counter}"
                    counter += 1
            post.save()
            form.save_m2m()  # Save many-to-many relationships (tags)
            messages.success(request, 'Post created successfully!')
            return redirect('blog:post_list')
    else:
        form = PostForm()

    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'blog/management/post_form.html', context)

@login_required
@user_passes_test(staff_check)
def post_edit(request, pk):
    """Edit a blog post"""
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            # Ensure slug is generated if left blank
            if not post.slug and post.title:
                from django.utils.text import slugify
                post.slug = slugify(post.title)
                # Ensure uniqueness, excluding current post
                original_slug = post.slug
                counter = 1
                while Post.objects.filter(slug=post.slug).exclude(pk=post.pk).exists():
                    post.slug = f"{original_slug}-{counter}"
                    counter += 1
            post.save()
            form.save_m2m()  # Save many-to-many relationships (tags)
            messages.success(request, 'Post updated successfully!')
            return redirect('blog:post_list')
    else:
        form = PostForm(instance=post)

    context = {
        'form': form,
        'post': post,
        'action': 'Edit',
    }
    return render(request, 'blog/management/post_form.html', context)



@login_required
@user_passes_test(staff_check)
def post_delete(request, pk):
    """Delete a blog post"""
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('blog:post_list')

    context = {
        'post': post,
    }
    return render(request, 'blog/management/post_confirm_delete.html', context)







@login_required
@user_passes_test(staff_check)
def category_management_list(request):
    """Manage blog categories"""
    categories = Category.objects.all().order_by('name')

    # Search functionality
    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(slug__icontains=search) |
            Q(description__icontains=search)
        )

    # Sorting functionality
    sort_by = request.GET.get('sort')
    if sort_by == 'name':
        categories = categories.order_by('name')
    elif sort_by == '-name':
        categories = categories.order_by('-name')
    elif sort_by == 'posts':
        categories = categories.annotate(posts_count=Count('post')).order_by('-posts_count')
    elif sort_by == '-posts':
        categories = categories.annotate(posts_count=Count('post')).order_by('posts_count')

    paginator = Paginator(categories, 20)
    page = request.GET.get('page')
    categories = paginator.get_page(page)

    context = {
        'categories': categories,
        'search': search,
        'sort_by': sort_by,
    }
    return render(request, 'blog/management/category_list.html', context)

@login_required
@user_passes_test(staff_check)
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('blog:category_list')
    else:
        form = CategoryForm()

    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'blog/management/category_form.html', context)

@login_required
@user_passes_test(staff_check)
def category_edit(request, pk):
    """Edit a category"""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('blog:category_list')
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'action': 'Edit',
    }
    return render(request, 'blog/management/category_form.html', context)

@login_required
@user_passes_test(staff_check)
def category_delete(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk)

    # Check if category is used by posts
    posts_count = category.post_set.count()
    if posts_count > 0:
        messages.error(request, f'Cannot delete category. It is used by {posts_count} posts.')
        return redirect('blog:category_list')

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('blog:category_list')

    context = {
        'category': category,
        'posts_count': posts_count,
    }
    return render(request, 'blog/management/category_confirm_delete.html', context)

@login_required
@user_passes_test(staff_check)
def category_export(request):
    """Export categories to CSV"""
    categories = Category.objects.all()

    # Apply same filters as list view
    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(slug__icontains=search) |
            Q(description__icontains=search)
        )

    # Apply sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'name':
        categories = categories.order_by('name')
    elif sort_by == '-name':
        categories = categories.order_by('-name')
    elif sort_by == 'posts':
        categories = categories.annotate(posts_count=Count('post')).order_by('-posts_count')
    elif sort_by == '-posts':
        categories = categories.annotate(posts_count=Count('post')).order_by('posts_count')

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="blog_categories.csv"'

    import csv
    writer = csv.writer(response)
    writer.writerow(['Name', 'Slug', 'Description', 'Posts Count', 'Created At'])

    for category in categories:
        writer.writerow([
            category.name,
            category.slug,
            category.description or '',
            category.post_set.count(),
            category.created_at.date() if hasattr(category, 'created_at') else ''
        ])

    return response

@login_required
@user_passes_test(staff_check)
def tag_management_list(request):
    """Manage blog tags"""
    tags = Tag.objects.all().order_by('name')

    # Search functionality
    search = request.GET.get('search')
    if search:
        tags = tags.filter(
            Q(name__icontains=search) |
            Q(slug__icontains=search)
        )

    # Sorting functionality
    sort_by = request.GET.get('sort')
    if sort_by == 'name':
        tags = tags.order_by('name')
    elif sort_by == '-name':
        tags = tags.order_by('-name')
    elif sort_by == 'posts':
        tags = tags.annotate(posts_count=Count('post')).order_by('-posts_count')
    elif sort_by == '-posts':
        tags = tags.annotate(posts_count=Count('post')).order_by('posts_count')

    paginator = Paginator(tags, 50)
    page = request.GET.get('page')
    tags = paginator.get_page(page)

    context = {
        'tags': tags,
        'search': search,
        'sort_by': sort_by,
    }
    return render(request, 'blog/management/tag_list.html', context)

@login_required
@user_passes_test(staff_check)
def tag_create(request):
    """Create a new tag"""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created successfully!')
            return redirect('blog:tag_list')
    else:
        form = TagForm()

    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'blog/management/tag_form.html', context)

@login_required
@user_passes_test(staff_check)
def tag_edit(request, pk):
    """Edit a tag"""
    tag = get_object_or_404(Tag, pk=pk)

    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated successfully!')
            return redirect('blog:tag_list')
    else:
        form = TagForm(instance=tag)

    context = {
        'form': form,
        'tag': tag,
        'action': 'Edit',
    }
    return render(request, 'blog/management/tag_form.html', context)

@login_required
@user_passes_test(staff_check)
def tag_delete(request, pk):
    """Delete a tag"""
    tag = get_object_or_404(Tag, pk=pk)

    # Check if tag is used by posts
    posts_count = tag.post_set.count()

    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully!')
        return redirect('blog:tag_list')

    context = {
        'tag': tag,
        'posts_count': posts_count,
    }
    return render(request, 'blog/management/tag_confirm_delete.html', context)

@login_required
@user_passes_test(staff_check)
def tag_export(request):
    """Export tags to CSV"""
    tags = Tag.objects.all()

    # Apply same filters as list view
    search = request.GET.get('search')
    if search:
        tags = tags.filter(
            Q(name__icontains=search) |
            Q(slug__icontains=search)
        )

    # Apply sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'name':
        tags = tags.order_by('name')
    elif sort_by == '-name':
        tags = tags.order_by('-name')
    elif sort_by == 'posts':
        tags = tags.annotate(posts_count=Count('post')).order_by('-posts_count')
    elif sort_by == '-posts':
        tags = tags.annotate(posts_count=Count('post')).order_by('posts_count')

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="blog_tags.csv"'

    import csv
    writer = csv.writer(response)
    writer.writerow(['Name', 'Slug', 'Posts Count', 'Created At'])

    for tag in tags:
        writer.writerow([
            tag.name,
            tag.slug,
            tag.post_set.count(),
            tag.created_at.date() if hasattr(tag, 'created_at') else ''
        ])

    return response

@login_required
@user_passes_test(staff_check)
def comment_management_list(request):
    """Manage blog comments"""
    comments = Comment.objects.all().select_related('post', 'post__author').order_by('-created_at')

    # Filters
    status_filter = request.GET.get('status')
    post_filter = request.GET.get('post')
    search = request.GET.get('search')

    if status_filter == 'approved':
        comments = comments.filter(is_approved=True)
    elif status_filter == 'pending':
        comments = comments.filter(is_approved=False)
    if post_filter:
        comments = comments.filter(post_id=post_filter)
    if search:
        comments = comments.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(content__icontains=search)
        )

    paginator = Paginator(comments, 25)
    page = request.GET.get('page')
    comments = paginator.get_page(page)

    # Get posts for filter dropdown
    posts = Post.objects.filter(comments__isnull=False).distinct().order_by('title')

    context = {
        'comments': comments,
        'posts': posts,
        'status_filter': status_filter,
        'post_filter': post_filter,
        'search': search,
    }
    return render(request, 'blog/management/comment_list.html', context)

@login_required
@user_passes_test(staff_check)
def approve_comment(request, pk):
    """Approve a comment"""
    comment = get_object_or_404(Comment, pk=pk)
    comment.is_approved = True
    comment.save()
    messages.success(request, 'Comment approved!')
    return redirect('blog:comment_list')

@login_required
@user_passes_test(staff_check)
def delete_comment(request, pk):
    """Delete a comment"""
    comment = get_object_or_404(Comment, pk=pk)

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
        return redirect('blog:comment_list')

    context = {
        'comment': comment,
    }
    return render(request, 'blog/management/comment_confirm_delete.html', context)

@login_required
@user_passes_test(staff_check)
def banner_management(request):
    """Manage blog banner"""
    banner = BlogBanner.objects.filter(is_active=True).first()
    if not banner:
        banner = BlogBanner()

    if request.method == 'POST':
        form = BlogBannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner updated successfully!')
            return redirect('blog:banner_management')
    else:
        form = BlogBannerForm(instance=banner)

    # Get all banners
    all_banners = BlogBanner.objects.all().order_by('-is_active', 'title')

    context = {
        'form': form,
        'banner': banner,
        'all_banners': all_banners,
    }
    return render(request, 'blog/management/banner_management.html', context)

@login_required
@user_passes_test(staff_check)
def toggle_banner_status(request, pk):
    """Toggle banner active status"""
    banner = get_object_or_404(BlogBanner, pk=pk)
    if banner.is_active:
        banner.is_active = False
        messages.success(request, 'Banner deactivated!')
    else:
        banner.is_active = True
        messages.success(request, 'Banner activated!')
    banner.save()
    return redirect('blog:banner_management')

@login_required
@user_passes_test(staff_check)
def toggle_post_status(request, pk):
    """Toggle post publish/draft status"""
    post = get_object_or_404(Post, pk=pk)
    if post.status == 'published':
        post.status = 'draft'
        messages.success(request, 'Post moved to draft!')
    else:
        post.status = 'published'
        messages.success(request, 'Post published!')
    post.save()
    # Redirect back to post list with any existing query parameters
    from django.urls import reverse
    base_url = reverse('blog:post_list')
    query_string = request.GET.urlencode()
    if query_string:
        base_url += '?' + query_string
    return redirect(base_url)

@login_required
@user_passes_test(staff_check)
def toggle_post_featured(request, pk):
    """Toggle post featured status"""
    post = get_object_or_404(Post, pk=pk)
    if post.is_featured:
        post.is_featured = False
        messages.success(request, 'Post removed from featured!')
    else:
        post.is_featured = True
        messages.success(request, 'Post marked as featured!')
    post.save()
    # Redirect back to post list with any existing query parameters
    from django.urls import reverse
    base_url = reverse('blog:post_list')
    query_string = request.GET.urlencode()
    if query_string:
        base_url += '?' + query_string
    return redirect(base_url)

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
        'banner': banner,
        'query': query,
    }
    return render(request, 'blog/blog_list.html', context)

@login_required
@user_passes_test(staff_check)
def post_preview(request, pk):
    """Preview post for staff - shows how it will look when published"""
    post = get_object_or_404(Post, pk=pk)

    # Get top-level comments only - show all approved comments for preview
    comments = post.comments.filter(parent__isnull=True, is_approved=True)
    # Get related posts based on same category and shared tags
    related_posts = Post.objects.filter(
        Q(category=post.category) |
        Q(tags__in=post.tags.all())
    ).exclude(id=post.id).distinct()[:3]

    # If still no related posts, show latest posts from same category
    if not related_posts.exists():
        related_posts = Post.objects.filter(category=post.category).exclude(id=post.id).order_by('-created_at')[:3]

    # Don't increment view count for previews
    # Comment form is optional for preview - interactions disabled

    context = {
        'post': post,
        'comments': comments,
        'related_posts': related_posts,
        'is_preview': True,  # Flag to indicate this is a preview
    }
    return render(request, 'blog/post_detail.html', context)

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')
    # Get top-level comments only for the original display
    comments = post.comments.filter(parent__isnull=True, is_approved=True)

    # Get related posts based on same category and shared tags
    related_posts = Post.objects.filter(
        Q(category=post.category) |
        Q(tags__in=post.tags.all())
    ).exclude(id=post.id).distinct()[:3]

    # If still no related posts, show latest posts from same category
    if not related_posts.exists():
        related_posts = Post.objects.filter(category=post.category).exclude(id=post.id).order_by('-created_at')[:3]

    # Increment view count
    post.views += 1
    post.save()

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.save()
            messages.success(request, 'Thank you for your comment! It has been submitted and will be reviewed before being published.')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        comment_form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'related_posts': related_posts,
        'is_preview': False,  # For published posts
    }
    return render(request, 'blog/post_detail.html', context)

def like_post(request, slug):
    """Handle post likes via AJAX"""
    try:
        if request.method == 'POST':
            post = get_object_or_404(Post, slug=slug, status='published')
            ip_address = get_client_ip(request)

            # Check if user already liked this post
            existing_like = PostLike.objects.filter(post=post, ip_address=ip_address).exists()

            liked = False
            if not existing_like:
                PostLike.objects.create(post=post, ip_address=ip_address)
                liked = True
            else:
                PostLike.objects.filter(post=post, ip_address=ip_address).delete()

            # Update likes count
            likes_count = post.post_likes.count()
            post.likes_count = likes_count
            post.save()

            return JsonResponse({
                'success': True,
                'liked': liked,
                'likes_count': likes_count
            })
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def like_comment(request, comment_id):
    """Handle comment likes via AJAX"""
    try:
        if request.method == 'POST':
            comment = get_object_or_404(Comment, id=comment_id)
            ip_address = get_client_ip(request)

            # Check if user already liked this comment
            existing_like = CommentLike.objects.filter(comment=comment, ip_address=ip_address).exists()
            liked = False

            if not existing_like:
                CommentLike.objects.create(comment=comment, ip_address=ip_address)
                liked = True

            # Update likes count
            likes_count = comment.comment_likes.count()
            comment.likes_count = likes_count
            comment.save()

            return JsonResponse({
                'success': True,
                'liked': liked,
                'likes_count': likes_count
            })
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def reply_comment(request, slug, comment_id):
    """Handle replies to comments"""
    post = get_object_or_404(Post, slug=slug, status='published')
    parent_comment = get_object_or_404(Comment, id=comment_id, post=post)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.post = post
            reply.parent = parent_comment
            reply.is_approved = True  # Replies don't need approval
            reply.save()
            messages.success(request, 'Thank you for your reply!')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = CommentForm()

    context = {
        'post': post,
        'parent_comment': parent_comment,
        'form': form,
    }
    return render(request, 'blog/comment_reply.html', context)

@login_required
def search_posts_api(request):
    """API endpoint for searching existing blog posts (for CKEditor internal linking)"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    # Search posts by title or slug
    posts = Post.objects.filter(
        Q(status='published') &
        (Q(title__icontains=query) | Q(slug__icontains=query))
    ).select_related('category').order_by('-created_at')[:10]

    results = []
    for post in posts:
        results.append({
            'id': post.pk,
            'title': post.title,
            'slug': post.slug,
            'url': post.get_absolute_url(),
            'category': post.category.name if post.category else '',
            'date': post.created_at.strftime('%b %d, %Y')
        })

    return JsonResponse({'results': results})

def get_client_ip(request):
    """Get client IP address for anonymous likes"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_nested_comments(comments):
    """Helper function to get nested comment structure"""
    nested = []
    for comment in comments:
        comment_data = {
            'comment': comment,
            'replies': []
        }
        # Get replies recursively
        replies = comment.replies.filter(is_approved=True)
        if replies:
            comment_data['replies'] = get_nested_comments(replies)
        nested.append(comment_data)
    return nested

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
        'banner': banner,
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
        'banner': banner,
    }
    return render(request, 'blog/tag_posts.html', context)
