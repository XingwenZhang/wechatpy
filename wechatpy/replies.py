from __future__ import absolute_import, unicode_literals
import time
import copy
import six

from .fields import BaseField, StringField, IntegerField, ImageField
from .fields import VoiceField, VideoField, MusicField, ArticleField
from .utils import ObjectDict


REPLY_TYPES = {}


def register_reply(type):
    def register(cls):
        REPLY_TYPES[type] = cls
        return cls
    return register


class ReplyMetaClass(type):
    """Metaclass for all repies"""
    def __new__(cls, name, bases, attrs):
        super_new = super(ReplyMetaClass, cls).__new__
        # Ensure initialization is only performed for subclasses of
        # BaseReply excluding BaseReply class itself
        parents = [b for b in bases if isinstance(b, ReplyMetaClass)]
        if not parents:
            return super_new(cls, name, bases, attrs)
        # Create the class
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        setattr(new_class, '_fields', ObjectDict())

        # Add all attributes to the class
        for obj_name, obj in attrs.items():
            if isinstance(obj, BaseField):
                new_class._fields[obj_name] = obj
            else:
                setattr(new_class, obj_name, obj)
        # Add the fields inherited from parent classes
        for parent in parents:
            for obj_name, obj in parent.__dict__.items():
                if isinstance(obj, BaseField):
                    new_class._fields[obj_name] = copy.deepcopy(obj)
        return new_class


class BaseReply(six.with_metaclass(ReplyMetaClass)):
    source = StringField('FromUserName')
    target = StringField('ToUserName')
    time = IntegerField('CreateTime', int(time.time()))
    type = 'unknown'

    def __init__(self, reply=None):
        reply = reply or {}
        for name, field in self._fields.items():
            value = reply.get(field.name, field.default)
            setattr(self, name, value)

    def render(self):
        tpl = '<xml>\n{data}\n</xml>'
        nodes = []
        for name, field in self._fields.items():
            value = getattr(self, name, field.default)
            node_xml = field.to_xml(value)
            nodes.append(node_xml)
        data = '\n'.join(nodes)
        return tpl.format(data=data)


@register_reply('text')
class TextReply(BaseReply):
    type = 'text'
    content = StringField('Content')


@register_reply('image')
class ImageReply(BaseReply):
    type = 'image'
    image = ImageField('Image')


@register_reply('voice')
class VoiceReply(BaseReply):
    type = 'voice'
    voice = VoiceField('Voice')


@register_reply('video')
class VideoReply(BaseReply):
    type = 'video'
    video = VideoField('Video')


@register_reply('music')
class MusicReply(BaseReply):
    type = 'music'
    music = MusicField('Music')


@register_reply('news')
class ArticleReply(BaseReply):
    type = 'news'
    articles = ArticleField('Articles')


def create_reply(reply, message=None):
    if isinstance(reply, BaseReply):
        return reply.render()
    elif isinstance(reply, six.string_types):
        _reply = TextReply()
        _reply.content = reply
        return _reply.render()
    elif isinstance(reply, (tuple, list)):
        if len(reply) > 10:
            raise AttributeError("Can't add more than 10 articles"
                                 " in an ArticlesReply")
        _reply = ArticleReply()
        _reply.article = reply
        return _reply.render()
    return None