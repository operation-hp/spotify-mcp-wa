from collections import defaultdict
from typing import Optional, Dict
import functools
from typing import Callable, TypeVar
from typing import Optional, Dict
from urllib.parse import quote

from requests import RequestException

T = TypeVar('T')


def parse_track(track_item: dict, detailed=False) -> Optional[dict]:
    if not track_item:
        return None
    narrowed_item = {
        'name': track_item['name'],
        'id': track_item['id'],
    }

    if 'is_playing' in track_item:
        narrowed_item['is_playing'] = track_item['is_playing']

    if detailed:
        narrowed_item['album'] = parse_album(track_item.get('album'))
        for k in ['track_number', 'duration_ms']:
            narrowed_item[k] = track_item.get(k)

    if not track_item.get('is_playable', True):
        narrowed_item['is_playable'] = False

    artists = [a['name'] for a in track_item['artists']]
    if detailed:
        artists = [parse_artist(a) for a in track_item['artists']]

    if len(artists) == 1:
        narrowed_item['artist'] = artists[0]
    else:
        narrowed_item['artists'] = artists

    return narrowed_item


def parse_artist(artist_item: dict, detailed=False) -> Optional[dict]:
    if not artist_item:
        return None
    narrowed_item = {
        'name': artist_item['name'],
        'id': artist_item['id'],
    }
    if detailed:
        narrowed_item['genres'] = artist_item.get('genres')

    return narrowed_item


def parse_playlist(playlist_item: dict, username, detailed=False) -> Optional[dict]:
    if not playlist_item:
        return None
    narrowed_item = {
        'name': playlist_item['name'],
        'id': playlist_item['id'],
        'owner': playlist_item['owner']['display_name'],
        'user_is_owner': playlist_item['owner']['display_name'] == username
    }
    if detailed:
        narrowed_item['description'] = playlist_item.get('description')
        tracks = []
        for t in playlist_item['tracks']['items']:
            tracks.append(parse_track(t['track']))
        narrowed_item['tracks'] = tracks

    return narrowed_item


def parse_album(album_item: dict, detailed=False) -> dict:
    narrowed_item = {
        'name': album_item['name'],
        'id': album_item['id'],
    }

    artists = [a['name'] for a in album_item['artists']]

    if detailed:
        tracks = []
        for t in album_item['tracks']['items']:
            tracks.append(parse_track(t))
        narrowed_item["tracks"] = tracks
        artists = [parse_artist(a) for a in album_item['artists']]

        for k in ['total_tracks', 'release_date', 'genres']:
            narrowed_item[k] = album_item.get(k)

    if len(artists) == 1:
        narrowed_item['artist'] = artists[0]
    else:
        narrowed_item['artists'] = artists

    return narrowed_item

def parse_show(show_item: dict, detailed=False) -> dict:
    """
    Parse a Spotify show object into a simplified format.
    
    Args:
        show_item: The show data from Spotify API
        detailed: Whether to include additional details
        
    Returns:
        A dictionary with parsed show information
    """
    narrowed_item = {
        'name': show_item['name'],
        'id': show_item['id'],
        'uri': show_item.get('uri', ''),
        'publisher': show_item.get('publisher', ''),
        'type': 'show',
        'total_episodes': show_item.get('total_episodes', 0),
    }
    
    # Add image if available
    if 'images' in show_item and show_item['images']:
        narrowed_item['image'] = show_item['images'][0].get('url', '')
    
    # Add description (shortened if not detailed)
    if 'description' in show_item:
        if detailed:
            narrowed_item['description'] = show_item['description']
        else:
            # Truncate description for non-detailed view
            desc = show_item['description']
            narrowed_item['description'] = (desc[:100] + '...') if len(desc) > 100 else desc
    
    # Add additional details for detailed view
    if detailed:
        if 'explicit' in show_item:
            narrowed_item['explicit'] = show_item['explicit']
        
        if 'languages' in show_item:
            narrowed_item['languages'] = show_item['languages']
            
        if 'media_type' in show_item:
            narrowed_item['media_type'] = show_item['media_type']
            
        if 'html_description' in show_item:
            narrowed_item['html_description'] = show_item['html_description']
    
    # Parse episodes if available
    if "episodes" in show_item and "items" in show_item["episodes"]:
        episodes = []
        for episode in show_item["episodes"]["items"]:
            episode_data = {
                'name': episode.get('name', ''),
                'id': episode.get('id', ''),
                'uri': episode.get('uri', ''),
                'release_date': episode.get('release_date', ''),
                'duration_ms': episode.get('duration_ms', 0),
            }
            
            if detailed and 'description' in episode:
                episode_data['description'] = episode['description']
                
            episodes.append(episode_data)
        
        narrowed_item["episodes"] = episodes
    
    return narrowed_item




