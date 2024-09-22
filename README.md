# VideoRetrieval

## Requirements
- Conda
- Python >= 3.10
- Other dependencies listed in `requirements.txt`

## How to install
Use conda environment.
```
conda create <env_name> python=3.10
conda activate <env_name>
pip install -r requirements.txt
```

In `local_settings.py`, specify `DATA_PATH` to match your data path. For example 

```py
# local_settings.py
DATA_PATH = 'E:/AIC2024/Data'
```

## How to run

```
python web.py
```

## How to use
The files in `DATA_PATH` should be organized like this
```
folder_path
|
|--keyframes
|-----------L01_V001
|-------------------001.jpg
|-------------------...
|-----------L01_V002
|-----------....
|--MobileClip
|-----------L01_V001.pt
|-----------L01_V002.pt
|-----------...
|--media-info
|-----------L01_V001.json
|-----------L01_V002.json
|-----------...
|--map-keyframes
|-----------L01_V001.csv
|-----------L01_V002.csv
|-----------...
|--AIC_db
|-----------chroma.sqlite3
|-----------<folder with .bin files>
|--video_id.txt (copy from here to the data path)
|--frame_data.json
```
