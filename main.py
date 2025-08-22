# -*- coding: utf-8 -*-
# File: kivy-morse-edited-29.py
# Morse code trainer with new categories and updated character table and quiz logic.

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.uix.relativelayout import RelativeLayout
from kivy.metrics import dp, sp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import random
import time

# Morse code dictionary
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.', '!': '-.-.--',
    '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...', ':': '---...',
    ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-', '_': '..--.-',
    '"': '.-..-.', '$': '...-..-', '@': '.--.-.'
}

# Categories for practice
ALPHABET_CHARS = sorted(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
NUMBERS_CHARS = sorted([char for char in MORSE_CODE_DICT.keys() if char.isdigit()])
PUNCTUATION_CHARS = sorted([char for char in MORSE_CODE_DICT.keys() if not char.isalnum()])

# Split punctuation into two categories
PUNCTUATION_CHARS_1 = PUNCTUATION_CHARS[:len(PUNCTUATION_CHARS) // 2]
PUNCTUATION_CHARS_2 = PUNCTUATION_CHARS[len(PUNCTUATION_CHARS) // 2:]

ALL_CHARS = ALPHABET_CHARS + NUMBERS_CHARS + PUNCTUATION_CHARS

CATEGORIES = {
    'Litery A-I': ALPHABET_CHARS[:9],
    'Litery J-R': ALPHABET_CHARS[9:18],
    'Litery S-Z': ALPHABET_CHARS[18:],
    'Liczby 0-9': NUMBERS_CHARS,
    'Interpunkcja (cz. 1)': PUNCTUATION_CHARS_1,
    'Interpunkcja (cz. 2)': PUNCTUATION_CHARS_2,
    'Wszystko razem': ALL_CHARS
}

# Load sound files
try:
    sound_dot = SoundLoader.load('dot.wav')
    sound_dash = SoundLoader.load('dash.wav')
    sound_correct = SoundLoader.load('correct.wav')
    sound_wrong = SoundLoader.load('wrong.wav')
except Exception as e:
    print(f"Error loading sound files: {e}")
    sound_dot = None
    sound_dash = None
    sound_correct = None
    sound_wrong = None


class StartScreen(Screen):
    """
    Start screen with buttons for category selection and a button to view the full Morse code table.
    """

    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))

        # Changed the title label text
        title_label = Label(text='Trener alfabetu Morse\'a', font_size=sp(28))
        layout.add_widget(title_label)

        for category_name in CATEGORIES.keys():
            btn = Button(text=category_name, font_size=sp(20),
                         on_press=lambda x, name=category_name: self.switch_to_practice(name))
            layout.add_widget(btn)

        # New button for the characters table
        table_btn = Button(text='Tablica wszystkich znaków', font_size=sp(20),
                           on_press=self.switch_to_characters_table)
        layout.add_widget(table_btn)

        self.add_widget(layout)

    def switch_to_practice(self, category_name):
        self.manager.get_screen('practice').set_category(category_name)
        self.manager.current = 'practice'

    def switch_to_characters_table(self, instance):
        self.manager.current = 'characters_table'


class PracticeScreen(Screen):
    """
    Practice screen for learning Morse code.
    """

    def __init__(self, **kwargs):
        super(PracticeScreen, self).__init__(**kwargs)
        self.category_name = None
        self.char_to_practice = None
        self.morse_to_input = ''
        self.is_playing_morse = False
        self.buttons = []
        self.is_ready_for_next = False

        # New quiz state management variables
        self.category_chars = []
        self.shuffled_chars = []
        self.wrong_guesses = []
        self.current_index = 0

        self.build_ui()

    def build_ui(self):
        # Builds the user interface for the practice screen.
        main_layout = RelativeLayout()

        # Counter label in the top right corner
        self.counter_label = Label(text='0/0', font_size=sp(20), size_hint=(None, None), size=(dp(100), dp(50)),
                                   pos_hint={'right': 0.95, 'top': 0.95})
        main_layout.add_widget(self.counter_label)

        # Character to translate section (moved higher)
        self.label = Label(text='Wybierz kategorię, aby zacząć', font_size=sp(60),
                           size_hint=(None, None), size=(dp(400), dp(100)), pos_hint={'center_x': 0.5, 'center_y': 0.8})
        main_layout.add_widget(self.label)

        # New label for incorrect answer feedback
        self.feedback_label = Label(text='', font_size=sp(40), size_hint=(None, None), size=(dp(400), dp(50)),
                                    pos_hint={'center_x': 0.5, 'center_y': 0.7})
        self.feedback_label.color = (1, 0, 0, 1)  # Red color for feedback
        main_layout.add_widget(self.feedback_label)

        # Morse code input section
        self.morse_input = TextInput(readonly=True, multiline=False, font_size=sp(40),
                                     size_hint=(None, None), size=(dp(250), dp(70)),
                                     pos_hint={'center_x': 0.5, 'center_y': 0.6},
                                     halign='center')
        main_layout.add_widget(self.morse_input)

        # Dot and dash buttons
        dot_dash_buttons = BoxLayout(spacing=dp(20), size_hint=(None, None), size=(dp(250), dp(100)),
                                     pos_hint={'center_x': 0.5, 'center_y': 0.4})
        self.dot_button = Button(text='.', on_press=self.on_dot_press, font_size=sp(40), size_hint=(1, 1))
        self.dash_button = Button(text='-', on_press=self.on_dash_press, font_size=sp(40), size_hint=(1, 1))
        dot_dash_buttons.add_widget(self.dot_button)
        dot_dash_buttons.add_widget(self.dash_button)
        main_layout.add_widget(dot_dash_buttons)

        # Control buttons row with Backspace and Check buttons (moved down)
        control_buttons = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint=(None, None),
                                    size=(dp(300), dp(70)),
                                    pos_hint={'center_x': 0.5, 'center_y': 0.18})  # Adjusted pos_hint
        self.backspace_button = Button(text='<', on_press=self.on_backspace_press, font_size=sp(25))
        self.check_button = Button(text='Sprawdź', on_press=self.check_input, font_size=sp(18))
        control_buttons.add_widget(self.backspace_button)
        control_buttons.add_widget(self.check_button)
        main_layout.add_widget(control_buttons)

        # Play sound button, separate line for clarity
        self.play_morse_button = Button(text='Odtwórz dźwięk', on_press=self.play_morse_sound, font_size=sp(18),
                                        size_hint=(None, None), size=(dp(150), dp(50)),
                                        pos_hint={'center_x': 0.5, 'center_y': 0.05})
        main_layout.add_widget(self.play_morse_button)

        # Button to go back to the start screen
        self.back_button = Button(text='Powrót', on_press=self.back_to_start, font_size=sp(18),
                                  size_hint=(None, None), size=(dp(120), dp(40)), pos_hint={'x': 0.05, 'y': 0.05})
        main_layout.add_widget(self.back_button)

        # Save the list of buttons for easy state management
        self.buttons = [self.dot_button, self.dash_button, self.backspace_button, self.check_button,
                        self.play_morse_button]

        self.add_widget(main_layout)

    def set_category(self, category_name):
        self.category_name = category_name
        self.category_chars = list(CATEGORIES[self.category_name])
        self.shuffled_chars = list(self.category_chars)
        random.shuffle(self.shuffled_chars)
        self.wrong_guesses = []
        self.current_index = 0
        self.update_counter_label()
        self.new_character()

    def update_counter_label(self):
        self.counter_label.text = f'{self.current_index}/{len(self.category_chars)}'

    def on_dot_press(self, instance):
        if not self.is_ready_for_next:
            self.morse_to_input += '.'
            self.morse_input.text = self.morse_to_input
            if sound_dot:
                sound_dot.play()

    def on_dash_press(self, instance):
        if not self.is_ready_for_next:
            self.morse_to_input += '-'
            self.morse_input.text = self.morse_to_input
            if sound_dash:
                sound_dash.play()

    def on_backspace_press(self, instance):
        if not self.is_ready_for_next:
            self.morse_to_input = self.morse_to_input[:-1]
            self.morse_input.text = self.morse_to_input

    def new_character(self, *args):
        if self.current_index >= len(self.shuffled_chars):
            self.show_summary()
            return

        # Clears input only when moving to a new character
        self.morse_input.text = ''
        self.morse_to_input = ''
        self.is_ready_for_next = False
        self.feedback_label.text = ''  # Clear feedback label

        self.char_to_practice = self.shuffled_chars[self.current_index]
        self.label.text = f'{self.char_to_practice}'

        self.toggle_buttons_state(True)
        self.label.color = (1, 1, 1, 1)

    def check_input(self, instance):
        if self.char_to_practice is None:
            return

        correct_morse = MORSE_CODE_DICT[self.char_to_practice]
        if self.morse_to_input == correct_morse:
            self.label.color = (0, 1, 0, 1)  # Green for correct
            if sound_correct:
                sound_correct.play()
            self.feedback_label.text = ''  # No message for correct answer
        else:
            self.label.color = (1, 0, 0, 1)  # Red for wrong
            self.feedback_label.text = f'{correct_morse}'  # Simplified feedback
            self.wrong_guesses.append((self.char_to_practice, correct_morse))
            if sound_wrong:
                sound_wrong.play()

        self.current_index += 1
        self.update_counter_label()

        self.toggle_buttons_state(False)
        self.is_ready_for_next = True

    def on_touch_down(self, touch):
        # A touch on the screen (not on a button) moves to the next character
        if self.is_ready_for_next:
            # Check if the touch is on the back button to not trigger new_character
            if self.back_button.collide_point(*touch.pos):
                return super().on_touch_down(touch)
            self.new_character()
            return True
        return super().on_touch_down(touch)

    def toggle_buttons_state(self, state):
        for btn in self.buttons:
            btn.disabled = not state
            if state:
                btn.background_color = (0.2, 0.5, 0.8, 1)
            else:
                btn.background_color = (0.5, 0.5, 0.5, 1)

    def play_morse_sound(self, instance):
        if self.char_to_practice is None:
            return

        if self.is_playing_morse:
            return

        morse_code = MORSE_CODE_DICT[self.char_to_practice]
        self.is_playing_morse = True

        def play_sequence(code, index=0):
            if index >= len(code):
                self.is_playing_morse = False
                return

            char = code[index]
            if char == '.':
                if sound_dot:
                    sound_dot.play()
                duration = 0.1
            else:
                if sound_dash:
                    sound_dash.play()
                duration = 0.3

            Clock.schedule_once(lambda dt: play_sequence(code, index + 1), duration + 0.1)

        play_sequence(morse_code)

    def show_summary(self):
        correct_count = len(self.category_chars) - len(self.wrong_guesses)
        total_count = len(self.category_chars)

        self.manager.get_screen('summary').update_summary(correct_count, total_count, self.wrong_guesses)
        self.manager.current = 'summary'

    def back_to_start(self, instance):
        self.manager.current = 'start'


