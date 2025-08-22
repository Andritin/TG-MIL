import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.button import Button
from kivy.clock import Clock

# Ustawia kolor tła okna dla lepszego wyglądu
Window.clearcolor = (0.95, 0.95, 0.95, 1)


class RoundedButton(Button):
    """
    Niestandardowa klasa przycisku z zaokrąglonymi rogami.
    Nadpisuje domyślne tło przycisku i rysuje zaokrąglony prostokąt.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Wyłącza domyślne tło i obramowanie przycisku Kivy, aby narysować własne
        self.background_normal = ''
        self.background_down = ''
        self.border = (0, 0, 0, 0)
        self.radius = kwargs.get('radius', [20])

        with self.canvas.before:
            # Tworzy zaokrąglony prostokąt z kolorem tła i promieniem przycisku
            self.rect_color = Color(*self.background_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

        # Powiązanie pozycji i rozmiaru przycisku w celu aktualizacji pozycji i rozmiaru prostokąta
        self.bind(pos=self.update_rect, size=self.update_rect, background_color=self.update_color)

    def update_rect(self, instance, value):
        """Aktualizuje pozycję i rozmiar zaokrąglonego prostokąta."""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def update_color(self, instance, value):
        """Aktualizuje kolor zaokrąglonego prostokąta."""
        self.rect_color.rgba = value


class MyLayout(BoxLayout):
    """
    Główny układ aplikacji, który zawiera wyświetlanie słowa i przyciski odpowiedzi.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ustawia orientację układu na pionową
        self.orientation = 'vertical'
        self.spacing = 30  # Odstępy między widżetami
        self.padding = 50  # Wypełnienie wokół zawartości

        # Słowa i ich tłumaczenia (poprawione zgodnie z terminologią branżową)
        self.words = {
            '52E': '4x4 BB Chassis 22.',
            '56E': '6x6 BB Chassis 33.',
            '56J': '6x6 BB Sattel 33.',
            '58J': '6x6 BB Sattel 40.',
            '96E': '8x8 BB Chassis 44.',
            '4PE': '8x8 BL Chassis 44.',
        }
        self.word_keys = list(self.words.keys())
        self.word_sequence = []
        self.word_index = -1
        self.current_word = ''

        # Słowniki do przechowywania poprawnych i niepoprawnych odpowiedzi
        self.correct_words = {}
        self.incorrect_words = {}

        # Zmienna do przechowywania skomponowanej odpowiedzi użytkownika
        self.composed_answer = ''

        # Główny kontener na słowo i przyciski
        self.main_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=20,
            padding=20,
        )
        self.add_widget(self.main_container)

        # Rysowanie tła kontenera
        with self.main_container.canvas.before:
            Color(0.58, 0.65, 0.73, 1)  # Delikatny, uspokajający szaroniebieski
            self.rect = RoundedRectangle(pos=self.main_container.pos, size=self.main_container.size, radius=[20])

        # Etykieta do wyświetlania słowa
        self.word_label = Label(
            text='',
            font_size='60sp',
            bold=True,
            color=(0.1, 0.1, 0.1, 1),  # Ciemnoszary tekst dla czytelności
            size_hint_y=0.2,
            halign='center',
            valign='middle'
        )
        self.main_container.add_widget(self.word_label)

        # Kontener na pola odpowiedzi (nowe ramki)
        self.answer_display_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.2,
            spacing=10,
            pos_hint={'center_x': 0.5}
        )
        self.main_container.add_widget(self.answer_display_container)

        # Kontener na wiersze przycisków
        self.button_rows_container = BoxLayout(
            orientation='vertical',
            size_hint_y=0.7,
            spacing=10,
        )
        self.main_container.add_widget(self.button_rows_container)

        # Pierwszy wiersz przycisków (typ pojazdu)
        self.row1 = BoxLayout(orientation='horizontal', spacing=10, padding=(80, 0))
        vehicle_types = ['4x4', '6x6', '8x8']
        for v_type in vehicle_types:
            btn = RoundedButton(text=v_type, font_size='30sp', size_hint=(1, 1), background_color=(0.85, 0.9, 0.95, 1),
                                color=(0.1, 0.1, 0.1, 1))
            btn.bind(on_release=self.compose_answer)
            self.row1.add_widget(btn)
        self.button_rows_container.add_widget(self.row1)

        # Drugi wiersz przycisków (seria podwozia)
        self.row2 = BoxLayout(orientation='horizontal', spacing=10, padding=(80, 0))
        chassis_series = ['BB', 'BL']
        for series in chassis_series:
            btn = RoundedButton(text=series, font_size='30sp', size_hint=(1, 1), background_color=(0.85, 0.9, 0.95, 1),
                                color=(0.1, 0.1, 0.1, 1))
            btn.bind(on_release=self.compose_answer)
            self.row2.add_widget(btn)
        self.button_rows_container.add_widget(self.row2)

        # Trzeci wiersz przycisków (Chassis i Sattel) - przywrócone
        self.row3 = BoxLayout(orientation='horizontal', spacing=10, padding=(80, 0))
        words_to_add = ['Chassis', 'Sattel']
        for word in words_to_add:
            btn = RoundedButton(text=word, font_size='30sp', size_hint=(1, 1), background_color=(0.85, 0.9, 0.95, 1),
                                color=(0.1, 0.1, 0.1, 1))
            btn.bind(on_release=self.compose_answer)
            self.row3.add_widget(btn)
        self.button_rows_container.add_widget(self.row3)

        # Czwarty wiersz przycisków (tonaż)
        self.row4 = BoxLayout(orientation='horizontal', spacing=10, padding=(80, 0))
        tonnage_buttons = ['22.', '33.', '40.', '44.']
        for tonnage in tonnage_buttons:
            btn = RoundedButton(text=tonnage, font_size='30sp', size_hint=(1, 1), background_color=(0.85, 0.9, 0.95, 1),
                                color=(0.1, 0.1, 0.1, 1))
            btn.bind(on_release=self.compose_answer)
            self.row4.add_widget(btn)
        self.button_rows_container.add_widget(self.row4)

        # Kontener na przyciski sterujące
        self.control_buttons_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.2,
            spacing=20,
            padding=(80, 0)
        )
        self.main_container.add_widget(self.control_buttons_container)

        # Przycisk "Wstecz"
        self.backspace_button = RoundedButton(
            text='<-',
            font_size='30sp',
            background_color=(0.9, 0.5, 0.4, 1),
            color=(1, 1, 1, 1),
            size_hint=(1, 1)
        )
        self.backspace_button.bind(on_release=self.backspace_answer)
        self.control_buttons_container.add_widget(self.backspace_button)

        # Przycisk "OK"
        self.ok_button = RoundedButton(
            text='OK',
            font_size='30sp',
            background_color=(0.5, 0.8, 0.5, 1),
            color=(1, 1, 1, 1),
            size_hint=(1, 1)
        )
        self.ok_button.bind(on_release=self.check_answer)
        self.control_buttons_container.add_widget(self.ok_button)

        # Etykieta z informacją zwrotną
        self.feedback_label = Label(
            text='',
            font_size='30sp',
            bold=True,
            color=(0.9, 0, 0, 1),
            size_hint_y=0.1,
            halign='center',
            valign='middle'
        )
        self.main_container.add_widget(self.feedback_label)

        # Tworzenie pojedynczej etykiety do wyświetlania odpowiedzi
        answer_label = Label(
            text='',
            font_size='30sp',
            bold=True,
            halign='center',
            valign='middle',
            color=(0.1, 0.1, 0.1, 1)
        )
        self.answer_display_container.add_widget(answer_label)
        self.answer_label = answer_label

        # Aktualizuje grafikę, gdy rozmiar kontenera się zmienia
        self.main_container.bind(pos=self.update_graphics, size=self.update_graphics)

        # Rozpoczyna nową sekwencję słów
        self.setup_new_sequence()

    def update_graphics(self, instance, value):
        """Aktualizuje pozycję i rozmiar grafiki tła."""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def setup_new_sequence(self):
        """
        Tworzy nową, losową sekwencję wszystkich słów.
        """
        self.word_keys = list(self.words.keys())
        random.shuffle(self.word_keys)
        self.word_sequence = self.word_keys
        self.word_index = -1
        self.next_word()

    def next_word(self, *args):
        """
        Wyświetla następne słowo w sekwencji. Tworzy pola odpowiedzi na podstawie długości poprawnej odpowiedzi.
        """
        self.word_index += 1
        if self.word_index >= len(self.word_sequence):
            self.show_end_message()
            return

        self.current_word = self.word_sequence[self.word_index]
        self.word_label.text = self.current_word
        self.composed_answer = ''
        self.answer_label.text = ''

        self.feedback_label.text = ''

        # Włącza przyciski
        self.ok_button.disabled = False
        self.backspace_button.disabled = False
        self.set_buttons_state(True)

    def compose_answer(self, instance):
        """
        Dodaje tekst z przycisku do skomponowanej odpowiedzi i aktualizuje pole odpowiedzi.
        Spacja jest dodawana przed nowym segmentem, jeśli odpowiedź nie jest pusta.
        """
        if self.ok_button.disabled:
            return

        # Dodaje spację przed dołączeniem, jeśli odpowiedź nie jest pusta
        if self.composed_answer:
            self.composed_answer += ' '

        self.composed_answer += instance.text
        self.answer_label.text = self.composed_answer

    def backspace_answer(self, instance):
        """
        Usuwa ostatnio wpisany znak lub segment z odpowiedzi.
        Obsługuje usuwanie ostatniego segmentu, w tym poprzedzającej go spacji.
        """
        if not self.composed_answer:
            return

        # Znajduje ostatnią spację, aby określić ostatni segment
        last_space_index = self.composed_answer.rfind(' ')
        if last_space_index != -1:
            # Usuwa ostatni segment i poprzedzającą go spację
            self.composed_answer = self.composed_answer[:last_space_index]
        else:
            # Jeśli nie znaleziono spacji, czyści całą odpowiedź
            self.composed_answer = ''

        self.answer_label.text = self.composed_answer

    def check_answer(self, instance):
        """
        Sprawdza, czy skomponowana odpowiedź jest poprawna i wyświetla informację zwrotną.
        Dodano zliczanie poprawnych odpowiedzi.
        """
        user_answer = self.composed_answer.strip()
        correct_answer = self.words[self.current_word]

        # Wyłącza przyciski
        self.ok_button.disabled = True
        self.backspace_button.disabled = True
        self.set_buttons_state(False)

        if user_answer == correct_answer:
            self.feedback_label.text = "Richtig!"
            self.feedback_label.color = (0.2, 0.6, 0.2, 1)  # Ciemniejszy, wyraźniejszy zielony
            # POPRAWKA: Dodajemy słowo do słownika poprawnych odpowiedzi
            self.correct_words[self.current_word] = self.words[self.current_word]
        else:
            self.feedback_label.text = f"Falsch. Die richtige Antwort ist: {self.words[self.current_word]}"
            self.feedback_label.color = (0.9, 0, 0, 1)  # Czerwony kolor
            self.incorrect_words[self.current_word] = self.words[self.current_word]

        # Planuje wyświetlenie następnego słowa po krótkiej przerwie
        Clock.schedule_once(self.next_word, 2)

    def set_buttons_state(self, state):
        """Ustawia stan (włączony/wyłączony) dla wszystkich przycisków do komponowania odpowiedzi."""
        for child in self.row1.children:
            child.disabled = not state
        for child in self.row2.children:
            child.disabled = not state
        for child in self.row3.children:
            child.disabled = not state
        for child in self.row4.children:
            child.disabled = not state

    def show_end_message(self, *args):
        """
        Wyświetla końcowy komunikat i podsumowanie wyników.
        """
        # Ukrywa główny kontener
        self.clear_widgets()

        # Oblicza wyniki
        total_questions = len(self.correct_words) + len(self.incorrect_words)
        correct_count = len(self.correct_words)

        # Oblicza procent, jeśli były jakieś pytania
        if total_questions > 0:
            percentage = (correct_count / total_questions) * 100
        else:
            percentage = 0

        # Przygotowuje tekst podsumowania
        summary_text = "Programm beendet!\n\n"
        summary_text += f"Ihr Ergebnis: {correct_count} / {total_questions} richtige Antworten.\n"
        summary_text += f"Prozentsatz: {percentage:.2f}%\n\n"

        if self.incorrect_words:
            summary_text += "Wörter, die wiederholt werden müssen:\n"
            for pl, en in self.incorrect_words.items():
                summary_text += f"    - {pl}: {en}\n"
        else:
            summary_text += "Herzlichen Glückwunsch! Alle Antworten waren richtig."

        # Dodaje etykietę z końcowym komunikatem
        end_label = Label(
            text=summary_text,
            font_size='30sp',
            color=(0, 0, 0, 1),
            size_hint=(1, 1),
            halign='center',
            valign='middle'
        )
        self.add_widget(end_label)

        # Dodaje przycisk wyjścia
        exit_button = RoundedButton(
            text='Beenden',
            font_size='30sp',
            background_color=(0.5, 0.5, 0.5, 1),
            size_hint=(0.3, 0.1),
            pos_hint={'center_x': 0.5, 'y': 0.1}
        )
        exit_button.bind(on_release=lambda x: App.get_running_app().stop())
        self.add_widget(exit_button)


class SampleApp(App):
    """
    Główna klasa aplikacji.
    """

    def build(self):
        """
        Metoda build zwraca główny widżet aplikacji.
        """
        return MyLayout()


if __name__ == "__main__":
    SampleApp().run()
