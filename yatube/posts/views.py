from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import create_pages


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    return render(
        request,
        'posts/index.html',
        {'page_obj': create_pages(request, post_list)},
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group')
    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': create_pages(request, posts)},
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.select_related('author')
    following = request.user.is_authenticated and author.following.filter(
        user=request.user,
    ).exists()
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': create_pages(request, author_posts),
            'following': following,
        },
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': CommentForm(request.POST or None),
    })


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
        return render(request, 'posts/create_post.html', {'form': form})
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not post.author == request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect('posts:post_detail', post_id)
    return render(
        request,
        'posts/create_post.html',
        {
            'form': form,
            'post': post,
            'is_edit': True,
        },
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

# Paginator для подписок
def paginator_page(
        queryset,
        request,
        posts_on_page=settings.POSTS_PER_PAGE,
):
    return Paginator(queryset, posts_on_page).get_page(
        request.GET.get('page'))

@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    context = {'page_obj': paginator_page(post, request)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    # Не разрешаем подписываться на самого себя
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_filter = Follow.objects.filter(user=request.user, author=author)
    # Проверка на существование подписки
    if follow_filter.exists():
        follow_filter.delete()
    return redirect('posts:profile', username=username)
