from flask import Flask, render_template, request, send_file, session
import os
import torch
import open_clip
from open_clip import tokenizer
from PIL import Image
import matplotlib.pyplot as plt
import io
import base64
import json
import csv
from googletrans import Translator
from VideoRetrieval import retrieve_frames, convert_to_suggestion_input, create_suggestion, retrieve_frames_multiple_queries
import settings

app = Flask(__name__)
app.secret_key = 'Yeu Phuong Anh<3'  # Necessary for session

# In-memory cache for storing frame data
cache_query = {}
cache_frame = {}
max_cache_query_size = 10
max_cache_frame_size = 1000

# Function to translate the query


def translate_query(query):
    translator = Translator()
    translated_query = translator.translate(query, dest='en').text
    return translated_query


# Global model variables (loaded once)
device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms(
    'MobileCLIP-B', pretrained='datacompdr_lt', device=device)


@app.route('/')
def index():
    num_frames = session.get('num_frames', 100)  # Default to 100 if not set
    csv_filename = session.get('file_name', 'query-p1-1-kis.csv')
    return render_template('index.html',
                           num_frames=num_frames,
                           csv_filename=csv_filename)


@app.route('/submit', methods=['POST'])
def submit():
    # Get input values
    # get all queries from the form
    queries = [(i, query) for i, query in enumerate(
        request.form.getlist('query[]'), start=0)]
    folder_path = settings.DATA_PATH
    num_frames = int(request.form.get('num_frames'))
    csv_filename = request.form.get('file_name', 'query-p1-1-kis.csv')

    # Process the form data as needed
    print(f"Queries: {queries}, Number of Frames: {num_frames}")
    session['num_frames'] = num_frames  # Save num_frames to session
    session['csv_filename'] = csv_filename

    # if view_mode == 'frame':
    #     suggestions = retrieve_frames_multiple_queries(
    #         queries, folder_path, num_frames)
    #     # Generate a unique key for this query
    #     cache_query_key = f"{query}_{folder_path}_{num_frames}"

    #     # Check if the frames are already cached in memory
    #     if cache_query_key not in cache_query:
    #         if len(cache_query) >= max_cache_query_size:
    #             # Remove the oldest cache entry
    #             oldest_key = next(iter(cache_query))
    #             del cache_query[oldest_key]
    #         # Retrieve frames if they are not cached
    #         suggestions = retrieve_frames_multiple_queries(
    #             queries, folder_path, num_frames)
    #         # Store the frames in the global cache
    #         cache_query[cache_query_key] = (suggestions)

    #     # Load the frames from the cache
    #     suggestions = cache_query[cache_query_key]
    #     # Frame view logic
    #     images = []
    #     for suggestion in suggestions:
    #         frames = suggestion['frames']
    #         frame = find_best_frame(frames)
    #         file_name = frame[5]
    #         frame_idx = frame[1]
    #         timestamp = frame[2]
    #         sim = frame[3]
    #         minute = int(float(timestamp)) // 60
    #         second = int(float(timestamp)) % 60
    #         cache_frame_key = f"{video_name}_{file_name}"
    #         if cache_frame_key not in cache_frame:
    #             if len(cache_frame) >= max_cache_frame_size:
    #                 # Remove the oldest cache entry
    #                 oldest_key = next(iter(cache_frame))
    #                 del cache_frame[oldest_key]
    #             # Load the image
    #             img = Image.open(os.path.join(
    #                 folder_path, 'keyframes', video_name, file_name))
    #             # Convert image to base64
    #             buffered = io.BytesIO()
    #             img.save(buffered, format="JPEG")
    #             img_str = base64.b64encode(
    #                 buffered.getvalue()).decode("utf-8")
    #             cache_frame[cache_frame_key] = img_str
    #         else:
    #             img_str = cache_frame[cache_frame_key]
    #         images.append(
    #             (img_str, video_name, frame_idx, sim, minute, second))

    #     return render_template('index.html', images=images, query=query, folder_path=folder_path, num_frames=num_frames)

    # elif view_mode == 'clip':
    # Clip view logic

    # Create suggestions for clips
    suggestions = retrieve_frames_multiple_queries(
        queries, folder_path, num_frames)

    # TODO: Load all the keyframes for the suggestions
    for suggestion in suggestions:
        frames = suggestion['frames']
        frame = find_best_frame(frames)
        file_name = frame[5]
        video_name = frame[0]

        # Load the image
        img = Image.open(os.path.join(
            folder_path, 'keyframes', video_name, file_name))

        # Resize the image to a lower quality version
        # Set the desired size for the low-quality image
        max_size = (360, 240)
        img.thumbnail(max_size)

        # Convert image to base64
        buffered = io.BytesIO()
        # Set the quality parameter to reduce quality
        img.save(buffered, format="JPEG", quality=75)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        suggestion['img_str'] = img_str
        suggestion['main_frame'] = frame[1]

    # Load the video_id.txt file to map video names to YouTube URLs
    video_urls = {}
    with open('video_id.txt', 'r') as f:
        for line in f:
            video_name, video_url = line.strip().split(' ')
            video_urls[video_name] = video_url

    return render_template(
        'index.html',
        queries=queries,
        suggestions=suggestions,
        video_urls=video_urls,
        num_frames=num_frames,
        csv_filename=csv_filename
    )


