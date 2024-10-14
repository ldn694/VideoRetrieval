// Function to extract the current order and send it to the server
function extractCSV() {
	console.log('Extracting CSV...');
	var frames = document.querySelectorAll('.suggestion');
	const order = [];
	const customText = document.getElementById('custom_text').value;
	const fileName = document.getElementById('file_name').value;

	frames.forEach(frame => {
		const video_name = frame.querySelector('.video-name').textContent;
		const frame_idx = frame.querySelector('.main-frame').textContent.split(' ')[1];
		order.push({ video_name, frame_idx });
	});

	// Send the data to the server
	const formData = new FormData();
	formData.append('order', JSON.stringify(order));
	formData.append('custom_text', customText); // Pass the custom text to the backend
	formData.append('file_name', fileName); // Pass the file name to the backend
	
	fetch('/download_csv', {
		method: 'POST',
		body: formData
	})
	.then(response => response.blob())
	.then(blob => {
		// Create a link to download the file
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = fileName;
		document.body.appendChild(a);
		a.click();
		a.remove();
	});
}