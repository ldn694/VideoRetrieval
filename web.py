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
from FrameRetrieval import retrieve_frames, convert_to_suggestion_input, create_suggestion, retrieve_frames_multiple_queries
import settings
import time
import chromadb

app = Flask(__name__)
app.secret_key = 'Yeu Phuong Anh<3'  # Necessary for session
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Global model variables (loaded once)
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cpu"
model, _, preprocess = open_clip.create_model_and_transforms(
    'MobileCLIP-B', pretrained='datacompdr_lt', device=device)

chroma_client = chromadb.PersistentClient(path=os.path.join(
    settings.DATA_PATH, 'AIC_db'))
collection = chroma_client.get_collection("image_embeddings")


@app.route('/')
def index():
    num_frames = session.get('num_frames', 100)  # Default to 100 if not set
    csv_filename = session.get('file_name', 'query-p1-1-kis.csv')
    return render_template('index.html',
                           num_frames=num_frames,
                           csv_filename=csv_filename)


@app.route('/submit', methods=['POST'])
def submit():
    start_time = time.time()
    # Get input values
    # get all queries from the form
    queries = [(i, query) for i, query in enumerate(
        request.form.getlist('query[]'), start=0)]
    folder_path = settings.DATA_PATH
    num_frames = int(request.form.get('num_frames'))
    csv_filename = request.form.get('file_name', 'query-p1-1-kis.csv')
    uploaded_files = request.files.getlist('images[]')
    # if upload folder does not exist, create it
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    # Process the uploaded files
    file_paths = []
    for file in uploaded_files:
        if file:
            file_path = os.path.join(
                app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            file_paths.append(file_path)
            print("Uploaded File:", file_path)

    # Process the form data as needed
    print(f"Queries: {queries}, Number of Frames: {num_frames}")
    session['num_frames'] = num_frames  # Save num_frames to session
    session['csv_filename'] = csv_filename

    # Create suggestions for clips
    suggestions = retrieve_frames_multiple_queries(
        queries, folder_path, num_frames, device, model, collection, file_paths)

    # TODO: Load all the keyframes for the suggestions
    for suggestion in suggestions:
        frames = suggestion['frames']
        highest_sim_id = 0
        for i, frame in enumerate(frames):
            video_name = frame[0]
            file_name = frame[5]
            # Load the image
            img = Image.open(os.path.join(
                folder_path, 'keyframes', video_name, file_name))
            # Convert image to base64
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            # Convert the tuple to a list, modify it, and convert it back to a tuple
            frame_list = list(frame)
            # Replace the file name with the base64 image
            frame_list[5] = img_str
            frames[i] = tuple(frame_list)
            if frame[3] > frames[highest_sim_id][3]:
                highest_sim_id = i

        suggestion['best_frame'] = highest_sim_id
        suggestion['main_frame'] = highest_sim_id

    # Load the video_id.txt file to map video names to YouTube URLs
    video_urls = load_video_urls()
    end_time = time.time()
    # Round to 2 decimal digits
    execution_time = round(end_time - start_time, 4)

    session['queries'] = queries
    session['execution_time'] = execution_time
    # save suggestions to a json file
    with open('suggestions.json', 'w') as f:
        json.dump(suggestions, f)

    return render_template(
        'index.html',
        queries=queries,
        suggestions=suggestions,
        video_urls=video_urls,
        num_frames=num_frames,
        csv_filename=csv_filename,
        execution_time=execution_time,
        sort_by="none"
    )


def load_video_urls():
    video_urls = {}
    with open(os.path.join(settings.DATA_PATH, 'video_id.txt'), 'r') as f:
        for line in f:
            video_name, video_url = line.strip().split(' ')
            video_urls[video_name] = video_url
    return video_urls


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

    map_keyframe_file = os.path.join(
        folder_path, 'map-keyframes', video_name + '.csv', )
    fps = -1
    with open(map_keyframe_file, 'r') as f:
        reader = csv.reader(f)
        keyframes = list(reader)
        fps = int(float(keyframes[1][2]))

    print(f"FPS: {fps}")

    if fps == -1:
        return {"status": "error", "message": f"Could not find FPS for video {video_name}"}

    media_info_file = os.path.join(
        folder_path, 'media-info', video_name + '.json')
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


def suggestion_sim(suggestion):
    if suggestion['main_frame'] == -1:
        return 0
    return suggestion['frames'][suggestion['main_frame']][3]

# route for sorting suggestions by best frame


@app.route('/frames', methods=['GET'])
def sort():
    sort = request.args.get('sort')
    suggestions = json.load(open('suggestions.json'))
    num_frames = session.get('num_frames', 100)  # Default to 100 if not set
    csv_filename = session.get('file_name', 'query-p1-1-kis.csv')
    queries = session.get('queries', [])
    execution_time = session.get('execution_time', None)

    if sort == 'none':
        pass
    elif sort == 'best_frame':
        for suggestion in suggestions:
            suggestion['main_frame'] = suggestion['best_frame']
    elif not len(sort) == 0:
        query_id = int(sort)
        for suggestion in suggestions:
            suggestion['main_frame'] = suggestion['max_frames'][query_id]

    suggestions = sorted(suggestions, key=suggestion_sim, reverse=True)
    return render_template('index.html',
                           queries=queries,
                           suggestions=suggestions,
                           num_frames=num_frames,
                           csv_filename=csv_filename,
                           video_urls=load_video_urls(),
                           execution_time=execution_time,
                           sort=sort)


if __name__ == '__main__':
    app.run(debug=True)
