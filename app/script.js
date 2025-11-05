const button = document.getElementById('login-button');

button.addEventListener('click', (event) => {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;
    alert(`Email: ${email}\nSenha: ${senha}`);
});