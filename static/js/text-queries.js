function addTextarea() {
	const queryContainer = document.getElementById('query-container');
	const newTextarea = document.createElement('div');
	newTextarea.classList.add('textarea-container', 'mb-2');
	// newTextarea.draggable = true;
	// newTextarea.ondragstart = dragQuery;
	// newTextarea.ondragover = onDragOverQuery;
	// newTextarea.ondrop = dropQuery;
	// newTextarea.ondragend = dragEndQuery;
	newTextarea.innerHTML = `
		<label class="form-label mb-0" style="width:100%" for="query_${num_queries}">
			Text #${num_queries} / 
			<input type="checkbox" class="disable-textarea-checkbox" data-textarea-id="query_${num_queries}"> Disable
			<button type="button" class="btn btn-outline-danger no-outline delete-query float-end" onclick="deleteTextarea(this)">
				<i class="fa-regular fa-trash-can"></i></button>
		</label>
		<textarea type="text" id="query_${num_queries}" name="query[]" class="form-control sm-8" rows="2" placeholder="Your query" required></textarea>
	`;
	newTextarea.querySelector('textarea').addEventListener('input', function() {
		this.style.height = 'auto';
		this.style.height = (this.scrollHeight) + 'px';
	});
	queryContainer.appendChild(newTextarea);
	updateQueryNumbers();
	num_queries += 1;
}

function updateQueryNumbers() {
	const queryNumbers = document.querySelectorAll('.textarea-container .input-group-text');
	let globalIndex = 0;
	queryNumbers.forEach((queryNumber, index) => {
		queryNumber.textContent = globalIndex;
		globalIndex += 1;
	});
	const imageNumbers = document.querySelectorAll('.accordion-item .accordion-button');
	imageNumbers.forEach((imageNumber, index) => {
		imageNumber.textContent = `#${globalIndex} - ${imageNumber.textContent.split(' - ')[1]}`;
		globalIndex += 1;
	});
}

function deleteTextarea(button) {
	// remove textarea container
	button.closest('.textarea-container').remove();
	updateQueryNumbers();
	num_queries -= 1;
}

// function onDragOverQuery(event) {
// 	event.preventDefault();
// }

// let dragged = null;

// function dragQuery(event) {
// 	dragged = event.target.closest(".textarea-container");
// 	dragged.classList.add("dragging");
// }

// function dropQuery(event) {
// 	event.preventDefault();
// 	const target = event.target.closest(".textarea-container");
// 	if (dragged !== target) {
// 		const queryContainer = document.getElementById('query-container');
// 		queryContainer.insertBefore(dragged, target);
// 	}
// }

// function dragEndQuery(event) {
// 	if (dragged) {
// 		dragged.classList.remove("dragging");
// 	}
// }

