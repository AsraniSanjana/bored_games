import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Ellipse, Color, Line

class RainbowCircleWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (100, 100)  # Size of the circle
        with self.canvas:
            # Draw a simple rainbow plushie-like circle using multiple arcs
            radius = 50  # Half of the circle size
            center = (50, 50)  # The center of the circle
            
            colors = [
                (1, 0, 0),  # Red
                (1, 0.5, 0),  # Orange
                (1, 1, 0),  # Yellow
                (0, 1, 0),  # Green
                (0, 0, 1),  # Blue
                (0.29, 0, 0.51),  # Indigo
                (0.93, 0.51, 0.93)  # Violet
            ]
            
            # Draw arcs for each color, creating the rainbow effect
            for i, color in enumerate(colors):
                Color(*color)
                angle = 180 * (i + 1) / len(colors)  # Spread out the colors
                Ellipse(pos=(center[0] - radius, center[1] - radius), size=(radius * 2, radius * 2), angle_start=angle, angle_end=180)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='horizontal', spacing=10)

        # Left side for the drawn rainbow circle
        self.circle_widget = RainbowCircleWidget()
        self.layout.add_widget(self.circle_widget)

        # Center content
        self.center_layout = BoxLayout(orientation='vertical', spacing=10)
        
        # Phrase Display
        self.phrase_label = Label(text="Loading phrase...")
        self.center_layout.add_widget(self.phrase_label)

        # Player Inputs
        self.player_inputs = []
        for i in range(4):  # Assume 4 players for now
            input_box = TextInput(hint_text=f"Player {i + 1}'s word")
            self.player_inputs.append(input_box)
            self.center_layout.add_widget(input_box)

        # Submit Button
        self.submit_button = Button(text="Submit")
        self.submit_button.bind(on_press=self.submit_answers)
        self.center_layout.add_widget(self.submit_button)

        # Add the center layout to the screen
        self.layout.add_widget(self.center_layout)

        # Right side for displaying the rainbow circle image
        self.image_widget = Image(source='rainbow_circle.png')  # Replace with actual image path
        self.layout.add_widget(self.image_widget)

        self.add_widget(self.layout)

    def load_new_phrase(self, phrases):
        # Select a random phrase and update the label
        self.phrase = random.choice(phrases)
        self.phrase_label.text = f"Fill in the blank: {self.phrase}"

    def submit_answers(self, instance):
        words = [input_box.text.lower() for input_box in self.player_inputs]
        matches = {word: words.count(word) for word in set(words)}
        score = sum(value for value in matches.values() if value > 1)

        # Debug: Display the words and score
        print("Words submitted:", words)
        print("Score this round:", score)

        # Optionally switch to the ScoreScreen or update scores directly
        App.get_running_app().score_screen.update_scores(score)
        App.get_running_app().screen_manager.current = "score"

class ScoreScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=10)

        # Scoreboard Display
        self.score_label = Label(text="Scores: [Player 1: 0, Player 2: 0, ...]")
        self.layout.add_widget(self.score_label)

        # Next Round Button
        self.next_round_button = Button(text="Next Round")
        self.next_round_button.bind(on_press=self.next_round)
        self.layout.add_widget(self.next_round_button)

        self.add_widget(self.layout)

    def update_scores(self, score):
        # Update the score display (example only)
        self.score_label.text = f"Updated Scores! Last score: {score}"

    def next_round(self, instance):
        # Reset for the next round
        app = App.get_running_app()
        app.main_screen.load_new_phrase(app.phrases)
        app.screen_manager.current = "main"

class BlankSlateApp(App):
    def build(self):
        # Load phrases from file
        self.phrases = self.load_phrases("phrase_list.txt")

        self.screen_manager = ScreenManager()

        # Screens
        self.main_screen = MainScreen(name="main")
        self.score_screen = ScoreScreen(name="score")
        
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.score_screen)

        # Load the first phrase
        self.main_screen.load_new_phrase(self.phrases)

        return self.screen_manager

    @staticmethod
    def load_phrases(file_path):
        try:
            import os
            print(f"Current Working Directory: {os.getcwd()}")
            print(f"File exists: {os.path.exists(file_path)}")

            with open(file_path, "r") as file:
                phrases = [line.strip() for line in file if line.strip()]
                if not phrases:
                    print("Error: The file is empty!")
                    return ["No phrases available."]
                print(f"Phrases successfully loaded: {phrases}")
                return phrases
        except FileNotFoundError:
            print(f"Error: {file_path} not found.")
            return ["No phrases available."]

if __name__ == "__main__":
    BlankSlateApp().run()
