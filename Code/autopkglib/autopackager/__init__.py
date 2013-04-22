#!/usr/bin/env python
#
# Copyright 2010 Per Olofsson
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

import imp
import os
import pprint

from autopkglib import LOCAL_OVERRIDE_KEY
from autopkglib.Processor import ProcessorError
import autopkglib

__all__ = ["AutoPackagerError", "AutoPackager"]


class AutoPackagerError(Exception):
    pass

class AutoPackager(object):
    """Instantiate and execute processors from a recipe."""

    def __init__(self, options, env):
        self.verbose = options.verbose
        self.quiet = options.quiet
        self.env = env
        self.results = []

    def output(msg, verbose_level=1):
        if self.verbose >= verbose_level:
            print msg

    def get_recipe_identifier(self, recipe):
        """Return the identifier given an input recipe plist."""
        identifier = recipe.Input.get("IDENTIFIER")
        if not identifier:
            print "ID NOT FOUND"
            # build a pseudo-identifier based on the recipe pathname
            recipe_path = self.env.get("RECIPE_PATH")
            # get rid of filename extension
            recipe_path = os.path.splitext(recipe_path)[0]
            path_parts = recipe_path.split("/")
            identifier = "-".join(path_parts)
        return identifier

    def process_input_overrides(self, recipe, cli_values):
        """Update env with 'composited' input values from overrides:
        1. Start with items in recipe's 'Input' dict
        2. Merge and overwrite any keys defined in app plist:
        <key>RecipeInputOverrides</key>
        <dict>
            <key>com.googlecode.autopkg.some_app</key>
            <dict>
                <key>MUNKI_CATALOG</key>
                <string>my_custom_catalog</string>
        3. Merge and overwrite any key-value pairs appended to the
        autopkg command invocation, of the form: NAME=value

        (3) takes precedence over (2), which takes precedence over (1)
        """

        # Set up empty container for final output
        inputs = {}
        inputs.update(recipe.Input)
        identifier = self.get_recipe_identifier(recipe)
        if self.env.get(LOCAL_OVERRIDE_KEY):
            recipe_overrides = self.env.get(LOCAL_OVERRIDE_KEY).get(identifier)
            if recipe_overrides:
                if not hasattr(recipe_overrides, "has_key"):
                    raise AutoPackagerError(
                        "Local recipe values for %s found in %s, "
                        "but is of type %s, when it should "
                        "be a dict of variables and values."
                        % (identifier, LOCAL_OVERRIDE_KEY, 
                           recipe_overrides.__class__.__name__))
                inputs.update(recipe_overrides)

        # handle CLI
        inputs.update(cli_values)
        self.env.update(inputs)

    def verify(self, recipe):
        """Verify a recipe and check for errors."""

        # Initialize variable set with input variables.
        variables = set(recipe.Input.keys())
        # Add environment.
        variables.update(set(self.env.keys()))
        recipe_dir = self.env.get('RECIPE_DIR')
        # Check each step of the process.
        for step in recipe.Process:
            # Look for the processor in the same directory as the recipe
            processor_filename = os.path.join(
                                    recipe_dir, step.Processor + '.py')
            if os.path.exists(processor_filename):
                try:
                    # attempt to import the module
                    _tmp = imp.load_source(
                        step.Processor, processor_filename)
                    # look for an attribute with the step.Processor name
                    _processor = getattr(_tmp, step.Processor)
                    # add the processor to autopkglib's namespace
                    autopkglib.add_processor(step.Processor, _processor)
                except (ImportError, AttributeError):
                    # if we aren't successful, that's OK, we're going
                    # see if the processor was already imported
                    pass
            try:
                processor_class = getattr(autopkglib, step.Processor)
            except AttributeError:
                raise AutoPackagerError(
                        "Unknown processor '%s'" % step.Processor)
            # Add arguments to set of variables.
            variables.update(set(step.Arguments.keys()))
            # Make sure all required input variables exist.
            for key, flags in processor_class.input_variables.items():
                if flags["required"] and (key not in variables):
                    raise AutoPackagerError("%s requires missing argument %s" 
                                            % (step.Processor, key))
            # Add output variables to set.
            variables.update(set(processor_class.output_variables.keys()))

    def process(self, recipe):
        """Process a recipe."""
        identifier = self.get_recipe_identifier(recipe)
        # define a cache/work directory for use by the recipe
        cache_dir = self.env.get("CACHE_DIR") or os.path.expanduser(
            "~/Library/AutoPkg/Cache")
        self.env["RECIPE_CACHE_DIR"] = os.path.join(
            cache_dir, identifier)

        recipt_input_dict = {}
        for key in self.env.keys():
            recipt_input_dict[key] = self.env[key]
        self.results.append({"Recipe input": recipt_input_dict})

        # make sure the RECIPE_CACHE_DIR exists, creating it if needed
        if not os.path.exists(self.env["RECIPE_CACHE_DIR"]):
            try:
                os.makedirs(self.env["RECIPE_CACHE_DIR"])
            except OSError, e:
                raise AutoPackagerError(
                    "Could not create RECIPE_CACHE_DIR %s: %s"
                    % (self.env["RECIPE_CACHE_DIR"], e))

        if self.verbose > 2:
            pprint.pprint(self.env)

        for step in recipe.Process:

            if self.verbose:
                print step.Processor

            processor_class = getattr(autopkglib, step.Processor)
            processor = processor_class(self.env)
            processor.inject(step.Arguments)

            input_dict = {}
            for key in processor.input_variables.keys():
                if key in processor.env:
                    input_dict[key] = processor.env[key]

            if self.verbose > 1:
                # pretty print any defined input variables
                pprint.pprint({"Input": input_dict})

            try:
                self.env = processor.process()
            except ProcessorError as e:
                print >> sys.stderr, str(e)
                raise AutoPackagerError("Recipe processing failed.")

            output_dict = {}
            for key in processor.output_variables.keys():
                output_dict[key] = self.env[key]
            if self.verbose > 1:
                # pretty print output variables
                pprint.pprint({"Output": output_dict})

            self.results.append({'Processor': step.Processor,
                                 'Input': input_dict,
                                 'Output': output_dict})

            if self.env.get("stop_processing_recipe"):
                # processing should stop now
                break

        if self.verbose > 2:
            pprint.pprint(self.env)