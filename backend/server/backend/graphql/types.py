from graphql import GraphQLError

from ..model.mixins import time_date_mixin_field, published_mixin_field, uuid_mixin_field
from ..model.translation_collection import add_trans_type, process_trans_name
from ..models import User
from ..models import Category, Tutorial, Graph, Code, ExecResultJson
from ..models import ENUS, ZHCN
from graphene_django.types import DjangoObjectType
import graphene


class UserType(DjangoObjectType):
    role = graphene.Int(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'role',
                  'is_verified', 'date_joined',
                  ) + uuid_mixin_field
        description = 'User type. Login required to get info an account. '


class TutorialInterface(graphene.Interface):
    id = graphene.UUID()
    title = graphene.String()
    authors = graphene.List(graphene.String)
    abstract = graphene.String()
    content_md = graphene.String()
    content_html = graphene.String()
    is_published = graphene.Boolean()
    createdTime = graphene.DateTime()
    modifiedTime = graphene.DateTime()

    def resolve_authors(self, info, **kwargs):
        return self.authors.all().values_list('username', flat=True)


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ('category', 'tutorial_set')
        description = 'Category of a tutorial'


class TutorialType(DjangoObjectType):
    categories = graphene.List(graphene.String)
    content = graphene.Field(TutorialInterface, translation=graphene.String(), default=graphene.String(), required=True)

    def resolve_categories(self, info):
        return self.categories.all().values_list('category', flat=True)

    def resolve_content(self, info, translation: str = 'en-us', default: str = '', **kwargs):
        content = self.get_translation(translation, default)
        if content:
            return content
        raise GraphQLError(f'This tutorial does not provide {translation} translation for now. ')

    def resolve_code(self, info):
        return getattr(self, 'code', Code(id='00000000-0000-0000-0000-000000000000', code='# Empty \n'))

    class Meta:
        model = Tutorial
        fields = ('url', 'content',
                  'categories', 'graph_set',
                  'code',
                  ) + \
                 time_date_mixin_field + \
                 published_mixin_field + \
                 uuid_mixin_field

        description = 'The tutorial anchor for an tutorial article. ' \
                      'The contents are in translation table that ' \
                      'corresponds to certain language you want to ' \
                      'query. This type only contains meta info' \
                      'like id, url, category, associated graphs' \
                      'associated codes etc.'


class GraphType(DjangoObjectType):
    priority = graphene.Int(required=True)

    class Meta:
        model = Graph
        fields = ('url', 'graph_info',
                  'cyjs', 'tutorials',
                  'execresultjson_set',
                  'priority'
                  ) + \
                 time_date_mixin_field + \
                 published_mixin_field + \
                 uuid_mixin_field
        description = 'Graph type that contains info of a graph like ' \
                      'cyjs, style json, and layout json'


class CodeType(DjangoObjectType):
    is_published = graphene.Boolean()

    class Meta:
        model = Code
        fields = ('tutorial', 'code', 'execresultjson_set') + \
                 time_date_mixin_field + \
                 published_mixin_field + \
                 uuid_mixin_field
        description = 'The code content of a tutorial. '


class ExecResultJsonType(DjangoObjectType):
    is_published = graphene.Boolean()

    class Meta:
        model = ExecResultJson
        fields = ('code', 'graph', 'json', ) + \
                 time_date_mixin_field + \
                 published_mixin_field + \
                 uuid_mixin_field
        description = 'The execution result of a piece of code on ' \
                      'a graph. '


TransBaseFields = ('tutorial_anchor', 'authors',
                   'abstract', 'content_md', 'content_html',
                   ) + \
                  time_date_mixin_field + \
                  published_mixin_field + \
                  uuid_mixin_field


@add_trans_type
class ENUSTransType(DjangoObjectType):
    class Meta:
        interfaces = (TutorialInterface,)
        model = ENUS
        fields = TransBaseFields
        description = 'The en-us translations of tutorials'


@add_trans_type
class ZHCNTransType(DjangoObjectType):
    class Meta:
        interfaces = (TutorialInterface,)
        model = ZHCN
        fields = TransBaseFields
        description = 'The zh-cn translations of tutorials'
