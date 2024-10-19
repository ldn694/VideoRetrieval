from flask import Flask, render_template, request, send_file, session, url_for
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
import subprocess
import atexit
import signal
import socket

app = Flask(__name__)
app.secret_key = 'Yeu Phuong Anh<3'  # Necessary for session
app.static_folder = 'static'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Global model variables (loaded once)
# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cpu"
model, _, preprocess = open_clip.create_model_and_transforms(
    'MobileCLIP-B', pretrained='datacompdr_lt', device=device)

transparent_image = None
server_process = None


def getTransparentImage():
    global transparent_image
    if transparent_image is None:
        # Create a 1x1 image with RGBA mode and fully transparent (0, 0, 0, 0)
        transparent_image = Image.new("RGB", (1, 1), (0, 0, 0))
    return transparent_image


chroma_client = chromadb.PersistentClient(path=os.path.join(
    settings.DATA_PATH, 'AIC_db'))
collection_12_new = chroma_client.get_collection("image_embeddings_new")
collection_12_old = chroma_client.get_collection("image_embeddings")
collection_3_new = chroma_client.get_collection("b3_new")
collection_3_old = chroma_client.get_collection("b3_baseline")
collection_3_new_refine = chroma_client.get_collection("b3_new_refine")

def get_collection(keyframes_name):
    if keyframes_name == '12_new':
        return collection_12_new, "keyframes_new"
    elif keyframes_name == '12_old':
        return collection_12_old, "keyframes"
    elif keyframes_name == '3_new':
        return collection_3_new, "keyframes_new"
    elif keyframes_name == '3_old':
        return collection_3_old, "keyframes"
    elif keyframes_name == '3_refined':
        # do sth 
        return collection_3_new_refine, "keyframes_new"
    else:
        return None


@app.route('/')
def index():
    num_frames = session.get('num_frames', 200)  # Default to 100 if not set
    csv_filename = session.get('file_name', 'query-p1-1-kis.csv')
    queries = session.get('queries', [(0, '')])
    query_disable = session.get('query_disable', [])
    return render_template('index.html',
                           num_frames=num_frames,
                           csv_filename=csv_filename,
                           queries=queries,
                           query_disable=query_disable,
                           sort="none")


