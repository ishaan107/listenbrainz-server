"""This module contains functions to insert and retrieve statistics
   calculated from Google BigQuery into the database.
"""

import sqlalchemy
import ujson
from listenbrainz import db


# XXX(param): think about the names of these stats variables
# should they be artist_stats and so on instead?
# Note: names are used in tests and stats/calculate.py also

def insert_user_stats(user_id, artists, recordings, releases, artist_count):
    # XXX(param): should this name be upsert_user_stats?

    # put all artist stats into one dict which will then be inserted
    # into the artist column of the stats.user table
    # XXX(param): This makes the schema of the stats very variable though.
    artist_stats = {
        'count': artist_count,
        'all_time': artists
    }

    with db.engine.connect() as connection:
        connection.execute(sqlalchemy.text("""
            INSERT INTO statistics.user (user_id, artists, recordings, releases)
                 VALUES (:user_id, :artists, :recordings, :releases)
            ON CONFLICT (user_id)
          DO UPDATE SET artists = :artists,
                        recordings = :recordings,
                        releases = :releases,
                        last_updated = NOW()
            """), {
                'user_id': user_id,
                'artists': ujson.dumps(artist_stats),
                'recordings': ujson.dumps(recordings),
                'releases': ujson.dumps(releases)
            }
        )


def get_user_stats(user_id):

    with db.engine.connect() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT user_id, artists, releases, recordings
              FROM statistics.user
             WHERE user_id = :user_id
            """), {
                'user_id': user_id
            }
        )
        row = result.fetchone()
        return dict(row) if row else None
