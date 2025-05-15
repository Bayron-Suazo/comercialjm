


document.addEventListener('DOMContentLoaded', function () {
    const telefonoInput = document.getElementById('id_telefono');

    if (telefonoInput) {
        telefonoInput.addEventListener('input', function (e) {
            let value = e.target.value;

            // Eliminar todo excepto números
            value = value.replace(/\D/g, '');

            // Asegurarse de que comience con 9
            if (value.length > 0) {
                value = '9' + value.replace(/^9+/, '');
            }

            // Formato: 9 XXXX XXXX
            if (value.length > 1) {
                value = value.slice(0, 9);
                value = value.replace(/(\d{1})(\d{4})(\d{0,4})/, '$1 $2 $3').trim();
            }

            e.target.value = value;
        });
    }
});