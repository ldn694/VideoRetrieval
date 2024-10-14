document.addEventListener('DOMContentLoaded', (event) => {
	const themeSwitch = document.getElementById('theme');
	const body = document.body;
	const html = document.documentElement;
	const inputSection = document.querySelector('.input-section');
	const DBDropdown = document.getElementById('DBDropdown');

	// Load the dark mode preference from local storage
	const darkMode = localStorage.getItem('darkMode');
	if (darkMode === 'enabled') {
		inputSection.classList.remove('text-bg-light');
		inputSection.classList.add('text-bg-dark');

		DBDropdown.classList.remove('btn-outline-dark');
		DBDropdown.classList.add('btn-outline-light');

		body.classList.add('dark-mode');
		html.setAttribute('data-bs-theme', 'dark');
		themeSwitch.checked = true;
	}

	themeSwitch.addEventListener('click', () => {
		if (themeSwitch.checked) {
			inputSection.classList.remove('text-bg-light');
			inputSection.classList.add('text-bg-dark');

			DBDropdown.classList.remove('btn-outline-dark');
			DBDropdown.classList.add('btn-outline-light');

			body.classList.add('dark-mode');
			html.setAttribute('data-bs-theme', 'dark');
			localStorage.setItem('darkMode', 'enabled');
		} else {
			inputSection.classList.remove('text-bg-dark');
			inputSection.classList.add('text-bg-light');

			DBDropdown.classList.remove('btn-outline-light');
			DBDropdown.classList.add('btn-outline-dark');

			body.classList.remove('dark-mode');
			html.removeAttribute('data-bs-theme');
			localStorage.setItem('darkMode', 'disabled');
		}
	});

	const textAreas = document.querySelectorAll('textarea');

	textAreas.forEach(textArea => {
		textArea.addEventListener('input', function() {
			this.style.height = 'auto';
			this.style.height = (this.scrollHeight) + 'px';
		});
	});
});