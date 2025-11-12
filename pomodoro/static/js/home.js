// Home page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Home page loaded');

    // Tag menu logic
    const closeAllTagMenus = () => {
        document.querySelectorAll('.tag-menu').forEach(menu => {
            menu.classList.remove('open');
            menu.setAttribute('aria-hidden', 'true');
        });
    };

    // Open/close tag menu
    document.querySelectorAll('.tag-form').forEach(form => {
        const btn = form.querySelector('.tag-btn');
        const menu = form.querySelector('.tag-menu');
        const hiddenInput = form.querySelector('input[name="tags"]');

        const presetButtons = Array.from(form.querySelectorAll('.color-choice'));

        // Initialize selected state from hidden input
        const initial = (hiddenInput?.value || '').split(',').filter(Boolean);
        presetButtons.forEach(b => {
            if (initial.includes(b.dataset.color)) b.classList.add('selected');
        });

        btn?.addEventListener('click', (e) => {
            e.preventDefault();
            const isOpen = menu.classList.contains('open');
            closeAllTagMenus();
            if (!isOpen) {
                menu.classList.add('open');
                menu.setAttribute('aria-hidden', 'false');
            }
        });

        // Select/deselect colors
        presetButtons.forEach(b => {
            b.addEventListener('click', (e) => {
                e.preventDefault();
                b.classList.toggle('selected');
            });
        });

        // Clear
        form.querySelector('.tag-clear')?.addEventListener('click', (e) => {
            e.preventDefault();
            presetButtons.forEach(b => b.classList.remove('selected'));
        });

        // Apply -> set hidden input and submit form
        form.querySelector('.tag-apply')?.addEventListener('click', (e) => {
            // allow normal submit, but first set value
            const colors = presetButtons.filter(b => b.classList.contains('selected')).map(b => b.dataset.color);
            if (hiddenInput) hiddenInput.value = colors.join(',');
            closeAllTagMenus();
        });
    });

    // Close menus on outside click
    document.addEventListener('click', (e) => {
        const isTagForm = e.target.closest?.('.tag-form');
        if (!isTagForm) closeAllTagMenus();
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeAllTagMenus();
    });
});