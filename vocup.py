# coding: utf-8
"""
Vocup Dictionary.

This app allows a user to add new words to the dictionary to learn them later.
It comes with a contextual search feature.

Classes:

    UI
    MainApp

"""
import os
import sys

if sys.__stdout__ is None or sys.__stderr__ is None:
    os.environ['KIVY_NO_CONSOLELOG'] = '1'

import kivy

kivy.require('2.1.1')

import json
from difflib import get_close_matches
from pathlib import Path

from kivy.animation import Animation
from kivy.app import App
from kivy.config import Config
from kivy.resources import resource_add_path
from kivy.uix.tabbedpanel import TabbedPanel

Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '500')
Config.set('graphics', 'resizable', '0')


BASE_DIR = Path(__file__).resolve().parent
DATA = BASE_DIR / 'data/data.json'


class UI(TabbedPanel):
    """Main UI widget."""


class MainApp(App):
    """Main App."""

    title = 'vocup'
    icon = './data/icon.png'

    data: list[dict] = []
    ui = None
    current = 0

    def build(self) -> UI:
        """App startup."""
        self.read_data()
        self.ui = UI()
        self.get_word('first')
        self.hint('hide')
        return self.ui

    def read_data(self) -> None:
        """Read and setup dictionary from file."""
        if DATA.exists():
            f = DATA.read_text(encoding='utf-8')
            self.data = json.loads(f)

    def get_word(self, mode: str = 'current') -> None:
        """
        Get word attributes from JSON data.

        Then set up according UI fields.
        """
        if self.data:
            if mode == 'prev':
                self.current -= 1 if self.current > 0 else 0
            elif mode == 'next':
                self.current = (
                    self.current + 1
                    if self.current < len(self.data) - 1
                    else len(self.data) - 1
                )
            for k, v in self.data[self.current].items():
                if k == 'examples' and v:
                    v = v.replace('\n', '\n\u2022 ').replace(
                        v[0],
                        f'\u2022 {v[0]}',
                        1,
                    )
                self.ui.ids['learn_' + k].text = v

    def find_exact(self, keyword: str) -> int | None:
        """
        Search for exact or almost exact match.

        Returns: index of the word in dictionary if it's found.
        """
        startswith = None
        for i in range(len(self.data)):
            if self.data[i]['original'].lower() == keyword:
                return i
            if self.data[i]['original'].lower().startswith(keyword):
                startswith = i
        if startswith:
            return startswith
        return None

    def surface_search(self, keyword: str) -> int | None:
        """
        Search for close match.

        Returns: index of the word in dictionary if it's found.
        """
        data = [w['original'].lower() for w in self.data]
        result = get_close_matches(keyword, data, 1)
        if result:
            for i in range(len(self.data)):
                if self.data[i]['original'].lower() == result[0]:
                    return i
        return None

    def deep_search(self, keyword: str) -> int | None:
        """
        Search for close match inside each phrase.

        Returns: index of the word in dictionary if it's found.
        """
        data = [w['original'].lower() for w in self.data]
        temp = []
        for i in range(len(data)):
            if len(data[i].split()) > 1:
                match = get_close_matches(keyword, data[i].split(), 1)
                if match:
                    temp.append((match[0], i))
        if temp:
            word = get_close_matches(keyword, [t[0] for t in temp], 1)[0]
            for v, i in temp:
                if v == word:
                    return i
        return None

    def search(self) -> None:
        """Keyword search in dictionary."""
        if not self.ui.ids.search_field.text:
            self.ui.ids.search_info.text = 'Can not not be empty'
            self.ui.ids.search_info.opacity = 1
            Animation(opacity=0, duration=3).start(self.ui.ids.search_info)
            return
        if self.ui.ids.search_field.text in ('0', '-1'):
            if self.ui.ids.search_field.text == '0':
                self.current = int(self.ui.ids.search_field.text)
            else:
                self.current = len(self.data) - 1
            self.get_word()
            self.ui.switch_to(self.ui.tab_list[2])
            return
        keyword = self.ui.ids.search_field.text.lower()
        exact = self.find_exact(keyword)
        if exact is not None:
            self.current = exact
            self.get_word()
            self.ui.switch_to(self.ui.tab_list[2])
            return
        surface = self.surface_search(keyword.split()[0])
        if surface is not None:
            self.current = surface
            self.get_word()
            self.ui.switch_to(self.ui.tab_list[2])
            return
        deep = self.deep_search(keyword.split()[0])
        if deep is not None:
            self.current = deep
            self.get_word()
            self.ui.switch_to(self.ui.tab_list[2])
            return
        self.ui.ids.search_info.text = 'Nothing found'
        self.ui.ids.search_info.opacity = 1
        Animation(opacity=0, duration=3).start(self.ui.ids.search_info)

    def hint(self, mode: str) -> None:
        """Show or hide word hints."""
        self.ui.ids.learn_translation.disabled = mode == 'hide'
        self.ui.ids.learn_transcription.disabled = mode == 'hide'
        self.ui.ids.learn_examples.disabled = mode == 'hide'

    def save_data(self, data=[{'test': 'dict'}]) -> None:
        """Save data as JSON file."""
        json_string = json.dumps(data, indent=4, ensure_ascii=False)
        DATA.parent.mkdir(parents=True, exist_ok=True)
        DATA.write_text(json_string, encoding='utf-8')

    def clear_add(self) -> None:
        """Clear additional fields after adding a word."""
        self.ui.ids.add_orig.text = ''
        self.ui.ids.add_translation.text = ''
        self.ui.ids.add_transcription.text = ''
        self.ui.ids.add_examples.text = ''

    def add_word(self) -> None:
        """Add new word to the data base."""
        if not self.ui.ids.add_orig.text:
            self.ui.ids.add_exists.color = (1, 0.2, 0.2)
            self.ui.ids.add_exists.text = 'Can not be empty'
            self.ui.ids.add_exists.opacity = 1
            Animation(opacity=0, duration=3).start(self.ui.ids.add_exists)
            return
        if self.ui.ids.add_orig.text.startswith('Added: '):
            self.ui.ids.add_exists.color = (1, 0.2, 0.2)
            self.ui.ids.add_exists.text = 'Just added'
            self.ui.ids.add_exists.opacity = 1
            Animation(opacity=0, duration=3).start(self.ui.ids.add_exists)
            return
        keyword = self.ui.ids.add_orig.text.lower()
        if self.find_exact(keyword):
            self.ui.ids.add_exists.color = (1, 0.2, 0.2)
            self.ui.ids.add_exists.text = 'Already exists'
            self.ui.ids.add_exists.opacity = 1
            Animation(opacity=0, duration=3).start(self.ui.ids.add_exists)
        else:
            self.data.append(
                {
                    'original': self.ui.ids.add_orig.text,
                    'translation': self.ui.ids.add_translation.text,
                    'transcription': self.ui.ids.add_transcription.text,
                    'examples': self.ui.ids.add_examples.text,
                },
            )
            self.ui.ids.add_exists.color = (0.2, 1, 0.2)
            self.ui.ids.add_exists.text = 'Added'
            self.ui.ids.add_exists.opacity = 1
            Animation(opacity=0, duration=3).start(self.ui.ids.add_exists)
            self.ui.ids.add_orig.text = f'Added: {self.ui.ids.add_orig.text}'
            self.save_data(self.data)


if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    app = MainApp()
    app.run()
