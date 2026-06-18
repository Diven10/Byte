"""
Forms for the recipes application.

Provides forms for recipe creation/editing and search functionality.
"""

from django import forms

from .models import Hashtag, Recipe


class RecipeForm(forms.ModelForm):
    """
    Form for creating and editing recipes.

    Includes an extra 'hashtags_text' field for entering hashtags
    as a space-separated string (e.g., '#vegan #healthy #dessert').
    """

    hashtags_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '#vegan #healthy #dessert',
        }),
        help_text='Enter hashtags separated by spaces (e.g., #vegan #healthy)',
        label='Hashtags',
    )

    class Meta:
        model = Recipe
        fields = [
            'title',
            'cover_image',
            'short_description',
            'ingredients',
            'instructions',
            'cooking_time',
            'servings',
            'category',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Recipe title',
            }),
            'cover_image': forms.ClearableFileInput(attrs={
                'class': 'form-input',
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'A brief description of your recipe...',
                'rows': 3,
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'One ingredient per line\ne.g.\n2 cups flour\n1 cup sugar\n3 eggs',
                'rows': 6,
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Step-by-step instructions\ne.g.\n1. Preheat oven to 350°F\n2. Mix dry ingredients\n3. Add wet ingredients',
                'rows': 8,
            }),
            'cooking_time': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Time in minutes',
                'min': 1,
            }),
            'servings': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Number of servings',
                'min': 1,
            }),
            'category': forms.Select(attrs={
                'class': 'form-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        """Populate hashtags_text from existing recipe hashtags when editing."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            existing_hashtags = self.instance.hashtags.all()
            if existing_hashtags:
                self.fields['hashtags_text'].initial = ' '.join(
                    f'#{tag.name}' for tag in existing_hashtags
                )

    def save(self, commit=True):
        """
        Save the recipe and parse/set hashtags from hashtags_text.

        The recipe must be saved first (to get a PK) before
        ManyToMany hashtags can be set.
        """
        recipe = super().save(commit=commit)

        if commit:
            # Parse hashtags from the text field and set them
            hashtags_text = self.cleaned_data.get('hashtags_text', '')
            hashtags = Hashtag.parse_hashtags(hashtags_text)
            recipe.hashtags.set(hashtags)

        return recipe


class SearchForm(forms.Form):
    """Search form for finding recipes, users, and tags."""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'search-input',
            'placeholder': 'Search recipes, users, tags...',
        }),
    )
