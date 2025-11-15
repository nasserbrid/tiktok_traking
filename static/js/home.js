// static/js/home.js

document.addEventListener('DOMContentLoaded', function() {
    // Animation au scroll pour les cartes
    const cards = document.querySelectorAll('.card');
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
    
    // Confirmation avant suppression
    const deleteButtons = document.querySelectorAll('a[href*="supprimer"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!this.href.includes('compte_delete')) {
                // Si ce n'est pas la page de confirmation, on demande confirmation
                if (!confirm('Es-tu sûr de vouloir supprimer ce compte ?')) {
                    e.preventDefault();
                }
            }
        });
    });
    
    // Auto-dismiss des alerts après 5 secondes
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
    
    // Tooltip pour les badges de statut
    const badges = document.querySelectorAll('.badge');
    badges.forEach(badge => {
        badge.setAttribute('title', badge.textContent.trim());
    });
    
    console.log('🚀 TikTok Tracking App loaded');
});