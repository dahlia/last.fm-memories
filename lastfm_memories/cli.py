import datetime
import json
import os
import os.path
import pathlib
import re
import shutil
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple
import unicodedata

from appdirs import user_cache_dir, user_config_dir
from click import INT, Choice, Path, argument, command, confirm, option, prompt
from monthdelta import monthdelta
from pylast import LastFMNetwork, LibreFMNetwork

from .query import Criteria, list_artists, list_albums

__all__ = 'main',


APP_NAME = 'last.fm-memories'
OPERATIONS: Mapping[str, Callable[[Criteria], Sequence[Tuple[Any, int]]]] = {
    'artists': list_artists,
    'albums': list_albums,
}


def get_api_key(
    config: pathlib.Path,
    api_key: Optional[str],
    api_secret: Optional[str],
) -> Tuple[str, str]:
    try:
        data = json.loads(config.read_text(encoding='utf-8'))
        cfg_api_key = data['api_key']
        cfg_api_secret = data['api_secret']
    except (IOError, KeyError):
        cfg_api_key = None
        cfg_api_secret = None
    if api_key and api_secret:
        if cfg_api_key != api_key or cfg_api_secret != api_secret:
            if confirm('Save API keys?'):
                config.parent.mkdir(parents=True, exist_ok=True)
                config.write_text(
                    json.dumps({
                        'api_key': api_key,
                        'api_secret': api_secret,
                    }),
                    encoding='utf-8',
                )
        return api_key, api_secret
    if cfg_api_key and cfg_api_secret:
        return cfg_api_key, cfg_api_secret
    api_key = prompt(
        'A Last.fm/Libre.fm API key is required.  '
        'You can get one from <https://www.last.fm/api/account/create>.\n'
        'API key'
    )
    api_secret = prompt('API secret key')
    return get_api_key(config=config, api_key=api_key, api_secret=api_secret)


_pad_right_re = re.compile(r'([-A-Za-z0-9_.,;!?/@#%&*()\[\]{}|~`"\'<>-]+)|(.)')


def pad_right(text: str, width: int) -> str:
    text_width = 0
    for match in _pad_right_re.finditer(text):
        if match.group(1):
            text_width += len(match.group(1))
        else:
            east_asian_width = unicodedata.east_asian_width(match.group(2))
            text_width += 1 + int(east_asian_width == 'W')
    return text + ' ' * (width - text_width)


@command(context_settings={'help_option_names': ['-h', '--help']})
@option(
    '-k', '--api-key',
    help=(
        'Last.fm/Libre.fm API key.  '
        'You can get one from <https://www.last.fm/api/account/create>.'
    ),
)
@option(
    '-s', '--api-secret',
    help='Last.fm/Libre.fm API secret key.',
)
@option(
    '-L', '--libre.fm', 'librefm',
    is_flag=True,
    default=False,
    help='Connect to Libre.fm network instead of Last.fm network.',
)
@option(
    '--config',
    type=Path(file_okay=True, dir_okay=False, writable=True),
    default=os.path.join(user_config_dir(APP_NAME), 'config.json'),
    show_default=True,
    help='The path to configuration file.',
)
@option(
    '--cache-dir',
    type=Path(file_okay=False, dir_okay=True, writable=True),
    metavar='DIR',
    default=user_cache_dir(APP_NAME),
    show_default=True,
    help='The directory path to store cache files.',
)
@option(
    '-b', '--back', 'months_back',
    metavar='MONTHS',
    type=INT,
    default=12,
    help=(
        'The period (in months) to rewind.  For example, '
        'to list music listened last year give it 12.  [default: 12 months]'
    ),
)
@option(
    '-w', '--window',
    metavar='DAYS',
    type=INT,
    default=30,
    help='The duration (in days) to query.  [default: 30 days]',
)
@option(
    '-d/-a', '--desc/--asc',
    default=False,
    help='Order the list ascendingly/descendingly.  [default: ascending]'
)
@argument('username')
@argument(
    'unit',
    type=Choice(OPERATIONS.keys(), case_sensitive=False),
    default='artist',
)
def main(
    api_key: str,
    api_secret: str,
    librefm: bool,
    config: str,
    cache_dir: str,
    months_back: int,
    window: int,
    desc: bool,
    username: str,
    unit: str,
):
    """Lists music you had listened before from Last.fm (or Libre.fm)."""
    cls = LibreFMNetwork if librefm else LastFMNetwork
    api_key, api_secret = get_api_key(pathlib.Path(config), api_key, api_secret)
    net = cls(api_key=api_key, api_secret=api_secret)
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    net.enable_caching(os.path.join(cache_dir, 'pylast'))
    user = net.get_user(username)
    criteria = Criteria(
        user=user,
        timestamp=datetime.datetime.now(
            datetime.timezone.utc
        ) - monthdelta(months_back),
        window=datetime.timedelta(days=window),
    )
    operation = OPERATIONS[unit]
    pairs = operation(criteria)
    if desc:
        pairs = list(pairs)[::-1]
    width, _ = shutil.get_terminal_size()
    freq_width = len(str(pairs[0][1] if pairs else 0))
    title_width = width - freq_width - 1
    for item, freq in pairs:
        print(f'{pad_right(str(item), title_width)} {freq:-{freq_width}}')
