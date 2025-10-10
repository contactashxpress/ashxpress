import django_filters
from store.models import Product, Category


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Nom du produit'
    )

    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        field_name="category__slug",
        to_field_name="slug",
        label="Catégorie"
    )

    class Meta:
        model = Product
        fields = ['name', 'category']

