from pathlib import Path
from tempfile import NamedTemporaryFile

def write_temp_file(filename:str, content:bytes) -> Path:
    suffix = Path(filename).suffix
    tmp = NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)
