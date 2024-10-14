let modelFrames = document.querySelectorAll('.modal-frame'); // Assuming frames have the class 'modal-frame'
let currentFrameIndex = 0;
var currentSuggestion = -1;

document.addEventListener('DOMContentLoaded', (event) => {
	const modal = document.getElementById('myModal');
	const modalContent = modal.querySelector('.modal-body');

	// Function to close the modal
	function closeModal() {
		modal.style.display = 'none';
	}

	// Close the modal when clicking outside of the modal content
	window.onclick = function(event) {
		if (event.target == modal) {
			closeModal();
		}
	};

	// Close the modal when pressing the Esc key
	document.addEventListener('keydown', function(event) {
		if (event.key === 'Escape') {
			closeModal();
		}
	});

	// Scroll to the next or previous frame when pressing the down or up arrow keys
	document.addEventListener('keydown', function(event) {
		if (event.key === 'ArrowDown' | event.key === 'ArrowUp') {
			// Prevent the default behavior of the arrow keys
			event.preventDefault();
		}
		if (event.key === 'ArrowDown') {
			// Scroll to the next frame
			console.log('ArrowDown');
			if (currentFrameIndex < modelFrames.length - 1) {
				console.log('Scrolling to the next frame');
				currentFrameIndex++;
				modelFrames[currentFrameIndex].scrollIntoView({ behavior: 'instant' });
				event.preventDefault();
			}
		} else if (event.key === 'ArrowUp') {
			console.log('ArrowUp');
			// Scroll to the previous frame
			if (currentFrameIndex > 0) {
				console.log('Scrolling to the previous frame');
				currentFrameIndex--;
				modelFrames[currentFrameIndex].scrollIntoView({ behavior: 'instant' });
				event.preventDefault();
			}
		} else if (event.key === 'ArrowLeft') {
			viewPreviousSuggestion();
		} else if (event.key === 'ArrowRight') {
			viewNextSuggestion();
		}
	});
});

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
}

// Modal Logic
function openModal(frames, index) {
	currentSuggestion = index;
	console.log('Opening modal...');
	var modal = document.getElementById("myModal");
	var modelTitle = document.querySelector('.modal-title');
	var modalBody = document.querySelector('.modal-body');
	currentFrameIndex = 0;
	// var sim = frames[0][3];
	// var frame = frames[0][1];
	const video = frames[0][0];
	// var query_id = frames[0][4];

	modal.style.display = "block";
	modelTitle.textContent = `${video}`;
	modalBody.innerHTML = '';
	// loop through the frames and add them to the modal body
	for (let i = 0; i < frames.length; i++) {
		const frame = frames[i];
		modalBody.innerHTML += `
			<img class="modal-frame" src=${frame[5]} style="width:100%">
			<ul>
				<li>Sim: ${frame[3]}</li>
				<li>Frame: ${frame[1]}</li>
				<li>Timestamp: ${frame[2]}s</li>
				<li>Query ID: ${frame[4]}</li>
			</ul>
		`;
		if (i < frames.length - 1) {
			modalBody.innerHTML += '<hr>';
		}
	}

	modelFrames = document.querySelectorAll('.modal-frame'); // Assuming frames have the class 'modal-frame'
	console.log(modelFrames.length + ' frames found');
	modal.focus();
}