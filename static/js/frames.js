function updateMainFrame(element, frameNumber, score, imageSrc, frames) {
	// Find the closest card element
	const card = element.closest('.card');

	// Update the main frame text
	const mainFrameElement = card.querySelector('.main-frame');
	mainFrameElement.textContent = `Frame: ${frameNumber}`;

	// update sim
	const simElement = card.querySelector('.sim');
	// round the score to 6 decimal places
	simElement.textContent = `Sim: ${parseFloat(score).toFixed(6)}`;

	// Update the image source
	if (imageSrc) {
		const imageElement = card.querySelector('.thumbnail');
		imageElement.src = imageSrc;
		// print the image source
		console.log(imageSrc);
		imageElement.type = 'button';
		imageElement.loading = 'lazy';
		imageElement.onclick = function() {
			openModal(frames);
		};
	}
}

function addFrame() {
	// Get video_name and frame_idx values from input fields
	const videoName = document.getElementById('video_name').value;
	const frameIdx = document.getElementById('frame_idx').value;

	// Validate inputs
	if (!videoName || !frameIdx) {
		alert('Video name and frame index are required.');
		return;
	}

	if (isNaN(frameIdx)) {
		alert('Frame index must be a number.');
		return;
	}

	// Create a FormData object
	const formData = new FormData();
	formData.append('video_name', videoName);
	formData.append('frame_idx', frameIdx);

	// Send the data to the server using fetch
	fetch('/add_frame', {
		method: 'POST',
		body: formData
	})
	.then(response => response.json())
	.then(data => {
		// Handle the response (show a message or update UI)
		if (data.status === "success") {
			// Add the frame to the frames section
			const framesSection = document.getElementById('framesSection');
			const url = data.suggestion['watch_url']
			const newCard = document.createElement('div');
			newCard.classList.add('suggestion', 'card', 'col-md-2');
			newCard.innerHTML = `
				<div class="card-header">
					<b class="video-name" style="width:100%">${videoName}</b>
					<button type="button" class="btn-close btn-sm btn-outline-danger float-end" aria-label="Close" onclick="deleteCard(this)"></button>
				</div>
				<div class="card-body suggestion-info">
					<p class="main-frame">Frame: ${frameIdx}</p>
					<a href="${url}" target="_blank" class="card-link">YouTube Video</a>
				</div>
			`;
			newCard.draggable = true;
			newCard.ondragstart = dragFrame;
			newCard.ondragover = allowDropFrame;
			newCard.ondrop = dropFrame;
			newCard.ondragend = onDragEndFrame;
			// add this card to the start of frames section
			framesSection.insertBefore(newCard, framesSection.firstChild);
			updateRetrievedFramesCount();
			alert(data.message + " " + data.suggestion['watch_url']);
		} else {
			alert('Failed to add frame.');
		}
	})
	.catch(error => {
		console.error('Error:', error);
		alert('An error occurred while adding the frame.');
	});
}

function sortFrame(option) {
	const sortInput = document.getElementById('sort');
	sortInput.value = option;
	const form = document.getElementById('frames-form');
	form.submit();
}

function deleteCard(button) {
	if (confirm("Are you sure you want to delete this card?")) {
		const card = button.closest('.card');
		card.remove();
		updateRetrievedFramesCount();
	}
}

function updateRetrievedFramesCount() {
	const framesSection = document.getElementById('framesSection');
	const totalFrames = framesSection.getElementsByClassName('card').length;
	const retrievedFramesElement = document.querySelector('.retrieved_frames');
	retrievedFramesElement.textContent = `Total frames: ${totalFrames}`;
}

function allowDropFrame(event) {
	event.preventDefault();
}

let draggedFrame = null;

function dragFrame(event) {
	draggedFrame = event.target.closest(".card");
	draggedFrame.classList.add("dragging");
}

function onDragEndFrame(event) {
	if (draggedFrame) {
		draggedFrame.classList.remove("dragging");
	}
}

function dropFrame(event) {
	event.preventDefault();
	const target = event.target.closest(".card");
	if (draggedFrame !== target) {
		const framesSection = document.getElementById('framesSection');
		framesSection.insertBefore(draggedFrame, target);
	}
	draggedFrame.classList.remove("dragging");
}