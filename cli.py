import typer
import yaml
import json
import pandas as pd
from pathlib import Path
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

app = typer.Typer()

CONFIG_PATH = Path("config.override.yaml")

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_spotify_client(cfg):
    return Spotify(auth_manager=SpotifyOAuth(
        client_id=cfg['spotify']['client_id'],
        client_secret=cfg['spotify']['client_secret'],
        redirect_uri=cfg['spotify']['redirect_uri'],
        scope="playlist-read-private"
    ),
        requests_timeout=30
    )

def get_playlist_tracks(sp: Spotify, playlist_id: str):
    tracks = []
    results = sp.playlist_items(playlist_id, limit=100)
    tracks.extend(results['items'])

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    return tracks

def get_audio_features(sp, track_ids):
    track_ids = [tid for tid in track_ids if tid is not None]
    if not track_ids:
        print("❌ No valid track IDs.")
        return []

    features = []
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        try:
            response = sp.audio_features(batch)
            features.extend(response)
            print(f"✅ Batch {i//100 + 1}: {len(response)} features")
        except Exception as e:
            print(f"❌ Batch {i//100 + 1} failed: {e}")
    return features

@app.command()
def extract_features(output: Path = Path("features.csv")):
    """
    Extract audio features from a Spotify playlist and save them to a CSV.
    """
    cfg = load_config()
    sp = get_spotify_client(cfg)
    auth =SpotifyOAuth(
        client_id=cfg['spotify']['client_id'],
        client_secret=cfg['spotify']['client_secret'],
        redirect_uri=cfg['spotify']['redirect_uri'],
        scope="playlist-read-private"
    )

    print("🔗 Redirect URI:", auth.get_authorize_url())
    playlist_id = cfg['spotify']['playlist_id']
    typer.echo(f"🎵 Fetching tracks from playlist: {playlist_id}")
    tracks = get_playlist_tracks(sp, playlist_id)

    track_ids = [
        item['track']['uri']
        for item in tracks
        if item.get('track') and item['track'].get('uri')
    ]

    # 💡 Filter out any lingering None values
    track_ids = [tid for tid in track_ids if tid is not None]
    typer.echo(f"✅ Retrieved {len(track_ids)} track IDs")

    features = get_audio_features(sp, track_ids)
    df = pd.DataFrame(features)
    df.to_csv(output, index=False)

    typer.echo(f"📁 Saved audio features to {output}")

if __name__ == "__main__":
    app()
