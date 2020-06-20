from django.db import models

from .mixins import PublishedMixin, TimeDateMixin
from .UserModel import User
from .TutorialRelatedModel import Tutorial

from .translation_collection import add_trans_table


class TranslationBase(PublishedMixin, TimeDateMixin, models.Model):
    # meta
    authors = models.ManyToManyField(User)
    tutorial_anchor = models.OneToOneField(Tutorial, on_delete=models.CASCADE)
    abstract = models.TextField()
    # content
    content_md = models.TextField()
    content_html = models.TextField()

    class Meta:
        abstract = True


@add_trans_table
class ENUS(TranslationBase):
    pass


@add_trans_table
class ZHCN(TranslationBase):
    pass
