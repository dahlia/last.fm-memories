from dataclasses import dataclass, field
import datetime
import functools
import math
from typing import Any, Callable, Hashable, Iterable, Sequence, Optional, Tuple

from pylast import _Network, Album, Artist, PlayedTrack, User

__name__ = 'Criteria', 'list_albums', 'list_artists'


@dataclass(frozen=True)
class Criteria:
    user: User
    window: datetime.timedelta
    timestamp: datetime.datetime = field(
        default_factory=functools.partial(
            datetime.datetime.now,
            datetime.timezone.utc,
        ),
    )

    @property
    def network(self) -> _Network:
        return self.user.network

    @property
    def timestamp_from(self) -> datetime.datetime:
        return self.timestamp - (self.window / 2)

    @property
    def timestamp_to(self) -> datetime.datetime:
        return self.timestamp + (self.window / 2)

    def get_played_tracks(self) -> Iterable[PlayedTrack]:
        limit = 200
        time_to = int(math.ceil(self.timestamp_to.timestamp()))
        while True:
            tracks = self.user.get_recent_tracks(
                limit=limit,
                time_from=int(self.timestamp_from.timestamp()),
                time_to=time_to,
            )
            yield from tracks
            if len(tracks) < limit:
                break
            time_to = int(tracks[-1].timestamp)


def group_tracks(
    criteria: Criteria,
    populater: Callable[[PlayedTrack], Any],
    grouper: Optional[Callable[[PlayedTrack], Hashable]] = None,
) -> Sequence[Tuple[Any, int]]:
    groups = {}
    if grouper is None:
        grouper = populater
    tracks = criteria.get_played_tracks()
    prev_key = None
    for track in tracks:
        key = grouper(track)
        try:
            pair = groups[key]
        except KeyError:
            title = populater(track)
            groups[key] = (title, 1)
        else:
            groups[key] = pair[0], pair[1] + int(key != prev_key)
        prev_key = key
    pairs = list(groups.values())
    pairs.sort(key=lambda pair: pair[1])
    return pairs


def list_albums(criteria: Criteria) -> Sequence[Tuple[Album, int]]:
    return group_tracks(
        criteria,
        lambda t: criteria.network.get_album(t.track.artist, t.album),
        lambda t: (t.track.artist, t.album)
    )


def list_artists(criteria: Criteria) -> Sequence[Tuple[Artist, int]]:
    return group_tracks(criteria, lambda t: t.track.artist)
