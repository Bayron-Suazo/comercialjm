

document.addEventListener('DOMContentLoaded', function () {
    const rutInput = document.getElementById('id_rut');

    if (rutInput) {
        rutInput.addEventListener('input', function (e) {
            let value = e.target.value;

            // Eliminar caracteres no válidos
            value = value.replace(/[^0-9kK]/g, '');

            // Separar cuerpo y dígito verificador
            let cuerpo = value.slice(0, -1);
            let dv = value.slice(-1).toUpperCase();

            // Formatear el cuerpo con puntos (de derecha a izquierda)
            let cuerpoFormateado = '';
            for (let i = cuerpo.length; i > 0; i -= 3) {
                let start = Math.max(i - 3, 0);
                cuerpoFormateado = cuerpo.slice(start, i) + (cuerpoFormateado ? '.' + cuerpoFormateado : '');
            }

            // Unir con guion si hay cuerpo y dv
            e.target.value = cuerpoFormateado + (dv ? '-' + dv : '');
        });
    }
});