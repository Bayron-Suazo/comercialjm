document.addEventListener('DOMContentLoaded', () => {
    const dropdownButtons = document.querySelectorAll('.dropdown-btn');

    dropdownButtons.forEach(button => {
        button.addEventListener('click', () => {
            const allDropdowns = document.querySelectorAll('.dropdown-container');
            const thisDropdown = button.nextElementSibling;

            // Cierra todos los dropdowns excepto el que se está abriendo
            allDropdowns.forEach(drop => {
                if (drop !== thisDropdown && drop.classList.contains('open')) {
                    closeDropdown(drop);
                }
            });

            // Toggle el actual
            if (thisDropdown.classList.contains('open')) {
                closeDropdown(thisDropdown);
            } else {
                openDropdown(thisDropdown);
            }
        });
    });

    function openDropdown(dropdown) {
        // Calcula el alto máximo posible
        const sidebar = document.querySelector('.sidebar');
        const sidebarHeight = sidebar.clientHeight;
        const maxHeight = sidebarHeight - 40;
    
        const fullHeight = dropdown.scrollHeight;
    
        const finalHeight = Math.min(fullHeight, maxHeight);
        dropdown.style.height = finalHeight + "px";
        dropdown.classList.add('open');
    }

    function closeDropdown(dropdown) {
        dropdown.style.height = dropdown.scrollHeight + "px";
        requestAnimationFrame(() => {
            dropdown.style.height = "0px";
        });
        dropdown.classList.remove('open');
    }
});