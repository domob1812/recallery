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

from .base import Module

import face_recognition
import io
import numpy as np
from PIL import Image

DOWNSCALING_TARGET_PIXELS = 2_000_000

def processFaces (data, model):
  """Processes all faces (locates them and computes their encodings)
  in the given image, which is passed in-memory as a bytes string.
  Returns an array of face encodings.
  
  Uses a hybrid approach for performance:
  - Face detection runs on a downscaled image
  - Face encoding uses the full resolution image for quality
  """
  img = Image.open(io.BytesIO(data))
  img_array = np.array(img)
  
  # Get original dimensions
  height, width = img_array.shape[:2]
  original_pixels = height * width
  
  # Calculate scale factor if downscaling is needed
  if original_pixels > DOWNSCALING_TARGET_PIXELS:
    scale_factor = np.sqrt(DOWNSCALING_TARGET_PIXELS / original_pixels)
    
    # Downscale for face detection using PIL
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    img_small_pil = img.resize((new_width, new_height), Image.LANCZOS)
    img_small = np.array(img_small_pil)
    
    # Detect faces on downscaled image
    face_locations_small = face_recognition.face_locations(img_small, model=model)
    
    # Scale face locations back to original image coordinates
    face_locations = []
    for (top, right, bottom, left) in face_locations_small:
      face_locations.append((
        int(top / scale_factor),
        int(right / scale_factor),
        int(bottom / scale_factor),
        int(left / scale_factor)
      ))
  else:
    # Image is already small enough, no downscaling needed
    face_locations = face_recognition.face_locations(img_array, model=model)
  
  # Extract encodings from FULL resolution image for quality
  face_encodings = face_recognition.face_encodings(img_array, face_locations)
  return face_encodings

class KnownFaces:
  """This class represents all known faces."""

  def __init__ (self):
    self.persons = []

  def add (self, name, encoding):
    self.persons.append ({"name": name, "encoding": encoding})

class FaceDetection (Module):
  """Module that detects known faces in pictures."""

  def __init__ (self, model, tolerance, known):
    """Initialises the module with the model to use and the KnownFaces
    instance that we use as ground truth."""

    self.model = model
    self.tolerance = tolerance
    self.known = known

  @property
  def name (self):
    return "Persons"

  @property
  def xmp_attribute (self):
    return "DetectedPersons"

  def process (self, img):
    encodings = processFaces(img.raw_data, self.model)
    if not encodings:
      return None

    matches = []
    for encoding in encodings:
      best_name = None
      best_distance = float('inf')

      for person in self.known.persons:
        distance = face_recognition.face_distance([person["encoding"]], encoding)[0]
        if distance < best_distance:
          best_distance = distance
          best_name = person["name"]

      if best_name is not None:
        matches.append((best_name, best_distance))

    matches.sort(key=lambda x: x[1])
    seen = set()
    names = []
    for name, dist in matches:
      if dist > self.tolerance:
        break
      if name not in seen:
        names.append(name)
        seen.add(name)

    if names:
      return ", ".join (names)
    return None
