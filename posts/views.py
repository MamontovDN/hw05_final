from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author', 'group'). \
        order_by('-pub_date').all().prefetch_related('comments')
    paginator = Paginator(post_list, 2)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(request, 'index.html',
                  {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group_posts. \
        select_related('author', 'group'). \
        order_by("-pub_date").all().prefetch_related('comments')
    paginator = Paginator(post_list, 2)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"page": page,
                                          "paginator": paginator,
                                          "group": group})


@login_required
def new_post(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form,
                                                 'post': None})
    return render(request, 'new_post.html', {'form': form,
                                             'post': None})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all(). \
        select_related('author', 'group'). \
        order_by('-pub_date').all().prefetch_related('comments')
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    return render(request,
                  'profile.html',
                  {
                      'author': author,
                      'page': page,
                      'paginator': paginator,
                      'user': request.user,
                      'following': following
                  }
                  )


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    post_count = author.posts.count()
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    form = CommentForm(None)
    comments = post.comments. \
        select_related('author').order_by('-created').all()
    return render(request, 'post.html',
                  {
                      'post': post,
                      'author': author,
                      'user': request.user,
                      'post_count': post_count,
                      'form': form,
                      'comments': comments,
                      'following': following
                  }
                  )


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        return redirect('post', username, post_id)
    article = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=article
                    )
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post', username, post_id)
        return render(request, 'new_post.html',
                      {'form': form, 'post': article}
                      )
    return render(request, 'new_post.html',
                  {'form': form, 'post': article}
                  )


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = Post.objects.get(id=post_id)
            comment.save()
            return redirect('post', username, post_id)
        return render(request, 'post.html', {'form': form})
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related('author', 'group').\
        order_by('-pub_date').filter(author__following__user=request.user).\
        prefetch_related('comments')
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(request, 'follow.html',
                  {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    follower = request.user
    author = get_object_or_404(User, username=username)
    if follower != author:
        Follow.objects.get_or_create(user=follower, author=author)
    previous_path = request.META.get('HTTP_REFERER')
    return redirect(previous_path if previous_path else 'profile', username)


@login_required
def profile_unfollow(request, username):
    follower = request.user
    author = get_object_or_404(User, username=username)
    follower.follower.filter(author=author).delete()
    previous_path = request.META.get('HTTP_REFERER')
    return redirect(previous_path if previous_path else 'profile', username)
