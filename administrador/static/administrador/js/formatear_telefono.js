


document.addEventListener('DOMContentLoaded', function () {
    const telefonoInput = document.getElementById('id_telefono');

    if (telefonoInput) {
        telefonoInput.addEventListener('input', function (e) {
            let value = e.target.value;

            value = value.replace(/\D/g, '');

            if (value.startsWith('9')) {

                value = value.slice(0, 9);

                value = value.replace(/(\d{1})(\d{4})(\d{0,4})/, '$1 $2 $3').trim();
            }

            e.target.value = value;
        });
    }
});