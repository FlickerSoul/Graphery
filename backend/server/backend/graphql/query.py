import graphene
from graphql_jwt.decorators import login_required
from graphql.execution.base import ResolveInfo

from ..model.translation_collection import get_translation_table
# from ..models import User
from ..models import Category, Tutorial, Graph

from .types import UserType, CategoryType, TutorialType, GraphType, TutorialInterface, ENUSTransType


class Query(graphene.ObjectType):
    # username_exist = graphene.Boolean(username=graphene.String(required=True))
    # email_exist = graphene.Boolean()
    user_info = graphene.Field(UserType)
    all_categories = graphene.List(CategoryType)
    all_tutorial_info = graphene.List(TutorialType)
    tutorial_count = graphene.Int()
    all_translation_info = graphene.List(TutorialInterface,
                                         translation=graphene.String())
    not_translated_count = graphene.Int(translation=graphene.String())

    tutorial = graphene.Field(TutorialInterface,
                              url=graphene.String(),
                              id=graphene.String(),
                              translation=graphene.String())
    graph = graphene.Field(GraphType,
                           url=graphene.String(),
                           id=graphene.String())

    # The most efficient method of finding whether a model with a unique field is a member of a QuerySet
    # def resolve_username_exist(self, info, username):
    #     return User.objects.filter(username=username).exists()

    # def resolve_email_exist(self, info, email):
    #     return User.objects.filter(email=email).exists()

    @login_required
    def resolve_user_info(self, info: ResolveInfo, **kwargs):
        return info.context.user

    def resolve_all_categories(self, info: ResolveInfo, **kwargs):
        return Category.objects.all()

    def resolve_all_tutorial_info(self, info: ResolveInfo, **kwargs):
        return Tutorial.objects.all()

    def resolve_tutorial_count(self, info: ResolveInfo, **kwargs):
        return Tutorial.objects.all().count()

    def resolve_all_translation_info(self, info: ResolveInfo, translation='en-us'):
        trans_table = get_translation_table(translation)
        if trans_table:
            return trans_table.objects.all()
        return None

    def resolve_not_translated_count(self, info: ResolveInfo, translation='en-us'):
        return Tutorial.objects.all().count() - get_translation_table(translation).objects.all().count()

    def resolve_tutorial(self, info: ResolveInfo, url=None, id=None, translation='en-us'):
        translation_table = get_translation_table(translation)
        if translation_table:
            if url:
                return translation_table.objects.get(tutorial_anchor__url=url)
            elif id:
                return translation_table.objects.get(tutorial_anchor__id=id)
        return None

    def resolve_graph(self, info: ResolveInfo, url=None, id=None):
        if url:
            return Graph.objects.get(url=url)
        elif id:
            return Graph.objects.get(id=id)
        return None
