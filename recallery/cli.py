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
from .config import Config
from .image import ImageFile
from .revgeo import ReverseGeocoding

import argparse
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

  processor = Processor()
  processor.add_module(ReverseGeocoding(nominatim_url, nominatim_delay))

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
