from __future__ import annotations

import os
from typing import Optional, Tuple


def recordings_dir(storage_dir: str) -> str:
    d = os.path.join(storage_dir, "recordings")
    os.makedirs(d, exist_ok=True)
    return d


def recording_temp_path(storage_dir: str, recording_id: str) -> str:
    return os.path.join(recordings_dir(storage_dir), f"{recording_id}.uploading")


def recording_final_path(storage_dir: str, recording_id: str, ext: str = "webm") -> str:
    return os.path.join(recordings_dir(storage_dir), f"{recording_id}.{ext}")


def safe_ext_from_mime(mime_type: str) -> str:
    mt = (mime_type or "").lower()
    if "webm" in mt:
        return "webm"
    if "mp4" in mt:
        return "mp4"
    return "webm"


def append_chunk(path: str, data: bytes) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "ab") as f:
        f.write(data)
    return len(data)


def finalize_upload(temp_path: str, final_path: str) -> Tuple[bool, Optional[str]]:
    try:
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        os.replace(temp_path, final_path)
        return True, None
    except Exception as e:
        return False, str(e)

