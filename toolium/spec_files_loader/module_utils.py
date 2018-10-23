# -*- coding: utf-8 -*-

u"""
Copyright 2018 Telefónica Investigación y Desarrollo, S.A.U.
This file is part of Toolium.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


def import_class_from_module_path(module_full_path, class_to_import):
    """
    Return the Python class implemented in the given module.
    :param module_full_path: Full path to the Python module (e.i: my_package.my_module)
    :param class_to_import: Class in that module to be imported
    :return: The class loaded from the module. THIS IS NOT AN INSTANCE of the class.
    """
    mod = __import__(module_full_path, fromlist=[class_to_import])
    return getattr(mod, class_to_import)
