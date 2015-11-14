#!/usr/bin/env python
#
# Copyright 2013 Per Olofsson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
import subprocess
from ..Handler import Handler, HandlerError


__all__ = [
    "OutputHandler",
    "OutputHandlerError"
]


class OutputHandlerError(HandlerError):
    pass

class OutputHandler(Handler):
    """OutputHandler base class.
    
    OutputHandlers imports items into a repository, and accepts a property
    list as input, with the following keys defined:
    
        NAME        The name of the item to import.
        version     The version of the item to import.
        item_path   The path to the item to import.
    """
    
    def __init__(self, env=None, infile=None, outfile=None):
        super(OutputHandler, self).__init__(env, infile, outfile)
    
    def main(self):
        raise OutputHandlerError("Abstract method main() not implemented.")