def find_best_frame(frames):
    # Find the frame with the highest similarity score
    best_frame = max(frames, key=lambda x: x[3])
    return best_frame


@app.route('/download_csv', methods=['POST'])
def download_csv():
    # Receive the order from the frontend
    data = json.loads(request.form['order'])
    custom_text = request.form['custom_text']  # Receive custom text

    # Create a CSV file
    csv_filename = request.form['file_name']
    # if downloads folder does not exist, create it
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    csv_filepath = os.path.join('downloads', csv_filename)

    with open(csv_filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        for row in data:
            # If custom text is provided, add it as an extra column
            if custom_text:
                writer.writerow(
                    [row['video_name'], row['frame_idx'], custom_text])
            else:
                writer.writerow([row['video_name'], row['frame_idx']])

    # Send the file to the client using 'download_name' instead of 'attachment_filename'
    return send_file(csv_filepath, as_attachment=True, download_name=csv_filename)

@app.route('/add_frame', methods=['POST'])
def add_frame():
    # Extract video_name and frame_idx from the form data
    video_name = request.form.get('video_name')
    frame_idx = int(request.form.get('frame_idx'))
    folder_path = settings.DATA_PATH

    map_keyframe_file = os.path.join(folder_path, 'map-keyframes', video_name + '.csv', )
    fps = -1
    with open(map_keyframe_file, 'r') as f:
        reader = csv.reader(f)
        keyframes = list(reader)
        fps = int(float(keyframes[1][2]))

    print(f"FPS: {fps}")
    
    if fps == -1:
        return {"status": "error", "message": f"Could not find FPS for video {video_name}"}
    
    media_info_file = os.path.join(folder_path, 'media-info', video_name + '.json')
    watch_url = ''
    with open(media_info_file, 'r', encoding='utf-8') as f:
        media_info = json.load(f)
        watch_url = media_info['watch_url']

    if watch_url == '':
        return {"status": "error", "message": f"Could not find watch URL for video {video_name}"}

    num_seconds = frame_idx / fps
    num_seconds = int(num_seconds)
    minute = num_seconds // 60
    second = num_seconds % 60

    # Make the url start at num_seconds
    watch_url = f"{watch_url}&t={num_seconds}s"

    # Create a suggestion object
    suggestion = {
        "video_name": video_name,
        "frame_idx": frame_idx,
        "minute": minute,
        "second": second,
        "watch_url": watch_url
    }
    # Optionally, store this new frame in your current frame list or cache
    # Example: cache_frame_key = f"{video_name}_{frame_idx}"
    # cache_frame[cache_frame_key] = img

    # Return a JSON response
    return {"status": "success", "message": f"Frame added for video {video_name} at index {frame_idx}", "suggestion": suggestion}


if __name__ == '__main__':
    app.run(debug=True)
