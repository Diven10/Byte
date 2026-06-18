"""
Views for the accounts application.

Handles user registration, login, logout, profile viewing/editing,
password changes, and follower/following lists.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import update_session_auth_hash

from .forms import ProfileEditForm, UserLoginForm, UserRegistrationForm
from interactions.models import Follow


def register_view(request):
    """
    Handle user registration.

    GET: Display the registration form.
    POST: Validate form data, create user, log them in, redirect to home.
    """
    if request.user.is_authenticated:
        return redirect('feed:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to Byte! Your account has been created.')
            return redirect('feed:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Handle user login.

    GET: Display the login form.
    POST: Authenticate user, handle remember_me, redirect appropriately.
    """
    if request.user.is_authenticated:
        return redirect('feed:home')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                # If remember_me is unchecked, session expires when browser closes
                if not remember_me:
                    request.session.set_expiry(0)

                messages.success(request, f'Welcome back, {user.username}!')

                # Redirect to 'next' param or default redirect URL
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Log the user out and redirect to the login page."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_view(request, username):
    """
    Display a user's profile.

    Shows the user's recipes (paginated), follower/following counts,
    and whether the current user is following them.
    """
    profile_user = get_object_or_404(User, username=username)
    
    tab = request.GET.get('tab', 'posts')
    if tab == 'liked':
        from recipes.models import Recipe
        recipes = Recipe.objects.filter(likes__user=profile_user).order_by('-created_at')
    elif tab == 'commented':
        from recipes.models import Recipe
        recipes = Recipe.objects.filter(comments__author=profile_user).distinct().order_by('-created_at')
    elif tab == 'reposts':
        # Placeholder for reposts if implemented later
        recipes = []
    else:
        recipes = profile_user.recipes.all().order_by('-created_at')

    # Pagination
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Check if the current user is following the profile user
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user,
        ).exists()

    is_own_profile = request.user == profile_user

    context = {
        'profile_user': profile_user,
        'recipes': page_obj,
        'page_obj': page_obj,
        'is_following': is_following,
        'is_own_profile': is_own_profile,
        'tab': tab,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """
    Handle profile editing.

    GET: Display the profile edit form pre-populated with current data.
    POST: Validate and save changes to both Profile and User models.
    """
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile', username=request.user.username)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def password_change_view(request):
    """
    Handle password changes using Django's PasswordChangeForm.

    GET: Display the password change form.
    POST: Validate and update the password, keeping the user logged in.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('accounts:profile', username=request.user.username)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})


@login_required
def followers_list(request, username):
    """
    Display the list of users who follow the given user.

    Shows all Follow objects where `following` is the given user.
    """
    profile_user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=profile_user).select_related(
        'follower', 'follower__profile'
    )

    paginator = Paginator(followers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile_user': profile_user,
        'follow_list': page_obj,
        'page_obj': page_obj,
        'list_type': 'followers',
    }
    return render(request, 'accounts/follow_list.html', context)


@login_required
def following_list(request, username):
    """
    Display the list of users that the given user follows.

    Shows all Follow objects where `follower` is the given user.
    """
    profile_user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=profile_user).select_related(
        'following', 'following__profile'
    )

    paginator = Paginator(following, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile_user': profile_user,
        'follow_list': page_obj,
        'page_obj': page_obj,
        'list_type': 'following',
    }
    return render(request, 'accounts/follow_list.html', context)


@login_required
def settings_view(request):
    """
    Display the user settings page.
    """
    return render(request, 'accounts/settings.html')


@login_required
def accessibility_view(request):
    """
    Display Accessibility, Display, and Language settings.
    """
    return render(request, 'accounts/accessibility.html')


