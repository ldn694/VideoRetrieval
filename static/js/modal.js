let modelFrames = document.querySelectorAll('.modal-frame'); // Assuming frames have the class 'modal-frame'
const modal = document.getElementById('myModal');
let currentFrameIndex = 0;
var currentSuggestion = -1;
let closeButton = document.getElementById('closeModalButton');
const modalTitle = modal.querySelector('.modal-title');
const focusableElements = 'button, [tabindex="0"]';
let firstFocusableElement;
let lastFocusableElement;

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

	// Open modal with Ctrl + Shift + V
	document.addEventListener('keydown', function(event) {
		// console.log(`Key pressed: ${event.key}, Ctrl: ${event.ctrlKey}, Shift: ${event.shiftKey}`);
		if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'v') {
			if (currentSuggestion === -1) {
				// Open the modal with the first suggestion
				const firstSuggestion = document.getElementById('thumbnail-0');
				if (firstSuggestion) {
					firstSuggestion.click();
				} else {
					console.error('First suggestion not found.');
				}
			} else {
				let title = document.querySelector('.modal-title');
				let videoLink = title.querySelector('a').href;
				window.open(videoLink, '_blank');
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
	document.removeEventListener('keydown', trapFocus);
	currentSuggestion = -1;
}

// Modal Logic
function openModal(frames, index, videoLink) {
	currentSuggestion = index;
	console.log('Opening modal...');
	var modalTitle = document.querySelector('.modal-title');
	var modalBody = document.querySelector('.modal-body');
	// var sim = frames[0][3];
	// var frame = frames[0][1];
	const video = frames[0][0];
	// var query_id = frames[0][4];

	modal.style.display = "block";
	modalTitle.innerHTML = `
		<a href="${videoLink}" target="_blank">${video}</a>
	`
	modalBody.innerHTML = '';
	// loop through the frames and add them to the modal body
	for (let i = 0; i < frames.length; i++) {
		const frame = frames[i];
		modalBody.innerHTML += `
			<img class="modal-frame col-lg-2 col-md-3 col-sm-4" src=${frame[5]}
				type="button"
				onclick="sendSubmission('${video}', '${frame[2]*1000}')"
				tabindex="0">
		`;
		if (i < frames.length - 1) {
			modalBody.innerHTML += '<hr>';
		}
	}

	modelFrames = document.querySelectorAll('.modal-frame'); // Assuming frames have the class 'modal-frame'
	console.log(modelFrames.length + ' frames found');
	currentFrameIndex = 0;
    const focusableContent = modal.querySelectorAll(focusableElements);
    firstFocusableElement = focusableContent[0];
    lastFocusableElement = focusableContent[focusableContent.length - 1];
    firstFocusableElement.focus(); // Focus the first element
    document.addEventListener('keydown', trapFocus);
}

// Function to trap focus inside the modal
function trapFocus(event) {
    if (event.key === 'Tab') {
        // Shift + Tab
        if (event.shiftKey) {
            if (document.activeElement === firstFocusableElement) {
                event.preventDefault();
                lastFocusableElement.focus(); // Loop back to the last element
            }
        }
        // Tab without shift
        else {
            if (document.activeElement === lastFocusableElement) {
                event.preventDefault();
                firstFocusableElement.focus(); // Loop back to the first element
            }
        }
    }
    // Handle Enter key on focused images to simulate click
    if (event.key === 'Enter' && document.activeElement.tagName === 'IMG') {
        document.activeElement.click();
    }
}

// Example function to handle image clicks
function handleImageClick(imgElement) {
    console.log(`Image clicked: ${imgElement.alt}`);
    // Your custom logic here
}

function sendSubmission(video, timestamp) {
	const url = `http://localhost:5002/?video_name=${video}&timestamp=${timestamp}`;
	console.log('Sending submission to:', url);
	window.open(url, '_blank');
}