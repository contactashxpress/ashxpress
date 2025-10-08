    // Animation pour la force du mot de passe
    const passwordInput = document.getElementById('id_new_password1');
    const strengthBar = document.getElementById('strength-bar');
    const ruleLength = document.getElementById('rule-length');
    const ruleSpecial = document.getElementById('rule-special');
    const ruleNumber = document.getElementById('rule-number');
    const ruleUpper = document.getElementById('rule-upper');

    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;

            // Vérification des règles
            const hasLength = password.length >= 8;
            const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
            const hasNumber = /[0-9]/.test(password);
            const hasUpper = /[A-Z]/.test(password);

            // Mise à jour des icônes
            ruleLength.classList.toggle('valid', hasLength);
            ruleLength.innerHTML = hasLength ? 'check_circle' : 'circle';

            ruleSpecial.classList.toggle('valid', hasSpecial);
            ruleSpecial.innerHTML = hasSpecial ? 'check_circle' : 'circle';

            ruleNumber.classList.toggle('valid', hasNumber);
            ruleNumber.innerHTML = hasNumber ? 'check_circle' : 'circle';

            ruleUpper.classList.toggle('valid', hasUpper);
            ruleUpper.innerHTML = hasUpper ? 'check_circle' : 'circle';

            // Calcul de la force
            if (hasLength) strength += 25;
            if (hasSpecial) strength += 25;
            if (hasNumber) strength += 25;
            if (hasUpper) strength += 25;

            // Mise à jour de la barre
            strengthBar.style.width = strength + '%';

            // Changement de couleur
            if (strength < 50) {
                strengthBar.style.backgroundColor = '#ff7675';
            } else if (strength < 75) {
                strengthBar.style.backgroundColor = '#FFA500';
            } else {
                strengthBar.style.backgroundColor = '#00b894';
            }
        });
    }
