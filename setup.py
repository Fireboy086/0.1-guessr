from setuptools import setup

setup(
    name="spotify-guessr-cli",
    version="0.1.0",
    description="Command-line version of Spotify Guessing Game",
    author="Fire",
    py_modules=["spotify_guessr", "game_logic", "spotify_manager", "config"],
    install_requires=[
        "spotipy>=2.22.1",
        "configparser",
    ],
    entry_points={
        "console_scripts": [
            "spotify-guessr=spotify_guessr:main",
        ],
    },
) 