document.addEventListener("DOMContentLoaded", function () {
    const lastNameInput = document.getElementById("id_last_name");

    if (lastNameInput) {
        lastNameInput.addEventListener("input", function () {
            let value = lastNameInput.value;

            // Eliminar números y caracteres especiales
            let cleaned = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]/g, "");

            // Si hay diferencias, actualizamos el valor limpio
            if (value !== cleaned) {
                value = cleaned;
            }

            // Separar palabras, limitar a 2, y capitalizar cada una
            let words = value.trim().split(/\s+/).slice(0, 2).map(word => {
                return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
            });

            // Mantener espacio final si el usuario aún está escribiendo
            if (value.endsWith(" ")) {
                lastNameInput.value = words.join(" ") + " ";
            } else {
                lastNameInput.value = words.join(" ");
            }
        });
    }
});