import json
import os
import logging
from pathlib import Path
import re
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
import subprocess
from pydub import AudioSegment

from .models.graph_ql_data import ClipsMetadata,Owner,PreviewComment,Caption, User, VideoVersion
from dacite import from_dict
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger(__name__).setLevel(logging.WARNING)

@dataclass
class GraphQLData:
    #? Información de Audio de Video.
    clips_metadata: ClipsMetadata
    {#  {

    #                  "audio_type":"licensed_music",

    #                  "achievements_info":{

    #                     "show_achievements":false

    #                  },

    #                  "music_info":{

    #                     "music_consumption_info":{

    #                        "should_mute_audio":false,

    #                        "should_mute_audio_reason":"s",

    #                        "is_trending_in_clips":false

    #                     },

    #                     "music_asset_info":{

    #                        "display_artist":"Cherrelle",

    #                        "title":"Saturday Love (feat. Alexander ONeal)",

    #                        "audio_cluster_id":"1178469355662545",

    #                        "is_explicit":false

    #                     }

    #                  },

    #                  "original_sound_info":"None",

    #                  "is_shared_to_fb":false

    #     }
    }
    like_count: int 
    #? Info of username {
    owner: Owner
    user: User
    product_type: str
    #? Algunos comentarios-
    preview_comments:  Optional[List[PreviewComment]]
    {
        # [{
        #                 "__typename":"XDTCommentDict",
        #                 "pk":"18064158416343592",
        #                 "text":"Qual a taxa de acerto?",
        #                 "user":{
        #                    "pk":"1420993358",
        #                    "is_verified":false,
        #                    "username":"emannuellcenzi",
        #                    "id":"1420993358"
        #                 },
        #                 "has_liked_comment":"None"
        #              },
        #              {
        #                 "__typename":"XDTCommentDict",
        #                 "pk":"17961770801919600",
        #                 "text":"@just.thalia.lya nao tem como, somente com impressao 3D em resina e molde mesmo",
        #                 "user":{
        #                    "pk":"1420993358",
        #                    "is_verified":false,
        #                    "username":"emannuellcenzi",
        #                    "id":"1420993358"
        #                 },
        #                 "has_liked_comment":"None"
        #              }]
    }
    #? Caption y descrición del video.
    display_uri: Optional[str]
    video_versions: Optional[List[VideoVersion]]
    caption: Optional[Caption] 
    {
        # {
        #              "text":"4Behind the scenes of how I made the Chaos Seigaiha keycaps for @urbanedcsupply \n\n#edc #keycaps #artisankeycaps",
        #              "pk":"18093354203149080",
        #              "has_translation":"None",
        #              "created_at":1775545219
        #           }
}
    
@dataclass
class LinkData:
    video_dimensions: str
    likes_count: int
    view_count: int
    user: str 
    caption: str
    creation_timestamp: str 
    audio_track: str

