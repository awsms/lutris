import json
import os
from gettext import gettext as _

from PIL import Image

from lutris import settings
from lutris.services.base import BaseService
from lutris.services.service_game import ServiceGame
from lutris.services.service_media import ServiceMedia
from lutris.util import system
from lutris.util.pcsx2.cache_reader import PCSX2_GAME_CACHE_FILE, PCSX2CacheReader
from lutris.util.strings import slugify

PCSX2_COVERS_CACHE_DIR = "~/.config/PCSX2/covers/"

class PCSX2Cover(ServiceMedia):
    service = "pcsx2"
    size = (256, 368)
    dest_path = os.path.join(settings.CACHE_DIR, "pcsx2/covers")
    file_patterns = ["%s.jpg"]
    file_format = "jpeg"
    api_field = "appid"
    url_pattern = "https://raw.githubusercontent.com/xlenore/ps2-covers/main/covers/%s.jpg"

class PCSX2Banner(ServiceMedia):
    service = "pcsx2"
    source = "local"
    size = (184, 69)
    file_patterns = ["%s.jpg"]
    file_format = "jpeg"
    dest_path = os.path.join(settings.CACHE_DIR, "banners")

class PCSX2Service(BaseService):
    id = "pcsx2"
    name = _("PCSX2")
    icon = "pcsx2"
    local = True
    medias = {
        "icon": PCSX2Banner,
        "cover": PCSX2Cover
    }
    default_format = "cover"

    def load(self):
        if not system.path_exists(PCSX2_GAME_CACHE_FILE):
            return
        cache_reader = PCSX2CacheReader()
        pcsx2_games = [PCSX2Game.new_from_cache(game) for game in cache_reader.get_games()]
        for game in pcsx2_games:
            game.save()
        return pcsx2_games

    def generate_installer(self, db_game):
        details = json.loads(db_game["details"])
        return {
            "name": db_game["name"],
            "version": "PCSX2",
            "slug": db_game["slug"],
            "game_slug": slugify(db_game["name"]),
            "runner": "pcsx2",
            "script": {
                "game": {
                    "main_file": details["path"],
                    "platform": "Sony PlayStation 2"
                },
            }
        }

    def get_game_directory(self, installer):
        """Pull install location from installer"""
        return os.path.dirname(installer["script"]["game"]["main_file"])

    def get_game_platforms(self, db_game):
        return ["Sony PlayStation 2"]

class PCSX2Game(ServiceGame):
    """Game for the PCSX2 emulator"""

    service = "pcsx2"
    runner = "pcsx2"
    installer_slug = "pcsx2"

    @classmethod
    def new_from_cache(cls, cache_entry):
        """Create a service game from an entry from the PCSX2 cache"""
        name = cache_entry["title"] or os.path.splitext(cache_entry["path"])[0]
        service_game = cls()
        if str(cache_entry["serial"]) == '':
            return
        service_game.name = name
        service_game.appid = str(cache_entry["serial"])
        service_game.game_id = str(cache_entry["serial"])
        service_game.slug = slugify(name)
        service_game.cover = service_game.get_cover(cache_entry)
        service_game.details = json.dumps({
            "path": cache_entry["path"],
            "appid": service_game.appid 
        })
        return service_game

    @staticmethod
    def get_game_name(cache_entry):
        names = cache_entry["long_names"]
        name_index = 1 if len(names.keys()) > 1 else 0
        return str(names[list(names.keys())[name_index]])

    def get_banner(self, cache_entry):
        return os.path.join(settings.CACHE_DIR, "banners", f"{self.appid}.jpg")

    def get_cover(self, cache_entry):
        return os.path.join(settings.CACHE_DIR, "pcsx2/covers", f"{self.appid}.jpg")
