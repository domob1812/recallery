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

import base64
import re
from ollama import Client

from .base import Module

PROMPT = """
Describe in a brief paragraph what this image depicts.  The description
should be suitable for indexing and searching for this image in a large
database of pictures.
"""
PROMPT_COMMENT = """
The user explicitly provided a comment for this file:
{comment}
"""

THINKING = False

class Captioning (Module):
  """A module that creates image captions / descriptions using a multimodal
  AI model running in Ollama."""

  def __init__ (self, ollama, model):
    """Initialises the captioning module based on the ollama endpoint
    and model name to use."""
    self.client = Client(host=ollama)
    self.model = model

  @property
  def name (self):
    return "Caption"

  @property
  def xmp_attribute (self):
    return "AICaption"

  def process (self, img):
    image_data = base64.b64encode(img.raw_data).decode('ascii')

    prompt = PROMPT
    comment = img.user_comment
    if comment is not None:
      prompt += PROMPT_COMMENT.format (comment=comment)

    response = self.client.chat(
      model=self.model,
      think=THINKING,
      messages=[
        {
          'role': 'user',
          'content': prompt,
          'images': [image_data]
        }
      ]
    )
    
    caption = response['message']['content']
    return caption if caption else None
