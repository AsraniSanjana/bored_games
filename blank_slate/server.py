import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO, emit, join_room
import random

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

# Game data
players = {}  # {room_code: {player_name: score}}
rooms = {}  # {room_code: {players: [list of player names], phrases: [list of phrases], current_phrase: int, answers: []}}
phrases = ["hand_", "_belly", "card_", "holy_", "ear_" , "black_", "_cream", "nail_", "frost_", "pink_", "baby_"]
WORDS_PER_GAME = min(len(phrases), 11)  # Max 5 words or fewer if phrases are limited

@socketio.on('connect')
def on_connect():
    print("Client connected.")

@socketio.on('join_room')
def on_join_room(data):
    player_name = data["name"]
    room_code = data["room"]

    if room_code not in rooms:
        rooms[room_code] = {"players": [], "phrases": [], "current_phrase": 0, "answers": []}

    if player_name not in rooms[room_code]["players"]:
        rooms[room_code]["players"].append(player_name)
        if room_code not in players:
            players[room_code] = {}
        players[room_code][player_name] = 0  # Initialize score for player

    join_room(room_code)
    print(f"Player {player_name} joined room {room_code}.")
    emit("update_leaderboard", {"scores": players[room_code]}, room=room_code)

    # Automatically start game if 4 players are in the room
    if len(rooms[room_code]["players"]) == 4:
        start_game(room_code)

def start_game(room_code):
    """Start the game for a room."""
    rooms[room_code]["phrases"] = random.sample(phrases, WORDS_PER_GAME)
    rooms[room_code]["current_phrase"] = 0
    emit("update_leaderboard", {"scores": players[room_code]}, room=room_code)
    next_phrase(room_code)
def next_phrase(room_code):
    print(f"Checking scores for room {room_code}: {players[room_code]}")

    """Send the next phrase or end the game."""
    current_phrase_index = rooms[room_code]["current_phrase"]
    
    # Check if any player has already won
    winners = [player for player, score in players[room_code].items() if score >= 25]
    
    if winners:
        # If there are winners, declare the game over immediately
        emit("game_over", {"scores": players[room_code], "winners": winners}, room=room_code)
        print(f"Game over for room {room_code}. Winners: {', '.join(winners)}")
        return  # Exit the function here so no further phrases are processed

    if current_phrase_index < WORDS_PER_GAME:
        # If no winners, continue to the next phrase
        rooms[room_code]["answers"] = []
        next_phrase = rooms[room_code]["phrases"][current_phrase_index]
        emit("new_phrase", {"phrase": next_phrase}, room=room_code)
    else:
        # If no winner after all phrases, declare the winner with the highest score
        winner = max(players[room_code], key=lambda p: players[room_code][p], default=None)
        emit("game_over", {"scores": players[room_code], "winner": winner}, room=room_code)
        print(f"Game over for room {room_code}. Winner: {winner}")

    # Move to the next phrase for the next round
    rooms[room_code]["current_phrase"] += 1

@socketio.on('submit_answer')
def on_submit_answer(data):
    room_code = data["room"]
    player_name = data["name"]
    answer = data["answer"].strip().lower()

    if room_code not in rooms or player_name not in players[room_code]:
        return

    # Prevent duplicate submissions
    if any(player_name == player for player, _ in rooms[room_code]["answers"]):
        return

    print(f"Received answer from {player_name} in room {room_code}: {answer}")
    rooms[room_code]["answers"].append((player_name, answer))

    # Wait until all players submit their answers
    if len(rooms[room_code]["answers"]) == len(rooms[room_code]["players"]):
        # All answers received, calculate scores
        calculate_scores(room_code)
        emit("update_leaderboard", {"scores": players[room_code]}, room=room_code)

        # Announce round result
        leader = max(players[room_code], key=lambda p: players[room_code][p], default=None)
        emit("round_end", {"leader": leader, "phrase": rooms[room_code]["phrases"][rooms[room_code]["current_phrase"]]}, room=room_code)

        # Move to the next phrase
        rooms[room_code]["current_phrase"] += 1
        next_phrase(room_code)

def calculate_scores(room_code):
    """Calculate scores for a round."""
    answers = [answer for _, answer in rooms[room_code]["answers"]]
    
    # Create a dictionary of how many times each answer was given
    word_count = {word: answers.count(word) for word in set(answers)}
    
    # If all players wrote the same word, assign 0 points to everyone
    if len(word_count) == 1:  # All players wrote the same word
        for player in rooms[room_code]["players"]:
            players[room_code][player] += 0
    else:
        # Assign points based on the number of occurrences
        for word, count in word_count.items():
            if count == 2:
                points = 15
            elif count > 2:
                points = 1
            else:
                continue  # No points for unique or unmatched answers

            # Award points to players who submitted the word
            for player, answer in rooms[room_code]["answers"]:
                if answer == word:
                    players[room_code][player] += points

    # Send updated leaderboard to all players
    emit("update_leaderboard", {"scores": players[room_code]}, room=room_code)
    print(players[room_code])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
