"""
Views for the recipes application.

Handles recipe CRUD, home feed, explore, search, hashtag/category
browsing, and trending recipes.
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from interactions.models import Bookmark, Follow, Like
from .forms import RecipeForm, SearchForm
from .models import Category, Hashtag, Recipe, Rating


@login_required
def home_feed(request):
    """
    Display the home feed.

    Supports two tabs:
    - 'foryou': All recipes ordered by newest first.
    - 'following': Recipes from users the current user follows.

    Each recipe is annotated with is_liked and is_bookmarked for the
    current user to support real-time UI state.
    """
    tab = request.GET.get('tab', 'foryou')

    if tab == 'following':
        # Get IDs of users the current user follows
        following_ids = Follow.objects.filter(
            follower=request.user,
        ).values_list('following_id', flat=True)
        recipes = Recipe.objects.filter(author_id__in=following_ids)
    else:
        tab = 'foryou'
        recipes = Recipe.objects.all()

    # Annotate with is_liked and is_bookmarked for the current user
    recipes = recipes.annotate(
        is_liked=Exists(
            Like.objects.filter(
                user=request.user,
                recipe=OuterRef('pk'),
            )
        ),
        is_bookmarked=Exists(
            Bookmark.objects.filter(
                user=request.user,
                recipe=OuterRef('pk'),
            )
        ),
    ).select_related('author', 'author__profile', 'category').order_by('-created_at')

    # Pagination
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'recipes': page_obj,
        'tab': tab,
        'page_obj': page_obj,
    }
    return render(request, 'feed/home.html', context)


@login_required
def explore_view(request):
    """
    Display the explore page.

    Shows trending hashtags (top 10 by recipe count),
    trending recipes (top 5 most liked in the last 7 days),
    and all recipe categories.
    """
    tab = request.GET.get('tab', 'foryou')
    seven_days_ago = timezone.now() - timedelta(days=7)

    if tab == 'trending':
        trending_recipes = Recipe.objects.filter(
            likes__created_at__gte=seven_days_ago,
        ).annotate(
            recent_likes=Count('likes'),
        ).order_by('-recent_likes')[:5]
    elif tab == 'most_viewed':
        trending_recipes = Recipe.objects.all().order_by('-views_count')[:5]
    elif tab == 'most_liked':
        trending_recipes = Recipe.objects.annotate(
            total_likes=Count('likes')
        ).order_by('-total_likes')[:5]
    else: # foryou
        trending_recipes = Recipe.objects.all().order_by('?')[:5]

    context = {
        'trending_recipes': trending_recipes,
        'tab': tab,
    }
    return render(request, 'feed/explore.html', context)


@login_required
def recipe_detail(request, pk):
    """
    Display a single recipe's detail page.

    Shows full recipe info, comments, and checks whether the
    current user has liked, bookmarked, or rated this recipe.
    """
    recipe = get_object_or_404(
        Recipe.objects.select_related('author', 'author__profile', 'category'),
        pk=pk,
    )
    
    # Increment view count
    recipe.views_count += 1
    recipe.save(update_fields=['views_count'])

    comments = recipe.comments.all().select_related(
        'user', 'user__profile',
    ).order_by('-created_at')

    # Check user interactions
    is_liked = Like.objects.filter(
        user=request.user, recipe=recipe,
    ).exists()
    is_bookmarked = Bookmark.objects.filter(
        user=request.user, recipe=recipe,
    ).exists()

    user_rating = None
    has_rated = False
    try:
        user_rating = Rating.objects.get(user=request.user, recipe=recipe)
        has_rated = True
    except Rating.DoesNotExist:
        pass

    context = {
        'recipe': recipe,
        'comments': comments,
        'is_liked': is_liked,
        'is_bookmarked': is_bookmarked,
        'has_rated': has_rated,
        'user_rating': user_rating,
    }
    return render(request, 'feed/recipe_detail.html', context)


@login_required
def recipe_create(request):
    """
    Handle recipe creation.

    GET: Display the recipe creation form.
    POST: Validate, save with author=request.user, parse hashtags, redirect.
    """
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            # Now save hashtags (M2M requires saved instance)
            hashtags_text = form.cleaned_data.get('hashtags_text', '')
            hashtags = Hashtag.parse_hashtags(hashtags_text)
            recipe.hashtags.set(hashtags)
            form.save_m2m()
            messages.success(request, 'Recipe created successfully!')
            return redirect('recipes:detail', pk=recipe.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RecipeForm()

    context = {
        'form': form,
        'is_editing': False,
    }
    return render(request, 'feed/recipe_form.html', context)


@login_required
def recipe_edit(request, pk):
    """
    Handle recipe editing.

    Only the recipe's author can edit it.
    GET: Display the form pre-populated with the recipe's data.
    POST: Validate and save changes.
    """
    recipe = get_object_or_404(Recipe, pk=pk)

    if recipe.author != request.user:
        return HttpResponseForbidden('You do not have permission to edit this recipe.')

    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recipe updated successfully!')
            return redirect('recipes:detail', pk=recipe.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RecipeForm(instance=recipe)

    context = {
        'form': form,
        'recipe': recipe,
        'is_editing': True,
    }
    return render(request, 'feed/recipe_form.html', context)


@login_required
def recipe_delete(request, pk):
    """
    Handle recipe deletion. POST only.

    Only the recipe's author can delete it.
    """
    recipe = get_object_or_404(Recipe, pk=pk)

    if recipe.author != request.user:
        return HttpResponseForbidden('You do not have permission to delete this recipe.')

    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted successfully.')
        return redirect('feed:home')

    return HttpResponseForbidden('Invalid request method.')


@login_required
def search_view(request):
    """
    Handle search across recipes, users, and hashtags.

    Searches recipes by title, short_description, and ingredients.
    Searches users by username, first_name, and last_name.
    Searches hashtags by name.
    """
    form = SearchForm(request.GET)
    recipes = Recipe.objects.none()
    users = User.objects.none()
    hashtags = Hashtag.objects.none()
    query = ''

    if form.is_valid():
        query = form.cleaned_data.get('query', '').strip()

        if query:
            # Search recipes
            recipes = Recipe.objects.filter(
                Q(title__icontains=query)
                | Q(short_description__icontains=query)
                | Q(ingredients__icontains=query)
            ).select_related('author', 'author__profile', 'category').distinct()

            # Search users
            users = User.objects.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            ).select_related('profile').distinct()

            # Search hashtags
            hashtags = Hashtag.objects.filter(
                name__icontains=query,
            )

    # Paginate recipe results
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'query': query,
        'recipes': page_obj,
        'page_obj': page_obj,
        'users': users,
        'hashtags': hashtags,
    }
    return render(request, 'feed/search_results.html', context)


@login_required
def hashtag_view(request, slug):
    """
    Display all recipes associated with a given hashtag.

    Recipes are paginated and ordered by newest first.
    """
    hashtag = get_object_or_404(Hashtag, slug=slug)
    recipes = hashtag.recipes.all().select_related(
        'author', 'author__profile', 'category',
    ).order_by('-created_at')

    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'hashtag': hashtag,
        'recipes': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'feed/hashtag.html', context)


@login_required
def category_view(request, slug):
    """
    Display all recipes in a given category.

    Recipes are paginated and ordered by newest first.
    """
    category = get_object_or_404(Category, slug=slug)
    recipes = category.recipes.all().select_related(
        'author', 'author__profile',
    ).order_by('-created_at')

    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'recipes': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'feed/category.html', context)


@login_required
def trending_view(request):
    """
    Display trending recipes.

    Trending is determined by the number of likes received
    in the last 7 days.
    """
    seven_days_ago = timezone.now() - timedelta(days=7)

    recipes = Recipe.objects.filter(
        likes__created_at__gte=seven_days_ago,
    ).annotate(
        recent_likes=Count('likes'),
    ).order_by('-recent_likes').select_related(
        'author', 'author__profile', 'category',
    )

    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'recipes': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'feed/trending.html', context)
