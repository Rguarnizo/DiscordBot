

from typing import Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class AchievementsInfo:
    show_achievements: Optional[bool]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'AchievementsInfo':
        _show_achievements = obj.get(_show_achievements)
        return AchievementsInfo(_show_achievements)

@dataclass
class MusicAssetInfo:
    display_artist: Optional[str] 
    title: Optional[str] 
    audio_cluster_id: Optional[str] 
    is_explicit: Optional[bool]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'MusicAssetInfo':
        _display_artist = str(obj.get("display_artist"))
        _title = str(obj.get("title"))
        _audio_cluster_id = str(obj.get("audio_cluster_id"))
        _is_explicit = obj.get("is_explicit")
        return MusicAssetInfo(_display_artist, _title, _audio_cluster_id, _is_explicit)

@dataclass
class MusicConsumptionInfo:
    should_mute_audio: Optional[bool]
    should_mute_audio_reason: Optional[str]
    is_trending_in_clips: Optional[bool] 

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'MusicConsumptionInfo':
        _should_mute_audio = obj.get("should_mute_audio")
        _should_mute_audio_reason = str(obj.get("should_mute_audio_reason"))
        _is_trending_in_clips = obj.get("is_trending_in_clips")
        return MusicConsumptionInfo(_should_mute_audio, _should_mute_audio_reason, _is_trending_in_clips)

@dataclass
class MusicInfo:
    music_consumption_info: Optional[MusicConsumptionInfo]
    music_asset_info: Optional[MusicAssetInfo]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'MusicInfo':
        _music_consumption_info = MusicConsumptionInfo.from_dict(obj.get("music_consumption_info"))
        _music_asset_info = MusicAssetInfo.from_dict(obj.get("music_asset_info"))
        return MusicInfo(_music_consumption_info, _music_asset_info)

@dataclass
class ClipsMetadata:
    audio_type: Optional[str]
    achievements_info: Optional[AchievementsInfo]
    music_info: Optional[MusicInfo]
    is_shared_to_fb: Optional[bool]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'ClipsMetadata':
        _audio_type = str(obj.get("audio_type"))
        _achievements_info = AchievementsInfo.from_dict(obj.get("achievements_info"))
        _music_info = MusicInfo.from_dict(obj.get("music_info"))
        _is_shared_to_fb = False
        return ClipsMetadata(_audio_type, _achievements_info, _music_info, _is_shared_to_fb)

# Example Usage
# jsonstring = json.loads(myjsonstring)
# root = Root.from_dict(jsonstring)
@dataclass
class User:
    pk: Optional[str]
    is_verified: Optional[bool]
    username: Optional[str]
    id: Optional[str]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'User':
        _pk = str(obj.get("pk"))
        _is_verified = obj.get("is_verified")
        _username = str(obj.get("username"))
        _id = str(obj.get("id"))
        return User(_pk, _is_verified, _username, _id)

@dataclass
class PreviewComment:
    __typename: Optional[str]
    pk: Optional[str]
    text: Optional[str]
    user: Optional[User]
    has_liked_comment: Optional[str]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'PreviewComment':
        ___typename = str(obj.get("__typename"))
        _pk = str(obj.get("pk"))
        _text = str(obj.get("text"))
        _user = User.from_dict(obj.get("user"))
        _has_liked_comment = str(obj.get("has_liked_comment"))
        return PreviewComment(___typename, _pk, _text, _user, _has_liked_comment)

@dataclass
class PreviewComments:
    preview_comments: List[PreviewComment]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'PreviewComments':
        _preview_comments = [PreviewComment.from_dict(y) for y in obj.get("preview_comments")]
        return PreviewComments(_preview_comments)



@dataclass
class Caption:
    text: Optional[str]
    pk: Optional[str]
    has_translation: Optional[str]
    created_at: Optional[int]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'Caption':
        _text = str(obj.get("text"))
        _pk = str(obj.get("pk"))
        _has_translation = str(obj.get("has_translation"))
        _created_at = int(obj.get("created_at"))
        return Caption(_text, _pk, _has_translation, _created_at)
    
@dataclass
class VideoVersion:
    width: Optional[int]
    height: Optional[int]
    url: Optional[str]
    type: Optional[int]

    @staticmethod
    def from_dict(obj: Any) -> "VideoVersion":
        return VideoVersion(
            width=obj.get("width"),
            height=obj.get("height"),
            url=obj.get("url"),
            type=obj.get("type")
        )

    
@dataclass
class Owner:
    pk: Optional[str]
    id: Optional[str]
    username: Optional[str]
    profile_pic_url: Optional[str]
    show_account_transparency_details: Optional[bool]
    __typename: Optional[str]
    is_private: Optional[bool]
    friendship_status: Optional[str]
    transparency_product: Optional[str]
    transparency_product_enabled: Optional[bool]
    transparency_label: Optional[str]
    ai_agent_owner_username: Optional[str]
    is_unpublished: Optional[bool]
    is_verified: Optional[bool]

    @staticmethod
    def from_dict(obj: Optional[Any]) -> 'Owner':
        _pk = str(obj.get("pk"))
        _id = str(obj.get("id"))
        _username = str(obj.get("username"))
        _profile_pic_url = str(obj.get("profile_pic_url"))
        _show_account_transparency_details =  obj.get("show_account_transparency_details")
        ___typename = str(obj.get("__typename"))
        _is_private = obj.get("is_private ")
        _friendship_status = str(obj.get("friendship_status"))
        _transparency_product = str(obj.get("transparency_product"))
        _transparency_product_enabled = obj.get("transparency_product_enabled ")
        _transparency_label = str(obj.get("transparency_label"))
        _ai_agent_owner_username = str(obj.get("ai_agent_owner_username"))
        _is_unpublished = obj.get("is_unpublished ")
        _is_verified = obj.get("is_verified ")
        return Owner(_pk, _id, _username, _profile_pic_url, _show_account_transparency_details, ___typename, _is_private, _friendship_status, _transparency_product, _transparency_product_enabled, _transparency_label, _ai_agent_owner_username, _is_unpublished, _is_verified)

# Example Usage
# jsonstring = json.loads(myjsonstring)
# root = Root.from_dict(jsonstring)