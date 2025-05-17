const menuLinks = document.querySelectorAll('.menu a');

menuLinks.forEach(link => {
    link.addEventListener('click', (event) => {
        // Remover la clase 'active' de todos los enlaces
        menuLinks.forEach(link => link.classList.remove('active'));

        // Agregar la clase 'active' al enlace clicado
        event.target.classList.add('active');
    });
});