def parse_search_results(results: Dict, qtype: str, username: Optional[str] = None):
    _results = defaultdict(list)
    # potential
    # if username:
    #     _results['User Spotify URI'] = username

    for q in qtype.split(","):
        match q:
            case "track":
                for idx, item in enumerate(results['tracks']['items']):
                    if not item: continue
                    _results['tracks'].append(parse_track(item))
            case "artist":
                for idx, item in enumerate(results['artists']['items']):
                    if not item: continue
                    _results['artists'].append(parse_artist(item))
            case "playlist":
                for idx, item in enumerate(results['playlists']['items']):
                    if not item: continue
                    _results['playlists'].append(parse_playlist(item, username))
            case "album":
                for idx, item in enumerate(results['albums']['items']):
                    if not item: continue
                    _results['albums'].append(parse_album(item))
            case "show":
                for idx, item in enumerate(results['shows']['items']):
                    if not item: continue
                    _results['shows'].append(parse_show(item)) 
            case "episode":
                for idx, item in enumerate(results['episodes']['items']):
                    if not item: continue
                    _results['episodes'].append(parse_episode(item))
            case "audiobook":
                for idx, item in enumerate(results['audiobooks']['items']):
                    if not item: continue
                    _results['audiobooks'].append(parse_audiobook(item))
            case _:
                raise ValueError(f"Unknown qtype {qtype}")

    return dict(_results)


def build_search_query(base_query: str,
                       artist: Optional[str] = None,
                       track: Optional[str] = None,
                       album: Optional[str] = None,
                       year: Optional[str] = None,
                       year_range: Optional[tuple[int, int]] = None,
                       # upc: Optional[str] = None,
                       # isrc: Optional[str] = None,
                       genre: Optional[str] = None,
                       is_hipster: bool = False,
                       is_new: bool = False
                       ) -> str:
    """
    Build a search query string with optional filters.

    Args:
        base_query: Base search term
        artist: Artist name filter
        track: Track name filter
        album: Album name filter
        year: Specific year filter
        year_range: Tuple of (start_year, end_year) for year range filter
        genre: Genre filter
        is_hipster: Filter for lowest 10% popularity albums
        is_new: Filter for albums released in past two weeks

    Returns:
        Encoded query string with applied filters
    """
    filters = []

    if artist:
        filters.append(f"artist:{artist}")
    if track:
        filters.append(f"track:{track}")
    if album:
        filters.append(f"album:{album}")
    if year:
        filters.append(f"year:{year}")
    if year_range:
        filters.append(f"year:{year_range[0]}-{year_range[1]}")
    if genre:
        filters.append(f"genre:{genre}")
    if is_hipster:
        filters.append("tag:hipster")
    if is_new:
        filters.append("tag:new")

    query_parts = [base_query] + filters
    return quote(" ".join(query_parts))


