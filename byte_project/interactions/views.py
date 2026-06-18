"""Views for social interactions: likes, comments, bookmarks, follows, and ratings."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from interactions.models import Like, Comment, Bookmark, Follow
from notifications.signals import create_notification
from recipes.models import Recipe, Rating


@login_required
@require_POST
def toggle_like(request, recipe_id):
    """Toggle a like on a recipe. Returns JSON with liked status and count."""
    recipe = get_object_or_404(Recipe, pk=recipe_id)

    try:
        like = Like.objects.get(user=request.user, recipe=recipe)
        like.delete()
        liked = False
    except Like.DoesNotExist:
        Like.objects.create(user=request.user, recipe=recipe)
        liked = True
        # Create notification for recipe author (don't notify self)
        if request.user != recipe.author:
            create_notification(
                sender_user=request.user,
                recipient_user=recipe.author,
                notification_type='like',
                recipe=recipe,
                message=f'{request.user.username} liked your recipe "{recipe.title}".',
            )

    likes_count = recipe.likes.count()
    return JsonResponse({'liked': liked, 'likes_count': likes_count})


@login_required
@require_POST
def add_comment(request, recipe_id):
    """Add a comment to a recipe. Returns JSON with comment data."""
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    text = request.POST.get('text', '').strip()

    if not text:
        return JsonResponse({'error': 'Comment text is required.'}, status=400)

    comment = Comment.objects.create(
        author=request.user,
        recipe=recipe,
        text=text,
    )

    # Create notification for recipe author (don't notify self)
    if request.user != recipe.author:
        create_notification(
            sender_user=request.user,
            recipient_user=recipe.author,
            notification_type='comment',
            recipe=recipe,
            message=f'{request.user.username} commented on your recipe "{recipe.title}".',
        )

    # Build author profile picture URL
    author_profile_picture = ''
    if hasattr(request.user, 'profile'):
        author_profile_picture = request.user.profile.get_profile_picture_url()

    return JsonResponse({
        'id': comment.id,
        'author': comment.author.username,
        'author_profile_picture': author_profile_picture,
        'text': comment.text,
        'created_at': comment.created_at.isoformat(),
        'can_delete': True,
    })


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Delete a comment. Only the author can delete their own comment."""
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author != request.user:
        return JsonResponse(
            {'error': 'You can only delete your own comments.'}, status=403
        )

    comment.delete()
    return JsonResponse({'deleted': True})


@login_required
@require_POST
def toggle_bookmark(request, recipe_id):
    """Toggle a bookmark on a recipe. Returns JSON with bookmarked status and count."""
    recipe = get_object_or_404(Recipe, pk=recipe_id)

    try:
        bookmark = Bookmark.objects.get(user=request.user, recipe=recipe)
        bookmark.delete()
        bookmarked = False
    except Bookmark.DoesNotExist:
        Bookmark.objects.create(user=request.user, recipe=recipe)
        bookmarked = True

    bookmarks_count = recipe.bookmarks.count()
    return JsonResponse({'bookmarked': bookmarked, 'bookmarks_count': bookmarks_count})


@login_required
@require_POST
def toggle_follow(request, user_id):
    """Toggle following a user. Returns JSON with follow status and counts."""
    target_user = get_object_or_404(User, pk=user_id)

    # Prevent self-follow
    if request.user == target_user:
        return JsonResponse(
            {'error': 'You cannot follow yourself.'}, status=400
        )

    try:
        follow = Follow.objects.get(follower=request.user, following=target_user)
        follow.delete()
        following = False
    except Follow.DoesNotExist:
        Follow.objects.create(follower=request.user, following=target_user)
        following = True
        # Create notification on follow (not unfollow)
        create_notification(
            sender_user=request.user,
            recipient_user=target_user,
            notification_type='follow',
            message=f'{request.user.username} started following you.',
        )

    followers_count = target_user.followers.count()
    following_count = target_user.following_set.count()

    return JsonResponse({
        'following': following,
        'followers_count': followers_count,
        'following_count': following_count,
    })


@login_required
def saved_recipes(request):
    """Display the user's bookmarked/saved recipes with pagination."""
    bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related('recipe', 'recipe__author')

    recipes = [bookmark.recipe for bookmark in bookmarks]

    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'feed/saved.html', {
        'page_obj': page_obj,
        'recipes': page_obj,
    })


@login_required
@require_POST
def rate_recipe(request, recipe_id):
    """Rate a recipe from 1-5. Updates existing rating or creates new one."""
    recipe = get_object_or_404(Recipe, pk=recipe_id)

    try:
        score = int(request.POST.get('score', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid score value.'}, status=400)

    if score < 1 or score > 5:
        return JsonResponse(
            {'error': 'Score must be between 1 and 5.'}, status=400
        )

    Rating.objects.update_or_create(
        user=request.user,
        recipe=recipe,
        defaults={'score': score},
    )

    return JsonResponse({
        'rated': True,
        'score': score,
        'average_rating': recipe.average_rating,
    })
