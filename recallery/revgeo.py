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

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

class ReverseGeocoding (Module):
  """Module that takes geo coordinates from image metadata and applies
  reverse geocoding to get a place name in text form that can then be
  attached to the image for better searching."""

  def __init__ (self, nominatim, delay=0):
    """Initialises the reverse geocoder based on a Nominatim API endpoint
    and with an optional rate-limiting delay between requests."""
    geolocator = Nominatim(user_agent="recallery", domain=nominatim)
    self.reverse = RateLimiter(geolocator.reverse, min_delay_seconds=delay)

  @property
  def name (self):
    return "Location"

  @property
  def xmp_attribute (self):
    return "RevgeoLocation"

  def process (self, img):
    coords = img.geo_coordinates
    if coords is None:
      return None
    location = self.reverse(coords)
    if location is None:
      return None
    return location.address
