import typer
import spotipy
import yaml
import json
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path

app = typer.Typer()

CONFIG_PATH = Path("config.override.yaml")
TRACKS_OUTPUT_PATH = Path("tracks.json")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def get_spotify_client(cfg):
    auth_manager = SpotifyOAuth(
        client_id=cfg["spotify"]["client_id"],
        client_secret=cfg["spotify"]["api_key"],
        redirect_uri="http://127.0.0.1:9090/callback",
        scope="playlist-read-private",
        open_browser=True  # Or False if using WSL
    )
    return spotipy.Spotify(auth_manager=auth_manager)

def get_playlist_tracks(sp: spotipy.Spotify, playlist_id: str):
    tracks = []
    results = sp.playlist_items(playlist_id, limit=100)
    tracks.extend(results["items"])
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    return tracks

@app.command()
def auth():
    """Authenticate with Spotify and print user info."""
    cfg = load_config()
    sp = get_spotify_client(cfg)
    user = sp.current_user()
    typer.echo(f"✅ Logged in as: {user['display_name']}")

@app.command()
def download_tracks():
    """Download all tracks from the configured playlist and save to JSON."""
    cfg = load_config()
    sp = get_spotify_client(cfg)

    playlist_id = cfg["spotify"]["playlist_id"]
    typer.echo(f"📥 Fetching tracks from playlist: {playlist_id}")
    
    tracks = get_playlist_tracks(sp, playlist_id)
    typer.echo(f"✅ Retrieved {len(tracks)} tracks")

    with open(TRACKS_OUTPUT_PATH, "w") as f:
        json.dump(tracks, f)
    typer.echo(f"📦 Saved to {TRACKS_OUTPUT_PATH}")

if __name__ == "__main__":
    app()
