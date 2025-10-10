
        // Version améliorée du script dans footer.html

document.addEventListener('DOMContentLoaded', function() {
    const legalPopup = document.getElementById('legal-popup');
    if (!legalPopup) return; // Si le popup n'existe pas, on arrête tout.

    const closeBtn = document.getElementById('close-legal-popup');
    const popupTitle = document.getElementById('popup-title');
    const popupContent = document.getElementById('popup-content');
    const legalLinks = document.querySelectorAll('.legal-link');
    const legalDataElement = document.getElementById('legal-data');

    let legalData = {};
    if (legalDataElement) {
        try {
            legalData = JSON.parse(legalDataElement.textContent);
        } catch (e) {
            console.error("Erreur d'analyse des données JSON.", e);
        }
    }

    const openPopup = (slug) => {
        const data = legalData[slug];
        if (data) {
            popupTitle.textContent = data.title;
            popupContent.innerHTML = data.content;
            legalPopup.classList.add('show'); // On utilise la classe pour l'animation
        }
    };

    const closePopup = () => {
        legalPopup.classList.remove('show'); // On retire la classe
    };

    legalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const slug = this.dataset.slug;
            openPopup(slug);
        });
    });

    closeBtn.addEventListener('click', closePopup);

    legalPopup.addEventListener('click', function(e) {
        if (e.target === legalPopup) {
            closePopup();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === "Escape" && legalPopup.classList.contains('show')) {
            closePopup();
        }
    });
});