class LinkProcessor:
    def __init__(self):
        """Initialize audio processor with specified Whisper model size or model path. By default, the medium model is used."""
        logger.info("Link Processor Initialized")
    
    def extract_shortcode_from_url(self,url):
        url = url.split('?')[0]  # Remove query parameters
        pattern = r'(?:p|reel|reels|tv)/([^/?]+)'
        match = re.search(pattern, url)
        
        if not match:
            raise ValueError("Invalid Instagram URL")
        
        return match.group(1)
    
    def shortcode_to_pk(self,code: str) -> int:
        pk = 0
        ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

        for c in code[:11]:
            pk = pk * 64 + ALPHABET.index(c)
        return pk

    def _load_cookies(self) -> Dict[str, str]:
        """Cookies de una sesión de Instagram, leídas del entorno (.env), nunca del código.

        IG_COOKIES: cabecera Cookie completa copiada del navegador ("a=b; c=d; ...").
        Es lo recomendado: solo con `sessionid` Instagram suele devolver HTML en vez de JSON.
        IG_SESSIONID: alternativa mínima, solo el valor de la cookie sessionid.
        """
        cookies = {}
        raw = re.sub(r"^cookie:\s*", "", os.getenv("IG_COOKIES", "").strip(), flags=re.I)
        for part in raw.split(";"):
            name, sep, value = part.strip().partition("=")
            if sep and name:
                cookies[name] = value
        if os.getenv("IG_SESSIONID"):
            cookies["sessionid"] = os.getenv("IG_SESSIONID").strip()
        if "sessionid" not in cookies:
            raise RuntimeError("Faltan cookies de Instagram: define IG_COOKIES (o IG_SESSIONID) en .env")
        return cookies

    def _session(self, shortcode: str) -> requests.Session:
        s = requests.Session()
        s.cookies.update(self._load_cookies())
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "X-IG-App-ID": "936619743392459",
            "X-CSRFToken": s.cookies.get("csrftoken", ""),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/reel/{shortcode}/",
            # Sin estas, /comments/ responde con la página HTML en vez de JSON.
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        })
        return s

    def _get_json(self, s: requests.Session, url: str, **params) -> dict:
        r = s.get(url, params=params or None, timeout=30)
        if r.status_code == 429:
            raise RuntimeError("Instagram limitó las peticiones (429). Intenta más tarde.")
        if r.status_code == 404:
            raise RuntimeError("Reel no encontrado o privado (404).")
        try:
            data = r.json()
        except ValueError:
            raise RuntimeError(f"Instagram no devolvió JSON en {url} (HTTP {r.status_code}): "
                               "las cookies caducaron o falta alguna; vuelve a copiar IG_COOKIES.")
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code} en {url}: {str(data)[:200]}")
        return data

    def _fetch_comments(self, s: requests.Session, pk: int) -> List[Dict[str, Any]]:
        """Primera página de comentarios, con el formato de preview_comments de GraphQL."""
        d = self._get_json(s, f"https://www.instagram.com/api/v1/media/{pk}/comments/",
                           can_support_threading="true", permalink_enabled="false")
        out = []
        for c in d.get("comments") or []:
            u = c.get("user") or {}
            out.append({
                "pk": str(c.get("pk")),
                "text": c.get("text") or "",
                "user": {"pk": str(u.get("pk")), "id": str(u.get("id") or u.get("pk")),
                         "username": u.get("username"), "is_verified": u.get("is_verified")},
            })
        return out

    def scrape_instagram_reel(self, url) -> Tuple[GraphQLData, str]:
        """Datos del reel vía /api/v1/media/{pk}/info/.

        La consulta GraphQL (xdt_api__v1__media__shortcode__web_info) es un envoltorio de este
        mismo endpoint REST: items[0] tiene el mismo esquema, así que GraphQLData sirve igual.
        Lanza RuntimeError si algo falla.
        """
        shortcode = self.extract_shortcode_from_url(url)
        pk = self.shortcode_to_pk(shortcode)
        s = self._session(shortcode)

        data = self._get_json(s, f"https://www.instagram.com/api/v1/media/{pk}/info/")
        items = data.get("items") or []
        if not items:
            raise RuntimeError(f"Instagram no devolvió el reel {shortcode}: {str(data)[:200]}")
        item = items[0]

        # Diferencias con la respuesta GraphQL:
        if not item.get("display_uri"):  # REST no trae display_uri: usar la mejor miniatura
            candidates = (item.get("image_versions2") or {}).get("candidates") or []
            item["display_uri"] = candidates[0]["url"] if candidates else None
        if not item.get("preview_comments"):  # REST trae preview_comments vacío
            try:
                item["preview_comments"] = self._fetch_comments(s, pk)
            except (RuntimeError, requests.RequestException) as e:
                logger.warning(f"No se pudieron obtener comentarios: {e}")

        os.makedirs("InstagramData", exist_ok=True)
        with open(f"InstagramData/{shortcode}_data.json", "w") as f:
            json.dump(data, f, indent=4)

        return (from_dict(GraphQLData, self.remove_none(item)), shortcode)
    
    
    def remove_none(self,data):
        if isinstance(data, dict):
            return {k: self.remove_none(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self.remove_none(v) for v in data]
        return data
