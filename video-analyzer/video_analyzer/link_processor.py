import json
import logging
from pathlib import Path
import re
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
import subprocess
from pydub import AudioSegment
from urllib.parse import quote
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
    caption: Caption 
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

    def create_payload(self, shortcode):
        variables = json.dumps({"shortcode": shortcode})
        encoded_variables = quote(variables)
        return f'variables={encoded_variables}&doc_id=24368985919464652'

    def scrape_instagram_reel(self,url) -> Tuple[GraphQLData,str]:
        try:
            shortcode = self.extract_shortcode_from_url(url)
            payload = self.create_payload(shortcode)
            headers = {
                    'content-type': 'application/x-www-form-urlencoded',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'x-csrftoken': 'BxGEN9GJKdXpi0ldJEbd160kLPcHzCix',
                    'x-ig-app-id': '936619743392459',
                }
    
            
            response = requests.post(
                "https://www.instagram.com/graphql/query",
                headers=headers,
                data=payload,
                timeout=10
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                return {"error": "Rate limited. Try again later."}
            
            # Handle not found
            if response.status_code == 404:
                return {"error": "Reel not found or private."}
            
            # Success
            if response.status_code == 200:
                data = response.json()
                
                # Save to file
                with open(f'InstagramData/{shortcode}_data.json', 'w') as f:
                    json.dump(data, f, indent=4)
                data = self.remove_none(data)
                graphql_data = from_dict(GraphQLData,data["data"]["xdt_api__v1__media__shortcode__web_info"]["items"][0])
                
                return (graphql_data,shortcode)
        
        except requests.Timeout:
            return ({"error": "Request timeout"},None)
        except Exception as e:
            return ({"error": str(e)},None)
    
    
    def remove_none(self,data):
        if isinstance(data, dict):
            return {k: self.remove_none(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self.remove_none(v) for v in data]
        return data
