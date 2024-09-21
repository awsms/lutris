import os
import struct
from lutris.util.log import logger

PCSX2_GAME_CACHE_FILE = os.path.expanduser("~/.config/PCSX2/cache/gamelist.cache")
SUPPORTED_CACHE_VERSION = 34
GAME_LIST_CACHE_SIGNATURE = 0x45434C47
PCSX2_COVERS_CACHE_DIR = "~/.config/PCSX2/covers/"

def get_word_len(data):
    """Return the length of a string as specified in the PCSX2 format."""
    if len(data) < 4:
        raise ValueError("Buffer too small to unpack 4-byte length")
    return struct.unpack("<I", data)[0]

def read_string(data, offset):
    """Read a length-prefixed string from data starting at the given offset."""
    if offset + 4 > len(data):
        raise ValueError(f"Buffer too small to read string length at offset {offset}")
    length = get_word_len(data[offset:offset + 4])
    offset += 4
    if offset + length > len(data):
        raise ValueError(f"Buffer too small to read string data at offset {offset}, expected length {length}")
    string = data[offset:offset + length]
    offset += length
    return string.decode('utf8', errors='ignore'), offset

def read_u8(data, offset):
    """Read a single byte from data starting at the given offset."""
    if offset + 1 > len(data):
        raise ValueError(f"Buffer too small to read u8 at offset {offset}")
    value = data[offset]
    offset += 1
    return value, offset

def read_u32(data, offset):
    """Read a 4-byte unsigned integer from data starting at the given offset."""
    if offset + 4 > len(data):
        raise ValueError(f"Buffer too small to read u32 at offset {offset}")
    value = struct.unpack("<I", data[offset:offset + 4])[0]
    offset += 4
    return value, offset

def read_u64(data, offset):
    """Read an 8-byte unsigned integer from data starting at the given offset."""
    if offset + 8 > len(data):
        raise ValueError(f"Buffer too small to read u64 at offset {offset}")
    value = struct.unpack("<Q", data[offset:offset + 8])[0]
    offset += 8
    return value, offset

class PCSX2CacheReader:
    # Game structure definition
    structure = {
        'path': 's',
        'serial': 's',
        'title': 's',
        'title_sort': 's',
        'title_en': 's',
        'type': 1,
        'region': 1,
        'total_size': 8,
        'last_modified_time': 8,
        'crc': 4,
        'compatibility_rating': 1,
    }

    def __init__(self):
        self.offset = 0
        with open(PCSX2_GAME_CACHE_FILE, "rb") as pcsx2_cache_file:
            self.cache_content = pcsx2_cache_file.read()
        if len(self.cache_content) < 8:
            raise ValueError("Cache content too small to contain header")
        self.read_header()

    def read_header(self):
        try:
            cache_signature, self.offset = read_u32(self.cache_content, self.offset)
            cache_version, self.offset = read_u32(self.cache_content, self.offset)
            if cache_signature != GAME_LIST_CACHE_SIGNATURE:
                logger.warning("PCSX2 cache signature expected %s but found %s", GAME_LIST_CACHE_SIGNATURE, cache_signature)
            if cache_version != SUPPORTED_CACHE_VERSION:
                logger.warning("PCSX2 cache version expected %s but found %s", SUPPORTED_CACHE_VERSION, cache_version)
        except Exception as ex:
            raise ValueError(f"Error reading header: {ex}")

    def get_game(self):
        game = {}
        for key, field_type in self.structure.items():
            if field_type == 's':
                game[key] = self.get_string()
            elif field_type == 1:
                game[key] = self.get_u8()
            elif field_type == 4:
                game[key] = self.get_u32()
            elif field_type == 8:
                game[key] = self.get_u64()
        return game

    def get_games(self):
        games = []
        while self.offset < len(self.cache_content):
            try:
                games.append(self.get_game())
            except Exception as ex:
                logger.error(f"Error reading game at offset {self.offset}: {ex}")
                break
        return games

    def get_string(self):
        string, self.offset = read_string(self.cache_content, self.offset)
        return string

    def get_u8(self):
        value, self.offset = read_u8(self.cache_content, self.offset)
        return value

    def get_u32(self):
        value, self.offset = read_u32(self.cache_content, self.offset)
        return value

    def get_u64(self):
        value, self.offset = read_u64(self.cache_content, self.offset)
        return value