# -*- coding: utf-8 -*-
u"""
Copyright 2016 Telefónica Investigación y Desarrollo, S.A.U.
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

from selenium.webdriver.common.by import By

from toolium.pageelements import InputText, Button
from toolium.test.pageobjects.examples.base.login import BaseLoginPageObject


class AndroidLoginPageObject(BaseLoginPageObject):
    username = InputText(By.ID, 'username_id_android')
    password = InputText(By.ID, 'password_id_android')
    login_button = Button(By.ID, 'login_id_android')
