def get_file_path_from_mpris_url(mpris_url: str) -> str:
    return mpris_url.replace("file://", "")