class SummaryScreen(Screen):
    """
    Quiz summary screen.
    """

    def __init__(self, **kwargs):
        super(SummaryScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(10))
        self.add_widget(self.layout)

        self.title_label = Label(text='Podsumowanie', font_size=sp(28))
        self.summary_label = Label(text='', font_size=sp(22), halign='center')
        self.wrong_answers_title = Label(text='Błędne odpowiedzi:', font_size=sp(18), bold=True,
                                         pos_hint={'center_x': 0.5, 'y': 0.6})  # Moved up
        # We use a box layout with padding to create a left-aligned effect within the centered layout
        self.wrong_list_container = BoxLayout(padding=[dp(50), 0, 0, 0])
        self.wrong_list_layout = BoxLayout(orientation='vertical', spacing=dp(25), size_hint_y=None, size_hint_x=1)
        self.wrong_list_layout.bind(minimum_height=self.wrong_list_layout.setter('height'))
        self.wrong_list_container.add_widget(self.wrong_list_layout)

        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.summary_label)
        self.layout.add_widget(self.wrong_answers_title)
        self.layout.add_widget(self.wrong_list_container)

        self.restart_button = Button(text='Powrót do menu głównego', font_size=sp(18), on_press=self.go_back)
        self.layout.add_widget(self.restart_button)

    def update_summary(self, correct, total, wrong_list):
        percentage = (correct / total) * 100 if total > 0 else 0
        self.summary_label.text = f'Poprawne odpowiedzi: {correct}/{total}\nWynik: {percentage:.2f}%'

        self.wrong_list_layout.clear_widgets()
        if wrong_list:
            for char, morse in wrong_list:
                label = Label(text=f'{char}: {morse}', font_size=sp(24), halign='left', valign='middle')
                self.wrong_list_layout.add_widget(label)
        else:
            label = Label(text='Brak błędnych odpowiedzi. Gratulacje!', font_size=sp(18), halign='center')
            self.wrong_list_layout.add_widget(label)

    def go_back(self, instance):
        # This will return to the start screen, as requested.
        self.manager.current = 'start'


