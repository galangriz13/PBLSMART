import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import lyricsgenius
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from deep_translator import GoogleTranslator
from functools import wraps
import firebase_admin
from firebase_admin import credentials, db

# === KONFIGURASI SPOTIFY & GENIUS ===
os.environ["SPOTIPY_CLIENT_ID"] = "61502a9a99fc4f0194f2aeaa7ed032c2"
os.environ["SPOTIPY_CLIENT_SECRET"] = "cb9d6b529eab451899090e73ac73ac2d"
os.environ["SPOTIPY_REDIRECT_URI"] = "http://127.0.0.1:8888/callback"
scope = "user-read-playback-state user-read-currently-playing"

GENIUS_ACCESS_TOKEN = "bJwzCCK8f1wtMr9EnCBDgEpR25df2PhfojDhCsDTv6qi0LzJlOrGy6kdKLMCVv73"

# === INISIALISASI ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, timeout=10, retries=3)
analyzer = SentimentIntensityAnalyzer()

# === INISIALISASI FIREBASE ===
firebase_cred = credentials.Certificate("pbl-smart-speaker-firebase-adminsdk-fbsvc-5a2521b3b8.json")
firebase_admin.initialize_app(firebase_cred, {
    'databaseURL': 'https://pbl-smart-speaker-default-rtdb.asia-southeast1.firebasedatabase.app/'})

# === FUNGSI ===
def retry_on_exception(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error: {e} (attempt {attempt + 1})")
                    time.sleep(delay)
            print(f"Failed after {max_retries} attempts.")
            return None
        return wrapper
    return decorator

@retry_on_exception(max_retries=3, delay=3)
def get_lyrics_from_genius(title, artist):
    song = genius.search_song(title, artist)
    if song:
        return song.lyrics
    return None

def translate_to_english(text):
    return GoogleTranslator(source='auto', target='en').translate(text)

def analyze_mood(lyrics):
    lyrics_en = translate_to_english(lyrics)
    sentiment = analyzer.polarity_scores(lyrics_en)
    score = sentiment['compound']

    if score >= 0.1:
        return "senang"
    elif score <= -0.1:
        return "sedih"
    else:
        return "biasa saja"

def kirim_ke_firebase(mood, title, artist):
    try:
        ref = db.reference("songs")
        ref.push({
            "title": title,
            "artist": artist,
            "mood": mood
        })
        print("Mood berhasil dikirim ke Firebase.")
    except Exception as e:
        print("Error kirim ke Firebase:", e)

# === MAIN LOOP ===
def main():
    last_song = None
    while True:
        try:
            current = sp.current_playback()
            if current and current["is_playing"]:
                track = current["item"]
                title = track["name"]
                artist = track["artists"][0]["name"]

                if last_song != title:
                    print(f"\nPlaying: {title} - {artist}")
                    lyrics = get_lyrics_from_genius(title, artist)
                    if lyrics:
                        print("Menganalisis mood...")
                        mood = analyze_mood(lyrics)
                        print(f"Mood lagu: {mood}")
                        kirim_ke_firebase(mood, title, artist)
                        last_song = title
                    else:
                        print("Lirik tidak ditemukan.")
            else:
                print("Tidak ada lagu yang sedang diputar.")
        except Exception as e:
            print("Error utama:", e)

        time.sleep(0.5)

if __name__ == '__main__':
    main()
