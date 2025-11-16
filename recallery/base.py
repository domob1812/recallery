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

class Module:
  """This is a base class (mostly an interface) that defines a recallery
  module.  Modules are in charge of a particular aspect of metadata processing
  and indexing (such as reverse geocoding or face recognition)."""

  @property
  def name (self):
    """Should return a human-readable name for this module and the data
    it represents."""
    raise RuntimeError ("not implemented: name")

  @property
  def xmp_attribute (self):
    """Should return the name of the recallery custom XMP attribute that
    this module is responsible for."""
    raise RuntimeError ("not implemented: xmp_attribute")

  def process (self, img):
    """Processes the ImageFile img and returns the final value that we should
    put into this module's metadata property.  May return None if there is
    no data known."""
    raise RuntimeError ("not implemented: process")

class Processor:
  """This class bundles multiple modules together, representing the full
  recallery pipeline for processing an image in various ways (e.g. process it,
  store metadata to XMP, clear metadata, read metadata)."""

  def __init__ (self):
    self._modules = []

  def add_module (self, m):
    self._modules.append (m)

  def get_metadata (self, img):
    """Reads all existing metadata tags on the given image (for all modules)
    and returns the data as a dict (module name, data)."""

    res = {}
    for m in self._modules:
      val = img.get_custom_property (m.xmp_attribute)
      if val is not None:
        res[m.name] = val

    return res

  def clear_metadata (self, img):
    """Removes the metadata (if it exists on the file) for all modules."""
    for m in self._modules:
      img.set_custom_property (m.xmp_attribute, None)

  def process (self, img, force):
    """Processes all modules, calculating their data, and stores all the
    data into the image metadata."""

    for m in self._modules:
      if not force:
        existing = img.get_custom_property (m.xmp_attribute)
        if existing is not None:
          continue
      val = m.process (img)
      # Even if val is None, we want to write the metadata attribute, in that
      # case clearing it.
      img.set_custom_property (m.xmp_attribute, val)
