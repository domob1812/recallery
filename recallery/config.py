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

import configparser
import os
from pathlib import Path

class Config:
  """This class processes and handles the recallery data directory
  and config file."""

  def __init__ (self, datadir=None):
    # If datadir is None, set it to ~/.recallery by default.
    if datadir is None:
      datadir = Path.home() / ".recallery"
    else:
      datadir = Path(datadir)
    
    self.datadir = datadir
    self.config = configparser.ConfigParser()
    
    # Ensure the data directory exists
    self.datadir.mkdir(parents=True, exist_ok=True)
    
    # Open the file <datadir>/recallery.conf (if it exists) and read
    # it as INI-style config file.
    self.config_file = self.datadir / "recallery.conf"
    if self.config_file.exists():
      self.config.read(self.config_file)

  def get (self, cat, nm):
    """Returns the configuration key for a given category and name.  Returns
    None if it is not defined."""
    try:
      return self.config.get(cat, nm)
    except (configparser.NoSectionError, configparser.NoOptionError):
      return None
