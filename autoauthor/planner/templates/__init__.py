"""autoauthor/planner/templates/ — 플랫폼별 콘텐츠 기획 템플릿"""
from .tistory_blog import TistoryBlogTemplate
from .youtube_script import YoutubeScriptTemplate
from .instagram_card import InstagramCardTemplate
from .facebook_post import FacebookPostTemplate
from .shortform import ShortformTemplate
from .thread_x import ThreadXTemplate
from .naver_blog import NaverBlogTemplate

from .synergy import SynergyTemplate

PLATFORM_TEMPLATES = {
    "tistory": TistoryBlogTemplate,
    "naver": NaverBlogTemplate,
    "youtube": YoutubeScriptTemplate,
    "instagram": InstagramCardTemplate,
    "facebook": FacebookPostTemplate,
    "shortform": ShortformTemplate,
    "thread": ThreadXTemplate,
    "synergy": SynergyTemplate,
}
