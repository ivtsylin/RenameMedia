import os
import re
from datetime import datetime, timedelta
import exifread
import pyheif
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

USER_DIR = "/path/to/your/directory"  # Укажите свою директорию
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".tiff", ".raw", ".heic", ".m4v", ".mov", ".mp4")


def get_creation_date(filepath):
    """Получает дату съемки файла, используя EXIF или метаданные"""
    ext = os.path.splitext(filepath)[1].lower()

    if ext in (".jpg", ".jpeg", ".tiff", ".raw"):
        return get_exif_date(filepath)
    elif ext == ".heic":
        return get_heic_date(filepath)
    elif ext in (".m4v", ".mov", ".mp4"):
        return get_video_date(filepath)

    return None


def get_exif_date(filepath):
    """Извлекает дату съемки из EXIF-данных (для JPEG, TIFF, RAW)"""
    with open(filepath, "rb") as f:
        tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
        date_taken = tags.get("EXIF DateTimeOriginal")
        if date_taken:
            return format_date(str(date_taken))
    return None


def get_heic_date(filepath):
    """Извлекает дату съемки из метаданных HEIC через pyheif"""
    heif_file = pyheif.read(filepath)
    metadata = {meta["type"]: meta["data"] for meta in heif_file.metadata}

    if b"Exif" in metadata:
        exif_data = metadata[b"Exif"]
        return extract_exif_date(exif_data)

    return None

def extract_exif_date(exif_data):
    """Извлекает дату из EXIF-данных HEIC"""
    import io
    exif_io = io.BytesIO(exif_data)
    tags = exifread.process_file(exif_io, stop_tag="EXIF DateTimeOriginal")
    date_taken = tags.get("EXIF DateTimeOriginal")

    if date_taken:
        return format_date(str(date_taken))

    return None


def get_video_date(filepath):
    """Извлекает дату съемки из метаданных видеофайла"""
    parser = createParser(filepath)
    if not parser:
        return None
    metadata = extractMetadata(parser)
    if metadata and metadata.has("creation_date"):
        result = metadata.get("creation_date")
        return (result + timedelta(hours=3)).strftime("%Y%m%d%H%M%S")
    return None


def format_date(date_str):
    """Преобразует дату в формат YYYYMMDDHHNNSS"""
    match = re.match(r"(\d+):(\d+):(\d+) (\d+):(\d+):(\d+)", date_str)
    if match:
        return f"{match[1]}{match[2]}{match[3]}{match[4]}{match[5]}{match[6]}"
    return None


def rename_files(directory):
    """Переименовывает файлы в указанной директории"""
    existing_names = {}

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        if not os.path.isfile(filepath) or not filename.lower().endswith(SUPPORTED_FORMATS):
            continue

        new_name = get_creation_date(filepath)
        if not new_name:
            continue

        ext = os.path.splitext(filename)[1].lower()
        final_name = f"{new_name}{ext}"

        # Разрешение коллизий
        counter = 1
        while final_name in existing_names:
            final_name = f"{new_name}_{counter}{ext}"
            counter += 1

        existing_names[final_name] = filepath
        new_filepath = os.path.join(directory, final_name)

        os.rename(filepath, new_filepath)
        print(f"Переименовано: {filename} → {final_name}")


USER_DIR = ""
rename_files(USER_DIR)
