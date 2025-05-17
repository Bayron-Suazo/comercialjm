document.addEventListener('DOMContentLoaded', () => {
    const dropdownButton = document.getElementById('dropdownMenuButton');
    const filterOptions = document.getElementById('filterOptions');
    const urlParams = new URLSearchParams(window.location.search);
    const currentOrderBy = urlParams.get('order_by');

    // Si hay un filtro activo, marca la opción en el dropdown
    if (currentOrderBy) {
        const activeFilter = document.querySelector(`#filterOptions a[data-filter="${currentOrderBy}"]`);
        if (activeFilter) activeFilter.classList.add('filtro-activo');
    }

    dropdownButton.addEventListener('click', (e) => {
        e.preventDefault();
        filterOptions.style.display = filterOptions.style.display === 'none' ? 'block' : 'none';
    });

    // Cerrar el dropdown al hacer clic fuera
    document.addEventListener('click', (e) => {
        if (!dropdownButton.contains(e.target) && !filterOptions.contains(e.target)) {
            filterOptions.style.display = 'none';
        }
    });

    // Aplicar filtro
    const filterLinks = filterOptions.querySelectorAll('a');
    filterLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const filter = link.getAttribute('onclick').split('applyFilter(\'')[1].split('\'')[0];

            // Actualizar la URL con el filtro seleccionado
            const params = new URLSearchParams(window.location.search);
            params.set('order_by', filter);
            window.location.search = params.toString(); // Recargar la página con el nuevo filtro
        });
    });

    // Función para limpiar el filtro
    window.clearOrderFilter = function() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Eliminar el parámetro 'order_by' de la URL
        urlParams.delete('order_by');
        
        // Recargar la página con los nuevos parámetros (sin el filtro)
        window.location.search = urlParams.toString();
    };

});