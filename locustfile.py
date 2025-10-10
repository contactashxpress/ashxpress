# locustfile.py
import random
from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    host =   "http://127.0.0.1:8000"    # "http://localhost:8000" # ou http://127.0.0.1:8000

    """
    Simule le comportement d'un utilisateur naviguant sur le site e-commerce.
    """
    # Chaque utilisateur virtuel attendra entre 1 et 3 secondes entre chaque action.
    wait_time = between(1, 3)

    # ====================================================================
    # ✅ ÉTAPE 1 : REMPLIR CES LISTES AVEC VOS PROPRES DONNÉES !
    # ====================================================================
    # Ajoutez ici des slugs de produits qui existent dans votre base de données.
    # Plus la liste est longue, plus le test sera réaliste.
    PRODUCT_SLUGS = [
        "sandale",
        "buds-live",
        "mini-micro",
        # ... ajoutez-en une dizaine ou plus
    ]

    # Ajoutez ici des slugs de catégories qui existent.
    CATEGORY_SLUGS = [
        "sandale",
        # ...
    ]

    # ====================================================================

    def on_start(self):
        """Appelé lorsqu'un utilisateur virtuel commence sa session."""
        print("Un nouvel utilisateur virtuel démarre son parcours.")
        # On pourrait ajouter une connexion ici pour un test d'utilisateur authentifié.

    @task(10)  # 10 fois plus de poids : la page d'accueil est la plus visitée.
    def visit_homepage(self):
        """Simule la visite de la page d'accueil."""
        self.client.get("/")

    @task(5)
    def browse_category_and_product(self):
        """
        Simule un utilisateur qui visite une page catégorie,
        puis clique sur un produit pour voir ses détails.
        """
        if not self.CATEGORY_SLUGS:
            print("La liste CATEGORY_SLUGS est vide, cette tâche est ignorée.")
            return

        # 1. Visiter une page catégorie au hasard
        # Note: Je suppose une URL comme /?category=<slug>, basé sur votre ProductFilter.
        # Si votre URL est différente (ex: /category/<slug>/), ajustez la ligne ci-dessous.
        category_slug = random.choice(self.CATEGORY_SLUGS)
        self.client.get(f"/?category={category_slug}", name="/?category=[slug]")

        # 2. Visiter une page de détail de produit au hasard
        if not self.PRODUCT_SLUGS:
            print("La liste PRODUCT_SLUGS est vide, impossible de voir un détail produit.")
            return

        product_slug = random.choice(self.PRODUCT_SLUGS)
        self.client.get(f"/product/{product_slug}/", name="/product/[slug]")

    @task(3)
    def view_product_and_add_to_cart(self):
        """
        Simule un utilisateur qui trouve un produit et l'ajoute au panier.
        """
        if not self.PRODUCT_SLUGS:
            print("La liste PRODUCT_SLUGS est vide, cette tâche est ignorée.")
            return

        # 1. Choisir un produit au hasard
        product_slug = random.choice(self.PRODUCT_SLUGS)

        # 2. Consulter sa page de détail
        self.client.get(f"/product/{product_slug}/", name="/product/[slug]")

        # 3. L'ajouter au panier
        self.client.get(f"/product/{product_slug}/add-to-cart", name="/product/[slug]/add-to-cart")
        print(f"Utilisateur a ajouté le produit '{product_slug}' au panier.")

    @task(1)  # Poids faible : moins d'utilisateurs consultent leur panier en continu.
    def view_cart(self):
        """Simule la consultation du panier."""
        self.client.get("/cart/")

