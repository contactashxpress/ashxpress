    document.addEventListener('DOMContentLoaded', function() {
        // Fonction pour changer l'image principale
        window.changerImage = function(nouvelleImageUrl, el) {
            const mainImage = document.getElementById('mainImage');
            mainImage.style.opacity = 0; // Ajout d'une petite transition
            setTimeout(() => {
                mainImage.src = nouvelleImageUrl;
                mainImage.style.opacity = 1;
            }, 200);

            // Mettre à jour l'active sur la miniature
            document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
            if (el) el.classList.add('active');
        };

        const minusBtn = document.querySelector('.minus');
        const plusBtn = document.querySelector('.plus');
        const quantityInput = document.querySelector('.quantity-input');
        const zoomOverlay = document.querySelector('.zoom-overlay');
        const zoomedImage = document.querySelector('.zoomed-image');
        const closeZoom = document.querySelector('.close-zoom');
        const mainImage = document.getElementById('mainImage');

        // Gestion de la quantité
        if(minusBtn) minusBtn.addEventListener('click', function(e) {
            e.preventDefault();
            let value = parseInt(quantityInput.value);
            if (value > 1) quantityInput.value = value - 1;
        });
        if(plusBtn) plusBtn.addEventListener('click', function(e) {
            e.preventDefault();
            let value = parseInt(quantityInput.value);
            if (value < 10) quantityInput.value = value + 1;
        });
        if(quantityInput) quantityInput.addEventListener('change', function() {
            let value = parseInt(this.value);
            if (isNaN(value) || value < 1) this.value = 1;
            else if (value > 10) this.value = 10;
        });

        // ZOOM effet identique à votre code original
        if(mainImage) mainImage.addEventListener('click', function() {
            zoomedImage.src = this.src;
            zoomOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
        if(closeZoom) closeZoom.addEventListener('click', function() {
            zoomOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
        if(zoomOverlay) zoomOverlay.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
                document.body.style.overflow = '';
            }
        });

        // NOUVEAU JAVASCRIPT POUR LE SYSTÈME DE REVIEW PREMIUM
        const stars = document.querySelectorAll('.star-rating-input .star');
        const ratingInput = document.querySelector('#id_rating');

        if (stars.length > 0 && ratingInput) {
            stars.forEach(star => {
                star.addEventListener('click', function() {
                    const value = this.getAttribute('data-value');
                    ratingInput.value = value;
                    updateStars(value);
                });

                star.addEventListener('mouseenter', function() {
                    const value = this.getAttribute('data-value');
                    updateStars(value, 'hover');
                });
            });

            const starContainer = document.querySelector('.star-rating-input');
            starContainer.addEventListener('mouseleave', function() {
                // Rétablit l'affichage en fonction de la valeur cliquée (active)
                updateStars(ratingInput.value);
            });

            function updateStars(value, state = 'active') {
                stars.forEach(s => {
                    s.classList.remove('active', 'hover');
                    if (s.getAttribute('data-value') <= value) {
                        s.classList.add(state);
                    }
                });
            }
        }

        // Fonction pour scroller les avis
        window.scrollReviews = function(amount) {
            const reviewList = document.getElementById('reviewList');
            if(reviewList) reviewList.scrollBy({ left: amount, behavior: 'smooth' });
        };
    });