document.addEventListener("DOMContentLoaded", function () {
    const nameInput = document.getElementById("id_first_name");

    if (nameInput) {
        nameInput.addEventListener("input", function (e) {
            let value = nameInput.value;

            // Solo permitir letras y espacios
            let cleaned = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]/g, "");

            if (value !== cleaned) {
                value = cleaned;
            }

            // Dividir en palabras (máximo 3), capitalizar
            let words = value.trim().split(/\s+/).slice(0, 3).map(word => {
                return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
            });

            if (value.endsWith(" ")) {
                nameInput.value = words.join(" ") + " ";
            } else {
                nameInput.value = words.join(" ");
            }
        });
    }
});