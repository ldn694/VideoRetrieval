let modelFrames = document.querySelectorAll('.modal-frame'); // Assuming frames have the class 'modal-frame'
const modal = document.getElementById('myModal');
let currentFrameIndex = 0;
var currentSuggestion = -1;
let closeButton = document.getElementById('closeModalButton');

document.addEventListener('DOMContentLoaded', (event) => {
	const modalBody = modal.querySelector('.modal-body');

	// Function to close the modal
	function closeModal() {
		modal.style.display = 'none';
	}

	// Close the modal when clicking outside of the modal content
	window.onclick = function(event) {
		if (event.target == modal) {
			closeButton.click();
		}
	};

	// Close the modal when pressing the Esc key
	document.addEventListener('keydown', function(event) {
		if (event.key === 'Escape') {
			closeButton.click();
		}
	});

	// Open modal with Ctrl + V
	document.addEventListener('keydown', function(event) {
		if (event.ctrlKey && event.key === 'v') {
			// Open the modal with the first suggestion
			const firstSuggestion = document.getElementById('thumbnail-0');
			if (firstSuggestion) {
				firstSuggestion.click();
			} else {
				console.error('First suggestion not found.');
			}
		}
	});

	// Scroll to the next or previous frame when pressing the down or up arrow keys
	document.addEventListener('keydown', function(event) {
		if (event.key === 'ArrowLeft' | event.key === 'ArrowRight') {
			// Prevent the default behavior of the arrow keys
			event.preventDefault();
		}
		// if (event.key === 'ArrowDown') {
		// 	// Scroll to the next frame
		// 	console.log('ArrowDown');
		// 	if (currentFrameIndex < modelFrames.length - 1) {
		// 		console.log('Scrolling to the next frame');
		// 		currentFrameIndex++;
		// 		modelFrames[currentFrameIndex].scrollIntoView({ behavior: 'instant' });
		// 		event.preventDefault();
		// 	}
		// } else if (event.key === 'ArrowUp') {
		// 	console.log('ArrowUp');
		// 	// Scroll to the previous frame
		// 	if (currentFrameIndex > 0) {
		// 		console.log('Scrolling to the previous frame');
		// 		currentFrameIndex--;
		// 		modelFrames[currentFrameIndex].scrollIntoView({ behavior: 'instant' });
		// 		event.preventDefault();
		// 	}
		// } else 
		if (event.key === 'ArrowLeft') {
			viewPreviousSuggestion();
		} else if (event.key === 'ArrowRight') {
			viewNextSuggestion();
		}
	});
});

function updateCurrentModalFrame() {
	// check if modal is opened
	if (currentSuggestion === -1) {
		return;
	}
	const cards = modelFrames;
	let closestCardIndex = 0;
	let closestCardDistance = Infinity;
	const modal = document.getElementById("myModal");;

	cards.forEach((card, i) => {
		const rect = card.getBoundingClientRect();
		const distance = Math.abs(rect.top + modal.getBoundingClientRect().top);
		// console.log(distance);
		if (distance < closestCardDistance) {
			closestCardDistance = distance;
			closestCardIndex = i;
		}
	});

	currentFrameIndex = closestCardIndex;
	console.log('Current Frame Index:', currentFrameIndex);
}

function viewNextSuggestion() {
	if (currentSuggestion === -1) {
		return;
	}
	const suggestions = document.querySelectorAll('.suggestion');
	if (currentSuggestion < suggestions.length - 1) {
		currentSuggestion++;
		triggerThumbnailClick(currentSuggestion);
	}
}

function viewPreviousSuggestion() {
	if (currentSuggestion === -1) {
		return;
	}
	if (currentSuggestion > 0) {
		currentSuggestion--;
		triggerThumbnailClick(currentSuggestion);
	}
}

function triggerThumbnailClick(index) {
	const thumbnail = document.getElementById(`thumbnail-${index}`);
	if (thumbnail) {
		thumbnail.click();
	} else {
		console.error(`Thumbnail with index ${index} not found.`);
	}
}

function closeModal() {
	var modal = document.getElementById("myModal");
	modal.style.display = "none";
	currentSuggestion = -1;
	console.log(currentSuggestion)
}

// Modal Logic
function openModal(frames, index, videoLink) {
	currentSuggestion = index;
	console.log('Opening modal...');
	// get the index-th suggestion
	const card = document.getElementById(`suggestion-${index}`);

	var modal = document.getElementById("myModal");
	var modelTitle = document.querySelector('.modal-title');
	var modalBody = document.querySelector('.modal-body');
	// var sim = frames[0][3];
	// var frame = frames[0][1];
	const video = frames[0][0];
	// var query_id = frames[0][4];

	modal.style.display = "block";
	modelTitle.innerHTML = `
		<a href="${videoLink}" target="_blank">${video}</a>
	`
	modalBody.innerHTML = '';
	// loop through the frames and add them to the modal body
	for (let i = 0; i < frames.length; i++) {
		const frame = frames[i];
		const onclick = `updateMainFrame(${frame[1]}, ${frame[3]}, "${frame[5]}", "${index}", ${JSON.stringify(frames).replace(/"/g, '&quot;')})`;
		modalBody.innerHTML += `
			<img class="modal-frame col-lg-2 col-md-3 col-sm-4 p-1" src=${frame[5]}
				type="button"
				onclick="sendSubmission('${video}', '${frame[2]*1000}')">
		`;
		if (i < frames.length - 1) {
			modalBody.innerHTML += '<hr>';
		}
	}

	modelFrames = document.querySelectorAll('.modal-frame'); // Assuming frames have the class 'modal-frame'
	console.log(modelFrames.length + ' frames found');
	modal.focus();
	currentFrameIndex = 0;
	modelFrames[currentFrameIndex].scrollIntoView({ behavior: 'instant' });
}

function sendSubmission(video, timestamp) {
	const url = `http://localhost:5002/?video_name=${video}&timestamp=${timestamp}`;
	console.log('Sending submission to:', url);
	window.open(url, '_blank');
}