def validate(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for Spotify API methods that handles authentication and device validation.
    - Checks and refreshes authentication if needed
    - Validates active device and retries with candidate device if needed
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Handle authentication
        if not self.auth_ok():
            self.auth_refresh()

        # Handle device validation
        if not self.is_active_device():
            kwargs['device'] = self._get_candidate_device()

        # TODO: try-except RequestException
        return func(self, *args, **kwargs)

    return wrapper


def parse_episode(episode_item: dict, detailed=False) -> dict:
    """
    Parse a Spotify episode object into a simplified format.
    
    Args:
        episode_item: The episode data from Spotify API
        detailed: Whether to include additional details
        
    Returns:
        A dictionary with parsed episode information
    """
    narrowed_item = {
        'name': episode_item['name'],
        'id': episode_item['id'],
        'uri': episode_item.get('uri', ''),
        'type': 'episode',
    }
    
    # Add show information if available
    if 'show' in episode_item:
        narrowed_item['show_name'] = episode_item['show'].get('name', '')
        narrowed_item['publisher'] = episode_item['show'].get('publisher', '')
    
    # Add duration in a readable format
    if 'duration_ms' in episode_item:
        duration_ms = episode_item['duration_ms']
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        narrowed_item['duration'] = f"{minutes}:{seconds:02d}"
    
    # Add image if available
    if 'images' in episode_item and episode_item['images']:
        narrowed_item['image'] = episode_item['images'][0].get('url', '')
    
    # Add release date
    if 'release_date' in episode_item:
        narrowed_item['release_date'] = episode_item['release_date']
    
    # Add description (shortened if not detailed)
    if 'description' in episode_item:
        if detailed:
            narrowed_item['description'] = episode_item['description']
        else:
            # Truncate description for non-detailed view
            desc = episode_item['description']
            narrowed_item['description'] = (desc[:100] + '...') if len(desc) > 100 else desc
    
    # Add additional details for detailed view
    if detailed:
        if 'explicit' in episode_item:
            narrowed_item['explicit'] = episode_item['explicit']
        
        if 'languages' in episode_item:
            narrowed_item['languages'] = episode_item['languages']
            
        if 'html_description' in episode_item:
            narrowed_item['html_description'] = episode_item['html_description']
            
        if 'audio_preview_url' in episode_item:
            narrowed_item['audio_preview_url'] = episode_item['audio_preview_url']
    
    return narrowed_item

def parse_audiobook(audiobook_item: dict, detailed=False) -> dict:
    """
    Parse a Spotify audiobook object into a simplified format.
    
    Args:
        audiobook_item: The audiobook data from Spotify API
        detailed: Whether to include additional details
        
    Returns:
        A dictionary with parsed audiobook information
    """
    narrowed_item = {
        'name': audiobook_item['name'],
        'id': audiobook_item['id'],
        'uri': audiobook_item.get('uri', ''),
        'type': 'audiobook',
    }
    
    # Add authors if available
    if 'authors' in audiobook_item:
        authors = [author.get('name', '') for author in audiobook_item['authors']]
        narrowed_item['authors'] = authors
    
    # Add narrators if available
    if 'narrators' in audiobook_item:
        narrators = [narrator.get('name', '') for narrator in audiobook_item['narrators']]
        narrowed_item['narrators'] = narrators
    
    # Add publisher
    if 'publisher' in audiobook_item:
        narrowed_item['publisher'] = audiobook_item['publisher']
    
    # Add image if available
    if 'images' in audiobook_item and audiobook_item['images']:
        narrowed_item['image'] = audiobook_item['images'][0].get('url', '')
    
    # Add description (shortened if not detailed)
    if 'description' in audiobook_item:
        if detailed:
            narrowed_item['description'] = audiobook_item['description']
        else:
            # Truncate description for non-detailed view
            desc = audiobook_item['description']
            narrowed_item['description'] = (desc[:100] + '...') if len(desc) > 100 else desc
    
    # Add additional details for detailed view
    if detailed:
        if 'explicit' in audiobook_item:
            narrowed_item['explicit'] = audiobook_item['explicit']
        
        if 'languages' in audiobook_item:
            narrowed_item['languages'] = audiobook_item['languages']
            
        if 'total_chapters' in audiobook_item:
            narrowed_item['total_chapters'] = audiobook_item['total_chapters']
            
        if 'html_description' in audiobook_item:
            narrowed_item['html_description'] = audiobook_item['html_description']
            
        # Add chapters if available
        if 'chapters' in audiobook_item and 'items' in audiobook_item['chapters']:
            chapters = []
            for chapter in audiobook_item['chapters']['items']:
                chapter_data = {
                    'name': chapter.get('name', ''),
                    'id': chapter.get('id', ''),
                    'uri': chapter.get('uri', ''),
                    'chapter_number': chapter.get('chapter_number', 0),
                }
                
                if 'duration_ms' in chapter:
                    duration_ms = chapter['duration_ms']
                    minutes = duration_ms // 60000
                    seconds = (duration_ms % 60000) // 1000
                    chapter_data['duration'] = f"{minutes}:{seconds:02d}"
                
                chapters.append(chapter_data)
            
            narrowed_item['chapters'] = chapters
    
    return narrowed_item
