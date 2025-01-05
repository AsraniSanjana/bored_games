'''
if u want to test the gui on ur phone, install 'pydroid' on ur android device and run the same code there
or, make a .exe file.


to do:
add a score fn: either wrt time or #guesses allowed
add a fn to give hints
restrict the ip by having a "genre" field, so if its selected as "fruit" only 4 letter fruits are to be guessed
allow for the player to be the guesser (the current implementatio) & the word giver (the computer or the other player guesses)
maintain a highscore count calculated by 1. time taken 2. number of guesses used
increase the lexicon for generated words, restrict the ip to only sensible words
improve the gui and make it responsive for phone views (~media queries)

'''


import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from random import choice

kivy.require('2.0.0')  # replace with your Kivy version

class BullsAndCowsGame(App):
    def __init__(self, **kwargs):
        super(BullsAndCowsGame, self).__init__(**kwargs)
        self.secret_word = ""
        self.word_length = 0
        self.is_code_maker = False
        self.history_table = None

    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Button to start the game
        start_button = Button(text="Start Game", on_press=self.show_start_dialog)
        layout.add_widget(start_button)

        return layout

    def show_start_dialog(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Text input for word length
        length_label = Label(text="Enter word length:")
        content.add_widget(length_label)

        length_input = TextInput()
        content.add_widget(length_input)

        # Button to start the game
        start_button = Button(text="Start Game", on_press=lambda x: self.start_game(length_input.text))
        content.add_widget(start_button)

        # Create and open the popup
        popup = Popup(title="Game Settings", content=content, size_hint=(None, None), size=(300, 200))
        popup.open()

    def start_game(self, length_text):
        try:
            self.word_length = int(length_text)
        except ValueError:
            return  # Handle invalid input

        # Reset game variables
        self.secret_word = self.generate_random_word()

        # Close the popup
        App.get_running_app().root_window.children[0].dismiss()

        # Clear the layout
        self.root.clear_widgets()

        if self.is_code_maker:
            # Code maker's interface
            label = Label(text="Your secret word is set. Let the code breaker guess!")
            self.root.add_widget(label)
        else:
            # Code breaker's interface
            label = Label(text=f"Try to guess the {self.word_length}-letter word:",height=30)
            self.root.add_widget(label)

            guess_input = TextInput()
            self.root.add_widget(guess_input)

            guess_button = Button(text="Submit Guess", on_press=lambda x: self.check_guess(guess_input.text))
            self.root.add_widget(guess_button)

            # Display table for guess history
            self.history_table = GridLayout(cols=3, spacing=10, size_hint_y=None)
            self.history_table.bind(minimum_height=self.history_table.setter('height'))
            self.root.add_widget(self.history_table)

    def generate_random_word(self):
        # replace this with a more sophisticated word generation logic
        # words = ["cows", "word", "toes", "tail", "head", "nail"] #for 4 lettered
        words = ["fishy", "nails", "words", "heads", "frame", "photo"] #for 5 lettered
        # words = ["apples", "banana", "orange", "python", "finger", "game"] #for 6 lettered
        return choice(words)

    def check_guess(self, guess):
        if len(guess) != self.word_length:
            return  # Handle invalid input

        bulls, cows = self.calculate_bulls_and_cows(guess)

        # Display the guess, bulls, and cows in the table-like format
        guess_label = Label(text=guess)
        bulls_label = Label(text=str(bulls))
        cows_label = Label(text=str(cows))
        self.history_table.add_widget(guess_label)
        self.history_table.add_widget(bulls_label)
        self.history_table.add_widget(cows_label)

        if bulls == self.word_length:
            # The word has been guessed correctly
            label = Label(text="Congratulations! You've guessed the word.")
            self.root.add_widget(label)

    def calculate_bulls_and_cows(self, guess):
        bulls = sum(1 for s, g in zip(self.secret_word, guess) if s == g)
        cows = sum(min(self.secret_word.count(digit), guess.count(digit)) for digit in set(self.secret_word))
        cows -= bulls  # Exclude bulls from cows count
        return bulls, cows

if __name__ == '__main__':
    BullsAndCowsGame().run()
