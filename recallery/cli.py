#    recallery - image metadata indexing and search
#    Copyright (C) 2025  Daniel Kraft <d@domob.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .base import Processor
from .caption import Captioning
from .config import Config
from .faces import KnownFaces, processFaces
from .image import ImageFile
from .revgeo import ReverseGeocoding

import argparse
import concurrent.futures
import os
import pickle
from pathlib import Path
import sys

def main ():
  parser = argparse.ArgumentParser(description="Process image metadata")
  parser.add_argument("--datadir", default=None,
                      help="Data directory (defaults to ~/.recallery)")
  parser.add_argument("-f", "--force", action="store_true",
                      help="Force reprocessing of all metadata")
  parser.add_argument("command", nargs="?", default="process",
                      help="Command to execute (clear, show, or process)")
  parser.add_argument("files", nargs="*", help="Image files to process")

  args = parser.parse_args()

  if args.command in ["clear", "show", "process"]:
    command = args.command
    files = args.files
  else:
    command = "process"
    files = [args.command] + args.files

  if not files:
    parser.error("at least one file must be specified")

  # Load configuration
  config = Config(args.datadir)
  
  # Get reverse geocoding configuration with defaults
  nominatim_url = config.get("revgeo", "nominatim")
  if nominatim_url is None:
    nominatim_url = "nominatim.openstreetmap.org"
  
  nominatim_delay = config.get("revgeo", "delay")
  if nominatim_delay is None:
    nominatim_delay = 5
  else:
    nominatim_delay = int(nominatim_delay)

  # Get caption configuration
  caption_model = config.get("caption", "model")
  if caption_model is not None:
    caption_ollama = config.get("caption", "ollama")
    if caption_ollama is None:
      caption_ollama = "http://localhost:11434"
  
  processor = Processor()
  processor.add_module(ReverseGeocoding(nominatim_url, nominatim_delay))
  if caption_model is not None:
    processor.add_module(Captioning(caption_ollama, caption_model))

  for i, filename in enumerate(files):
    with ImageFile(filename) as f:
      if command == "clear":
        processor.clear_metadata(f)
      elif command == "process":
        print(f"Processing {filename}...", file=sys.stderr)
        processor.process(f, args.force)
      elif command == "show":
        metadata = processor.get_metadata(f)
        print(f"{filename}:")
        print()
        for module_name, value in metadata.items():
          print(f"{module_name}:")
          print(value)
          print()
        if i < len(files) - 1:
          print("=" * 80)
          print()

def _encode_face_image (task):
  person_name, image_path, model = task
  with open(image_path, "rb") as f:
    image_data = f.read()

  encodings = processFaces(image_data, model)

  if len(encodings) == 0:
    return None, f"Error: No face found in {image_path}"
  elif len(encodings) > 1:
    return None, f"Error: Multiple faces found in {image_path}"

  return (encodings[0], person_name, image_path.name), None

def mainEncodeFaces ():
  parser = argparse.ArgumentParser(description="Encode known faces for recognition")
  parser.add_argument("--datadir", default=None,
                      help="Data directory (defaults to ~/.recallery)")
  parser.add_argument("--faces", default=None,
                      help="Directory containing known faces")
  args = parser.parse_args()

  config = Config(args.datadir)

  # Get face model configuration with default
  model = config.get("faces", "model")
  if model is None:
    model = "cnn"

  if args.faces is None:
    faces_dir = config.datadir / "faces"
  else:
    faces_dir = Path(args.faces)

  if not faces_dir.exists():
    print(f"Error: Faces directory {faces_dir} does not exist", file=sys.stderr)
    sys.exit(1)

  tasks = []
  for person_dir in sorted(faces_dir.iterdir()):
    if not person_dir.is_dir():
      continue

    person_name = person_dir.name
    image_files = sorted(person_dir.glob("*.jpg")) + sorted(person_dir.glob("*.jpeg"))

    if not image_files:
      print(f"Warning: No JPEG images found for {person_name}", file=sys.stderr)
      continue

    for image_path in image_files:
      tasks.append((person_name, image_path, model))

  known_faces = KnownFaces()

  with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
    futures = {executor.submit(_encode_face_image, task): task for task in tasks}
    for future in concurrent.futures.as_completed(futures):
      task = futures[future]
      person_name, image_path, _ = task
      print(f"  {person_name}/{image_path.name}", end=" ... ", flush=True)

      result, error = future.result()
      if error:
        print(error, file=sys.stderr)
        sys.exit(1)

      encoding, name, _ = result
      known_faces.add(name, encoding)

      print("ok")

  with open(config.encoded_faces_file, "wb") as f:
    pickle.dump(known_faces, f)

  print(f"\nEncoded {len(known_faces.persons)} faces and saved to {config.encoded_faces_file}")