@app.route('/submit', methods=['POST'])
def submit():
    start_time = time.time()
    # Get input values
    # get all queries from the form
    queries = [(i, query) for i, query in enumerate(
        request.form.getlist('query[]'), start=0)]
    query_disable = [int(id) for id in request.form.getlist('query_disable[]')]
    folder_path = settings.DATA_PATH
    num_frames = int(request.form.get('num_frames'))
    csv_filename = request.form.get('file_name', 'query-p1-1-kis.csv')
    uploaded_files = request.files.getlist('images[]')
    db_mode = request.form.get('db_mode')
    show_image = request.form.get('show_image')
    is_show_image = show_image is not None
    keyframes = request.form.get('keyframes')
    print("Keyframes:", keyframes, "; DB Mode: ", db_mode)
    print("Disable queries:", query_disable)
    
    collection, keyframes_name = get_collection(keyframes)

    # if upload folder does not exist, create it
    if not os.path.exists(os.path.join(app.static_folder, app.config['UPLOAD_FOLDER'])):
        os.makedirs(os.path.join(app.static_folder,
                    app.config['UPLOAD_FOLDER']))
    # Process the uploaded files
    file_paths = []
    for file in uploaded_files:
        if file:
            file_path = os.path.join(app.static_folder,
                                     app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            file_paths.append(file_path)
            print("Uploaded File:", file_path)

    # Process the form data as needed
    session['num_frames'] = num_frames  # Save num_frames to session
    session['csv_filename'] = csv_filename
    session['query_disable'] = query_disable
    
    # Create suggestions for clips
    enabled_queries = [(i, query) for (i, query) in queries if i not in query_disable]
    suggestions = retrieve_frames_multiple_queries(
        enabled_queries, folder_path, num_frames, device, model, collection, file_paths, preprocess, db_mode)

    map_id = generate_map_id(query_disable, len(queries))
    for suggestion in suggestions:
        frames = suggestion['frames']
        highest_sim_id = 0
        for i, frame in enumerate(frames):
            video_name = frame[0]
            file_name = frame[5]
            if is_show_image:
                # # Load the image
                local_ip = socket.gethostbyname(socket.gethostname())
                if video_name[:3] == "L25" and keyframes == "3_new":
                    main_name = "keyframes_new_tmp"
                else:
                    main_name = keyframes_name
                img_str = os.path.join(
                     f'http://localhost:8000', main_name, video_name, file_name)
                img_str = '/'.join(img_str.split('\\'))
            else:
                #  # Generate a transparent image and convert it to base64
                img_str = ""
            # Convert the tuple to a list, modify it, and convert it back to a tuple
            frame_list = list(frame)
            # Replace the file name with the base64 image
            frame_list[4] = map_id[frame_list[4]]
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
    session['db_mode'] = db_mode
    session['image_paths'] = file_paths
    # save suggestions to a json file
    with open('suggestions.json', 'w') as f:
        json.dump(suggestions, f)

    image_queries = get_img_str_from_paths(file_paths, len(queries))

    return render_template(
        'index.html',
        queries=queries,
        query_disable=query_disable,
        image_queries=image_queries,
        suggestions=suggestions,
        video_urls=video_urls,
        num_frames=num_frames,
        csv_filename=csv_filename,
        execution_time=execution_time,
        db_mode=db_mode,
        sort="none"
    )


def generate_map_id(query_disable, num_queries):
    map_id = {}
    retrieved_id = 0
    for i in range(num_queries):
        if i not in query_disable:
            map_id[retrieved_id] = i
            print(f"Map id {retrieved_id} to {i}")
            retrieved_id += 1
    return map_id

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


def get_img_str_from_paths(file_paths, num_text_queries):
    image_queries = []
    for i, file_path in enumerate(file_paths):
        # img = Image.open(file_path)
        # # resize the image to 1280 width while keeping the aspect ratio
        # img.thumbnail((1280, 1280))
        # buffered = io.BytesIO()
        # img.save(buffered, format="JPEG")
        # join current path of this file with the file path
        file_name = os.path.basename(file_path)
        img_str = url_for(
            'static', filename=f"{app.config['UPLOAD_FOLDER']}/{file_name}")
        print("Image Path:", img_str)
        image_queries.append(
            {"index": i + num_text_queries, "name": file_name, "image": img_str})
    return image_queries


@app.route('/download_csv', methods=['POST'])
def download_csv():
    # Receive the order from the frontend
    data = json.loads(request.form['order'])
    custom_text = request.form['custom_text']  # Receive custom text

    # Create a CSV file
    csv_filename = request.form['file_name']
    session['file_name'] = csv_filename  # Save the file name to session
    # if downloads folder does not exist in static, create it
    if not os.path.exists(os.path.join(app.static_folder, 'downloads')):
        os.makedirs(os.path.join(app.static_folder, 'downloads'))
    csv_filepath = os.path.join(app.static_folder, 'downloads', csv_filename)

    with open(csv_filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        if custom_text:
            wrote = 0
            ans_list = [ans.strip() for ans in custom_text.split(',')]
            print(ans_list)
            for row in data[:100]:  # Limit to 100 rows
                for ans in ans_list:
                    if wrote >= 100:
                        break
                    writer.writerow(
                        [row['video_name'], row['frame_idx'], ans])
                    wrote += 1
        else:
            for row in data[:100]:
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
    num_frames = session.get('num_frames', 200)  # Default to 100 if not set
    csv_filename = session.get('file_name', 'query-p1-1-kis.csv')
    queries = session.get('queries', [(0, '')])
    file_paths = session.get('image_paths', [])
    execution_time = session.get('execution_time', None)
    image_queries = get_img_str_from_paths(file_paths, len(queries))

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
                           image_queries=image_queries,
                           query_disable=session.get('query_disable', []),
                           suggestions=suggestions,
                           num_frames=num_frames,
                           csv_filename=csv_filename,
                           video_urls=load_video_urls(),
                           execution_time=execution_time,
                           db_mode=session.get('db_mode', 'none'),
                           sort=sort)


if __name__ == '__main__':
    app.run(debug=True)
