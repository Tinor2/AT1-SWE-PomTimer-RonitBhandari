// Home page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Home page loaded');

    // Tag menu logic
    const closeAllTagMenus = () => {
        document.querySelectorAll('.tag-menu').forEach(menu => {
            menu.classList.remove('open');
            menu.setAttribute('aria-hidden', 'true');
            // Move menu back to its original form
            const originalForm = menu.dataset.originalForm;
            if (originalForm) {
                const form = document.querySelector(`.tag-form[data-form-id="${originalForm}"]`);
                if (form) {
                    form.appendChild(menu);
                }
            }
        });
    };

    // Open/close tag menu
    document.querySelectorAll('.tag-form').forEach((form, index) => {
        const btn = form.querySelector('.tag-btn');
        const menu = form.querySelector('.tag-menu');
        const hiddenInput = form.querySelector('input[name="tags"]');

        // Add unique ID to form for tracking
        form.setAttribute('data-form-id', `form-${index}`);
        menu.setAttribute('data-original-form', `form-${index}`);

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
                // Move menu to body and position it
                document.body.appendChild(menu);
                
                // Position menu to the left of the button
                const rect = btn.getBoundingClientRect();
                menu.style.position = 'fixed';
                menu.style.top = `${rect.bottom + 6}px`;
                menu.style.right = 'auto';
                menu.style.left = `${rect.left - 180}px`; // Position 180px to the left (menu width + padding)
                
                // If menu would go off-screen left, adjust position
                if (rect.left - 180 < 10) {
                    menu.style.left = '10px';
                    menu.style.top = `${rect.bottom + 6}px`;
                }
                
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