import ujson
from werkzeug.exceptions import NotFound, BadRequest

from flask import Blueprint, render_template, current_app
from flask_login import current_user
from listenbrainz.domain import spotify
from listenbrainz.webserver.views.api_tools import is_valid_uuid
from listenbrainz.webserver.views.playlist_api import serialize_jspf, fetch_playlist_recording_metadata
import listenbrainz.db.playlist as db_playlist

playlist_bp = Blueprint("playlist", __name__)


@playlist_bp.route("/<playlist_mbid>", methods=["GET"])
def load_playlist(playlist_mbid: str):
    """Load a single playlist by id
    """
    if not is_valid_uuid(playlist_mbid):
        raise BadRequest("Provided playlist ID is invalid: %s" % playlist_mbid)

    playlist = db_playlist.get_by_mbid(playlist_mbid, True)
    # TODO: Allow playlist collaborators to access private playlist
    if playlist is None or not playlist.public and (not current_user.is_authenticated or playlist.creator_id != current_user.id):
        raise NotFound("Cannot find playlist: %s" % playlist_mbid)

    fetch_playlist_recording_metadata(playlist)

    spotify_data = {}
    current_user_data = {}
    if current_user.is_authenticated:
        spotify_data = spotify.get_user_dict(current_user.id)

        current_user_data = {
                "id": current_user.id,
                "name": current_user.musicbrainz_id,
                "auth_token": current_user.auth_token,
        }
    props = {
        "current_user": current_user_data,
        "spotify": spotify_data,
        "api_url": current_app.config["API_URL"],
        "playlist": serialize_jspf(playlist)
    }

    return render_template(
        "playlists/playlist.html",
        props=ujson.dumps(props)
    )
