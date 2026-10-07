"""Package the generated artwork as PNG and multi-resolution macOS ICNS."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
source = root / 'assets/icon-generated.png'
with Image.open(source) as artwork:
    image = artwork.convert('RGBA').resize((1024, 1024), Image.Resampling.LANCZOS)
    image.save(root / 'assets/icon.png')
    image.save(root / 'assets/icon.icns')
print('PNG and ICNS packaged from', source)