class AllCharactersScreen(Screen):
    """
    A screen to display a table of all Morse code characters in a three-column layout.
    """

    def __init__(self, **kwargs):
        super(AllCharactersScreen, self).__init__(**kwargs)
        main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        title = Label(text='Tablica znaków Morse\'a', font_size=sp(28), size_hint_y=None, height=dp(50))
        main_layout.add_widget(title)

        scroll_view = ScrollView(size_hint=(1, 1))
        # Use a GridLayout with 3 columns to create the three-column layout
        # Spacing reduced for a more compact view
        grid_layout = GridLayout(cols=3, spacing=dp(5), size_hint_y=None, padding=dp(10))
        grid_layout.bind(minimum_height=grid_layout.setter('height'))

        # Separate and sort characters and other symbols
        all_chars_sorted = sorted(MORSE_CODE_DICT.keys())
        letter_items = [(char, MORSE_CODE_DICT[char]) for char in all_chars_sorted if char.isalpha()]
        other_items = [(char, MORSE_CODE_DICT[char]) for char in all_chars_sorted if not char.isalpha()]
        sorted_items = letter_items + other_items

        # Add all characters to the grid
        for char, morse in sorted_items:
            # Use a horizontal BoxLayout to keep the character and Morse code on the same line
            char_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(2), 0])
            char_label = Label(text=char, font_size=sp(20), bold=True, size_hint_x=0.2, halign='left')
            morse_label = Label(text=morse, font_size=sp(18), size_hint_x=0.8, halign='left')

            char_box.add_widget(char_label)
            char_box.add_widget(morse_label)

            grid_layout.add_widget(char_box)

        scroll_view.add_widget(grid_layout)
        main_layout.add_widget(scroll_view)

        back_button = Button(text='Powrót', size_hint_y=None, height=dp(50), on_press=self.go_back)
        main_layout.add_widget(back_button)

        self.add_widget(main_layout)

    def go_back(self, instance):
        # This will return to the start screen, as requested.
        self.manager.current = 'start'


class MorseApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartScreen(name='start'))
        sm.add_widget(PracticeScreen(name='practice'))
        sm.add_widget(SummaryScreen(name='summary'))
        sm.add_widget(AllCharactersScreen(name='characters_table'))

        return sm


if __name__ == '__main__':
    MorseApp().run()
