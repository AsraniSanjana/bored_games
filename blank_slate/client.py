from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Ellipse, Color
from kivy.animation import Animation
from socketio import Client
import random

sio = Client()

class ConfettiWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.canvas = self.canvas

    def generate_confetti(self, dt):
        """Generate falling confetti."""
        with self.canvas:
            Color(random.random(), random.random(), random.random(), 1)  # Random color for each confetti
            x_pos = random.random() * self.width  # Use layout width
            y_pos = self.height  # Use layout height
            size = random.random() * 20 + 10  # Random size for confetti
            Ellipse(pos=(x_pos, y_pos), size=(size, size))

    def stop_confetti(self):
        """Clear confetti from canvas."""
        self.canvas.clear()


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=10)

        # Player Name Label (big font)
        self.player_name_label = Label(
            text="Player Name", 
            font_size=40,  # Large font size
            color=(0, 0, 1, 1),  # Blue color (RGBA format)
            size_hint_y=None, 
            height=50,
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.player_name_label)

        # Phrase Display
        self.phrase_label = Label(text="Waiting for game to start...")
        self.layout.add_widget(self.phrase_label)

        # Player Input
        self.input_box = TextInput(hint_text="Enter your word here", size_hint_y=None, height=50, multiline=False)
        self.layout.add_widget(self.input_box)

        # Submit Button
        self.submit_button = Button(text="Submit", size_hint_y=None, height=50)
        self.submit_button.bind(on_press=self.submit_answer)
        self.layout.add_widget(self.submit_button)

        # Leaderboard Display
        self.leaderboard_label = Label(text="Leaderboard will appear here", size_hint_y=None, height=300)
        self.layout.add_widget(self.leaderboard_label)

        self.add_widget(self.layout)

        self.confetti_widget = None  # Will store confetti widget reference

    def update_player_name(self, name):
        """Update the player's name label on the screen."""
        self.player_name_label.text = name    

    def update_phrase(self, phrase):
        """Update the phrase on the screen."""
        self.phrase_label.text = f"Fill in the blank: {phrase}"
        self.input_box.disabled = False
        self.submit_button.disabled = False

    def update_leaderboard(self, scores):
        """Update the leaderboard with the latest scores."""
        leaderboard_text = ""
        for name, score in scores.items():
            # Create a string of circles representing the score
            filled_circles = 'o' * score  # Green-filled circles (score)
            empty_circles = 'x' * (25 - score)  # Gray empty circles (max 25)
            leaderboard_text += f"{name}: {filled_circles}{empty_circles} ({score}/25)\n"  # Showing cumulative score

        self.leaderboard_label.text = leaderboard_text

    def show_round_result(self, leader, phrase):
        """Display round result with leader."""
        def create_popup(*args):
            popup = Popup(
                title="Round Finished",
                content=Label(
                    text=f"Phrase '{phrase}' finished! Scores updated! ",
                    halign="center",
                    valign="center",
                ),
                size_hint=(0.8, 0.4),
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 2)

        Clock.schedule_once(create_popup)

    def submit_answer(self, instance):
        """Send the player's answer to the server."""
        word = self.input_box.text.strip()
        if word:
            sio.emit("submit_answer", {
                "name": self.manager.player_name,
                "room": self.manager.room_code,
                "answer": word
            })
            self.input_box.text = ""  # Clear input after submission
            self.input_box.disabled = True  # Disable further inputs
            self.submit_button.disabled = True  # Disable submit button

    def show_confetti(self):
        """Display confetti animation for the winner."""
        if self.confetti_widget is None:
            self.confetti_widget = ConfettiWidget()
            self.layout.add_widget(self.confetti_widget)

        # Generate confetti every 0.05 seconds
        Clock.schedule_interval(self.confetti_widget.generate_confetti, 0.05)

        # Stop confetti animation after 3 seconds
        Clock.schedule_once(lambda dt: self.confetti_widget.stop_confetti(), 3)

    def stop_confetti_animation(self, dt):
        """Stop the confetti animation."""
        self.layout.clear_widgets()


class BlankSlateApp(App):
    def build(self):
        self.screen_manager = ScreenManager()

        self.main_screen = MainScreen(name="main")
        self.screen_manager.add_widget(self.main_screen)

        Clock.schedule_once(self.show_room_name_popup)

        # SocketIO Event Handlers
        sio.on("new_phrase", lambda data: self.main_screen.update_phrase(data["phrase"]))
        sio.on("update_leaderboard", lambda data: self.main_screen.update_leaderboard(data["scores"]))
        sio.on("round_end", lambda data: Clock.schedule_once(lambda dt: self.main_screen.show_round_result(data["leader"], data["phrase"])))
        # Handle game over (display winners)
        sio.on("game_over", self.handle_game_over)

        return self.screen_manager

    def handle_game_over(self, data):
        """Handle the game over event and display the winner(s)."""
        winners = data.get("winners", [])
        scores = data.get("scores", {})
        
        if winners:
            # Display winner(s)
            winners_text = " and ".join(winners)  # If multiple winners, join names with 'and'
            Clock.schedule_once(lambda dt: self.show_winner_popup(f"Game Over! Winner(s): {winners_text}"))
            Clock.schedule_once(lambda dt: self.main_screen.show_confetti(), 0.5)  # Start confetti after a slight delay
        else:
            # If no winner (just in case), show the highest scorer
            highest_scorer = max(scores, key=scores.get)
            Clock.schedule_once(lambda dt: self.show_winner_popup(f"Game Over! Winner: {highest_scorer}"))
            Clock.schedule_once(lambda dt: self.main_screen.show_confetti(), 0.5)  # Start confetti after a slight delay

    def show_winner_popup(self, message):
        """Show a popup with the winner's name."""
        layout = BoxLayout(orientation="vertical")
        label = Label(text=message)
        close_button = Button(text="Close")

        def close_popup(instance):
            popup.dismiss()

        close_button.bind(on_press=close_popup)

        layout.add_widget(label)
        layout.add_widget(close_button)

        popup = Popup(
            title="Game Over", 
            content=layout,
            size_hint=(0.8, 0.4)
        )
        popup.open()

    def show_room_name_popup(self, *args):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        name_input = TextInput(hint_text="Enter your name", multiline=False)
        room_input = TextInput(hint_text="Enter room code", multiline=False)
        submit_button = Button(text="Submit", size_hint_y=None, height=40)

        layout.add_widget(name_input)
        layout.add_widget(room_input)
        layout.add_widget(submit_button)

        popup = Popup(title="Player Info", content=layout, size_hint=(0.8, 0.4))
        submit_button.bind(on_press=lambda instance: self.submit_room_name(name_input.text, room_input.text, popup))
        popup.open()

    def submit_room_name(self, player_name, room_code, popup):
        if player_name.strip() and room_code.strip():
            self.screen_manager.player_name = player_name.strip()
            self.screen_manager.room_code = room_code.strip()
            popup.dismiss()

            # Update the player's name on the screen
            self.main_screen.update_player_name(player_name.strip())

            try:
                sio.connect("http://localhost:5000")
                sio.emit("join_room", {"name": player_name, "room": room_code})
            except Exception as e:
                self.show_error_popup("Unable to connect to server. Please try again.")

    def show_error_popup(self, message):
        popup = Popup(title="Error", content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()


if __name__ == "__main__":
    try:
        BlankSlateApp().run()
    except Exception as e:
        print(f"An error occurred: {e}")
