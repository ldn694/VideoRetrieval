document.addEventListener('DOMContentLoaded', (event) => {
	const fileInput = document.getElementById('formFileMultiple');
	const imageListAccordion = document.getElementById('imageListAccordion');

	fileInput.addEventListener('change', function(event) {
		imageListAccordion.innerHTML = ''; // Clear the accordion
		// Loop through the selected files
		Array.from(fileInput.files).forEach((file, index) => {
			const reader = new FileReader();
			reader.onload = function(e) {
				// Create a new accordion item
				const accordionItem = document.createElement('div');
				accordionItem.classList.add('accordion-item');

				accordionItem.innerHTML = `
					<h2 class="accordion-header" id="heading${index}">
						<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${index}" aria-expanded="false" aria-controls="collapse${index}">
							#${index + num_queries} - ${file.name}
						</button>
					</h2>
					<div id="collapse${index}" class="accordion-collapse collapse" aria-labelledby="heading${index}" data-bs-parent="#imageListAccordion">
						<div class="accordion-body">
							<img src="${e.target.result}" loading="lazy" class="img-thumbnail" alt="Image ${file.name}">
						</div>
					</div>
				`;

				// Append the new accordion item to the beginning of the accordion
				imageListAccordion.appendChild(accordionItem);
			};

			// Read the file as a data URL
			reader.readAsDataURL(file);
			updateQueryNumbers();
		});
	});

	const showImageElement = document.getElementById('show_image');
	const showImage = localStorage.getItem('show_image');
	showImageElement.addEventListener('change', () => {
		if (showImageElement.checked) {
			localStorage.setItem('show_image', 'enabled');
		} else {
			localStorage.setItem('show_image', 'disabled');
		}
	});
	if (showImage === 'enabled') {
		showImageElement.checked = true;
	}
	else {
		showImageElement.checked = false;
	}
});