    document.addEventListener('DOMContentLoaded', function() {

        // Indicateur de force du mot de passe
        const passwordInput = document.getElementById('{{ form.password1.id_for_label }}');
        const strengthBar = document.getElementById('strength-bar');
        if (passwordInput && strengthBar) {
            passwordInput.addEventListener('input', function() {
                const password = this.value;
                let strength = 0;
                if (password.length >= 8) strength += 25;
                if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 25;
                if (/[0-9]/.test(password)) strength += 25;
                if (/[A-Z]/.test(password)) strength += 25;
                strengthBar.style.width = strength + '%';
                if (strength < 50) {
                    strengthBar.style.backgroundColor = '#d63031';
                } else if (strength < 75) {
                    strengthBar.style.backgroundColor = '#fdcb6e';
                } else {
                    strengthBar.style.backgroundColor = '#00b894';
                }
            });
        }
    });
