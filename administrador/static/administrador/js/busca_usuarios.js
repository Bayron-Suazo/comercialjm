document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('.input-busqueda');
    const table = document.querySelector('.tabla-usuarios');
    const rows = table.querySelectorAll('tbody tr');

    // Asegurarse de que el input y las filas sean válidos
    if (!searchInput || !table || rows.length === 0) {
        console.error('No se encontraron los elementos necesarios para realizar la búsqueda.');
        return;
    }

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase().trim(); // Asegurarse de que se eliminen los espacios extras

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            let matchFound = false;

            cells.forEach(cell => {
                if (cell.textContent.toLowerCase().includes(query)) {
                    matchFound = true;
                }
            });

            // Mostrar o esconder la fila según si se encontró una coincidencia
            if (matchFound) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
});
