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

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from libxmp import XMPFiles, XMPMeta
from libxmp.exempi import XMPError

# XML namespace for recallery's custom XMP properties
XMP_NS = "https://www.domob.eu/projects/recallery"
XMP_PREFIX = "recallery"

XMPMeta.register_namespace(XMP_NS, XMP_PREFIX)

class ImageFile:
  """This class represents an image file that is read or written to (metadata)
  for recallery.  It supports the required methods for that, exposing EXIF
  and XMP metadata as well as the raw file contents (to be used e.g. for sending
  to an AI model)."""

  def __init__ (self, fn):
    self.filename = fn
    self.image = Image.open(fn)
    self.xmpfile = XMPFiles(file_path=fn, open_forupdate=False)
    self.xmpfile_writable = False

  def __enter__ (self):
    return self

  def __exit__ (self, exc_type, exc_value, traceback):
    self.image.close()
    self.xmpfile.close_file()

  @property
  def raw_data (self):
    """Returns the raw file content as bytes."""
    with open(self.filename, 'rb') as f:
      return f.read()

  @property
  def user_comment (self):
    """Returns the user comment from JPEG COM as string, or None if it is
    not set."""
    comment = self.image.info.get('comment')
    if comment:
      return comment.decode('utf-8')
    return None

  @property
  def geo_coordinates (self):
    """Returns the geo coordinates (latitude, longitude in decimal degrees)
    from the image metadata or None if none are set."""
    exif_data = self.image.getexif()
    if not exif_data:
      return None

    gps_ifd = None
    for tag, name in TAGS.items():
      if name == "GPSInfo":
        gps_ifd = exif_data.get_ifd(tag)
        break

    if not gps_ifd:
      return None

    gps_info = {}
    for gps_tag, value in gps_ifd.items():
      gps_info[GPSTAGS.get(gps_tag, gps_tag)] = value

    lat = gps_info.get('GPSLatitude')
    lon = gps_info.get('GPSLongitude')
    if not lat or not lon:
      return None

    lat_decimal = float(lat[0]) + float(lat[1]) / 60.0 + float(lat[2]) / 3600.0
    lon_decimal = float(lon[0]) + float(lon[1]) / 60.0 + float(lon[2]) / 3600.0

    if gps_info.get('GPSLatitudeRef') == 'S':
      lat_decimal = -lat_decimal
    if gps_info.get('GPSLongitudeRef') == 'W':
      lon_decimal = -lon_decimal

    return lat_decimal, lon_decimal

  def get_custom_property (self, nm):
    """Returns the custom recallery XMP property with the given name or
    None if it is not set."""
    xmp = self.xmpfile.get_xmp()
    if xmp is None:
      return None
    try:
      return xmp.get_property(XMP_NS, nm)
    except XMPError:
      return None

  def set_custom_property (self, nm, val):
    """Sets or clears (val is None) the custom recallery XMP property with
    the given name on the image."""
    if not self.xmpfile_writable:
      self.xmpfile.close_file()
      try:
        self.xmpfile = XMPFiles(file_path=self.filename, open_forupdate=True)
        self.xmpfile_writable = True
      except Exception as e:
        raise RuntimeError(f"Cannot open file for writing: {e}")
    xmp = self.xmpfile.get_xmp()
    if xmp is None:
      xmp = XMPMeta()

    if val is None:
      xmp.delete_property(XMP_NS, nm)
    else:
      xmp.set_property(XMP_NS, nm, val)

    if self.xmpfile.can_put_xmp(xmp):
      self.xmpfile.put_xmp(xmp)
