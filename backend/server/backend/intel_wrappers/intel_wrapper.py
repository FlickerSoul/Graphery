from __future__ import annotations

import json
from random import random
from typing import Optional, Iterable, Mapping, Type, Union, Any, TypeVar, Generic, List, Tuple

from django.core.files import File
from django.db import transaction
from django.db.models import Model, QuerySet

from backend.intel_wrappers.validators import dummy_validator, category_validator, name_validator, url_validator, \
    categories_validator, code_validator, wrapper_validator, authors_validator, non_empty_text_validator, \
    graph_priority_validator, json_validator, email_validator, username_validator, \
    tutorial_anchors_validator, level_validator, section_validator, first_name_validator, last_name_validator, \
    file_validator, string_validator
from backend.model.TranslationModels import TranslationBase, GraphTranslationBase, ENUS, ZHCN, ENUSGraphContent, \
    ZHCNGraphContent, ESGraphContent, ES
from backend.model.TutorialRelatedModel import Category, Tutorial, Graph, Code, ExecResultJson, Uploads, FAKE_UUID
from backend.model.UserModel import User
from backend.intel_wrappers.wrapper_bases import AbstractWrapper, PublishedWrapper, VariedContentWrapper
from bundle.server_utils.main_functions import time_out_execute


def finalize_prerequisite_wrapper_iter(model_wrappers: Iterable[AbstractWrapper]) -> None:
    for model_wrapper in model_wrappers:
        model_wrapper.finalize_model(overwrite=False)


def _result_json_updater(code_list: Iterable[Code], graph_list: Iterable[Graph]) -> List[Tuple[Code, Graph, Exception]]:
    failed_code_and_graph = []
    for code in code_list:
        for graph in graph_list:
            try:
                response = time_out_execute(code=code.code, graph_json=graph.cyjs)
                if 'data' not in response or 'errors' in response:
                    raise ValueError('Execution went wrong with response: {}'.format(response))

                with transaction.atomic():
                    try:
                        exec_result_json: ExecResultJson = ExecResultJson.objects.get(code=code, graph=graph)
                    except ExecResultJson.DoesNotExist:
                        exec_result_json: ExecResultJson = ExecResultJson(code=code, graph=graph)

                    result_json: List[Mapping] = response['data']['execResult']
                    exec_result_json.json = result_json
                    exec_result_json.save()
            except Exception as e:
                failed_code_and_graph.append(
                    (code, graph, e)
                )

    return failed_code_and_graph


class UserWrapper(AbstractWrapper[User]):
    model_class: Type[User] = User

    def __init__(self):
        AbstractWrapper.__init__(self, {
            'email': email_validator,
            'username': username_validator,
            'first_name': first_name_validator,
            'last_name': last_name_validator,
            'role': dummy_validator,
        })

        self.id = None
        self.username: Optional[str] = None
        self.email: Optional[str] = None
        self.first_name: str = ''
        self.last_name: str = ''
        self.role: Optional[int] = None

    def load_model_var(self, loaded_model: User) -> None:
        super().load_model_var(loaded_model)
        self.username = loaded_model.username
        self.email = loaded_model.email
        self.first_name = loaded_model.first_name
        self.last_name = loaded_model.last_name
        self.role = loaded_model.role

    def make_new_model(self) -> None:
        self.model = User(username=self.username,
                          email=self.email,
                          role=self.role,
                          first_name=self.first_name,
                          last_name=self.last_name)

    def __str__(self):
        return f'<UserWrapper\n' \
               f'email={self.email}\n' \
               f'username={self.username}\n' \
               f'fullname={f"{self.first_name} {self.last_name}"}>'

    def __repr__(self):
        return self.__str__()


class CategoryWrapper(PublishedWrapper[Category]):
    model_class: Type[Category] = Category

    def __init__(self):
        self.category: Optional[str] = None

        PublishedWrapper.__init__(self, {
            'category': category_validator
        })

    def load_model_var(self, loaded_model: Category) -> None:
        super().load_model_var(loaded_model)
        self.category = loaded_model.category

    def make_new_model(self) -> None:
        self.model: Category = self.model_class(category=self.category, is_published=self.is_published)

    def __str__(self):
        return '<CategoryWrapper category_name={}>'.format(self.category)

    def __repr__(self):
        return self.__str__()


class TutorialAnchorWrapper(PublishedWrapper[Tutorial]):
    model_class: Type[Tutorial] = Tutorial

    def __init__(self):
        self.url: Optional[str] = None
        self.name: Optional[str] = None
        self.categories: Optional[Iterable[CategoryWrapper]] = None
        self.level: Optional[int] = None
        self.section: Optional[int] = None

        PublishedWrapper.__init__(self, {
            'url': url_validator,
            'name': name_validator,
            'categories': categories_validator,
            'level': level_validator,
            'section': section_validator,
        })

    def load_model_var(self, loaded_model: Tutorial) -> None:
        super().load_model_var(loaded_model)
        self.url = loaded_model.url
        self.name = loaded_model.name
        self.categories = [CategoryWrapper().load_model(cat) for cat in loaded_model.categories.all()]
        self.level = loaded_model.level
        self.section = loaded_model.section

    def make_new_model(self) -> None:
        self.model: Tutorial = self.model_class(url=self.url, name=self.name,
                                                level=self.level, section=self.section,
                                                is_published=self.is_published)

    def prepare_model(self) -> None:
        finalize_prerequisite_wrapper_iter(self.categories)

    def __str__(self):
        return f'<TutorialWrapper\n' \
               f'url={self.url}\n' \
               f'name={self.name}\n' \
               f'categories={self.categories}>'

    def __repr__(self):
        return self.__str__()


class GraphWrapper(PublishedWrapper[Graph]):
    model_class: Type[Graph] = Graph

    def __init__(self):
        self.url: Optional[str] = None
        self.name: Optional[str] = None
        self.categories: Optional[Iterable[CategoryWrapper]] = None
        self.authors: Optional[Iterable[UserWrapper]] = None
        self.priority: Optional[int] = None
        self.cyjs: Optional[dict] = None
        self.tutorials: Optional[Iterable[TutorialAnchorWrapper]] = None

        PublishedWrapper.__init__(self, {
            'url': url_validator,
            'name': name_validator,
            'categories': categories_validator,
            'authors': authors_validator,
            'priority': graph_priority_validator,
            'cyjs': json_validator,
            'tutorials': tutorial_anchors_validator
        }, post_actions=[self._execute_code_after_submission])

    def _execute_code_after_submission(self) -> List:
        code_list: List[Code] = list(tutorial.code
                                     for tutorial in self.model.tutorials.filter(code__isnull=False))
        graph_list: List[Graph] = [self.model]
        failed_missions = _result_json_updater(code_list, graph_list)
        return failed_missions

    def load_model_var(self, loaded_model: Graph) -> None:
        super().load_model_var(loaded_model)
        self.url = loaded_model.url
        self.name = loaded_model.name
        self.categories = [CategoryWrapper().load_model(cat) for cat in loaded_model.categories.all()]
        self.authors = [UserWrapper().load_model(user) for user in loaded_model.authors.all()]
        self.priority = loaded_model.priority
        self.cyjs = json.loads(loaded_model.cyjs) if isinstance(loaded_model.cyjs, str) else loaded_model.cyjs
        self.tutorials = [TutorialAnchorWrapper().load_model(tutorial_anchor)
                          for tutorial_anchor in loaded_model.tutorials.all()]

    def make_new_model(self) -> None:
        self.model: Graph = self.model_class(url=self.url, name=self.name,
                                             priority=self.priority, cyjs=self.cyjs,
                                             is_published=self.is_published)

    def prepare_model(self) -> None:
        finalize_prerequisite_wrapper_iter(self.categories)
        finalize_prerequisite_wrapper_iter(self.tutorials)
        finalize_prerequisite_wrapper_iter(self.authors)

    def __str__(self):
        return f'<GraphWrapper url={self.url} \n' \
               f'name={self.name}\n' \
               f'categories={self.categories}\n' \
               f'authors={self.authors}\n' \
               f'priority={self.priority}\n' \
               f'cyjs={self.cyjs}\n' \
               f'tutorials={self.tutorials}\n' \
               f'>'

    def __repr__(self):
        return self.__str__()


class CodeWrapper(AbstractWrapper[Code]):
    model_class: Type[Code] = Code

    def __init__(self):
        self.name: Optional[str] = None
        self.tutorial: Optional[TutorialAnchorWrapper] = None
        self.code: Optional[str] = None

        AbstractWrapper.__init__(self, {
            'name': non_empty_text_validator,
            'tutorial': wrapper_validator,
            'code': code_validator
        }, post_actions=[self._execute_code_after_submission])

    def _execute_code_after_submission(self) -> List:
        code_list: List[Code] = [self.model]
        graph_list: QuerySet[Graph] = self.tutorial.model.graph_set.all()
        failed_missions = _result_json_updater(code_list, graph_list)
        return failed_missions

    def load_model_var(self, loaded_model: Code) -> None:
        super().load_model_var(loaded_model)
        self.name = loaded_model.name
        self.tutorial = TutorialAnchorWrapper().load_model(loaded_model.tutorial)
        self.code = loaded_model.code

    def make_new_model(self) -> None:
        self.model: Code = self.model_class(name=self.name,
                                            tutorial=self.tutorial.model,
                                            code=self.code)

    def __str__(self):
        return f'<CodeWrapper\n' \
               f'name={self.name}\n' \
               f'tutorial={self.tutorial}\n' \
               f'code={self.code}>'

    def __repr__(self):
        return self.__str__()


class ExecResultJsonWrapper(AbstractWrapper[ExecResultJson]):
    model_class: Type[ExecResultJson] = ExecResultJson

    def __init__(self):
        AbstractWrapper.__init__(self, {
            'code': wrapper_validator,
            'graph': wrapper_validator,
            'json': json_validator,
        })

        self.code: Optional[CodeWrapper] = None
        self.graph: Optional[GraphWrapper] = None
        self.json: Optional[Mapping] = None

    def load_model_var(self, loaded_model: ExecResultJson) -> None:
        super().load_model_var(loaded_model)
        self.code = CodeWrapper().load_model(loaded_model.code)
        self.graph = GraphWrapper().load_model(loaded_model.graph)
        json_value = loaded_model.json
        self.json = json.loads(json_value) if isinstance(json_value, str) else json_value

    def retrieve_model(self) -> None:
        # TODO Unresolved attribute reference 'objects' for class 'ExecResultJson' ?????
        self.model: ExecResultJson = self.model_class.objects.get(code=self.code.model, graph=self.graph.model)
        self.id = self.model.id

    def make_new_model(self) -> None:
        self.model: ExecResultJson = self.model_class(code=self.code.model, graph=self.graph.model, json=self.json)

    def __str__(self):
        return f'<ExecResultWrapper\n' \
               f'code={self.code}\n' \
               f'graph={self.graph}\n' \
               f'json={self.json}>'

    def __repr__(self):
        return self.__str__()


class UploadsWrapper(PublishedWrapper[Uploads]):
    model_class: Type[Uploads] = Uploads

    def __init__(self):
        self.file: Optional[Union[str, Any]] = None
        self.alias: Optional[str] = None

        super(UploadsWrapper, self).__init__({
            'file': file_validator,
            'alias': string_validator,
        })

        self.id: str = FAKE_UUID

    def load_model_var(self, loaded_model: Uploads) -> None:
        super().load_model_var(loaded_model)
        self.file = loaded_model.file
        self.alias = loaded_model.alias

    def retrieve_model(self) -> None:
        if self.id is not None and self.id != FAKE_UUID:
            self.model: Uploads = Uploads.objects.get(id=self.id)
        elif self.alias:
            self.model: Uploads = Uploads.objects.get(alias=self.alias)
        elif isinstance(self.file, File):
            self.model: Uploads = Uploads.objects.get(file=self.file.name)
        else:
            raise ValueError(f'Cannot find file model since `id` {self.id} and `file` {self.file}  '
                             f'are either empty or not valid..')

    def make_new_model(self) -> None:
        if isinstance(self.file, File):
            self.model: Uploads = Uploads(file=self.file,
                                          alias=(
                                              self.alias if self.alias else f'{self.file.name}_{int(random() * 100000)}'
                                          ),
                                          is_published=self.is_published)
        else:
            raise ValueError(f'Cannot create upload since `file` {self.file} '
                             f'(alias: {self.alias}) is not a File instance.')


_T = TypeVar('_T', bound=Model)


class TutorialTranslationContentWrapper(VariedContentWrapper[_T], Generic[_T]):
    def __init__(self):
        self.title: Optional[str] = None
        self.authors: Optional[Iterable[UserWrapper]] = None
        self.tutorial_anchor: Optional[TutorialAnchorWrapper] = None
        self.abstract: Optional[str] = None
        self.content_md: Optional[str] = None
        self.content_html: Optional[str] = None

        super(TutorialTranslationContentWrapper, self).__init__({
            'title': non_empty_text_validator,
            'authors': authors_validator,
            'tutorial_anchor': wrapper_validator,
            'abstract': non_empty_text_validator,
            'content_md': non_empty_text_validator,
            'content_html': non_empty_text_validator,
        })

    def load_model_var(self, loaded_model: _T) -> None:
        super().load_model_var(loaded_model)

        self.model_class = type(loaded_model)
        self.title = loaded_model.title
        self.authors = [UserWrapper().load_model(user_model) for user_model in loaded_model.authors.all()]
        self.tutorial_anchor = TutorialAnchorWrapper().load_model(loaded_model.tutorial_anchor)
        self.abstract = loaded_model.abstract
        self.content_md = loaded_model.content_md
        self.content_html = loaded_model.content_html

    def set_model_class(self, model_class: Type[_T]) -> TutorialTranslationContentWrapper[_T]:
        self.model_class = model_class
        return self

    def set_variables(self, **kwargs) -> TutorialTranslationContentWrapper[_T]:
        the_model_class = kwargs.pop('model_class', None)
        if the_model_class is not None and issubclass(the_model_class, TranslationBase):
            self.set_model_class(the_model_class)

        super().set_variables(**kwargs)
        return self

    def retrieve_model(self) -> None:
        self.model: TranslationBase = self.model_class.objects.get(id=self.id)

    def make_new_model(self) -> None:
        self.model: TranslationBase = self.model_class(title=self.title,
                                                       tutorial_anchor=self.tutorial_anchor.model,
                                                       abstract=self.abstract,
                                                       content_md=self.content_md,
                                                       content_html=self.content_html,
                                                       is_published=self.is_published)

    def prepare_model(self) -> None:
        finalize_prerequisite_wrapper_iter(self.authors)

    def __str__(self):
        return f'<TutorialContentWrapper\n' \
               f'model_class={self.model_class}\n' \
               f'model={self.model}\n' \
               f'title={self.title}\n' \
               f'tutorial_anchor={self.tutorial_anchor.model}\n' \
               f'abstract={self.abstract}\n' \
               f'content_md={self.content_md}\n' \
               f'content_html={self.content_html}>'

    def __repr__(self):
        return self.__str__()


class ENUSTutorialContentWrapper(TutorialTranslationContentWrapper[ENUS]):
    model_class = ENUS


class ZHCNTutorialContentWrapper(TutorialTranslationContentWrapper[ZHCN]):
    model_class = ZHCN


class ESTutorialContentWrapper(TutorialTranslationContentWrapper[ES]):
    model_class = ES


_S = TypeVar('_S', bound=Model)


class GraphTranslationContentWrapper(VariedContentWrapper[_S], Generic[_S]):
    def __init__(self):
        self.title: Optional[str] = None
        self.abstract_md: Optional[str] = None
        self.abstract: Optional[str] = None
        self.graph_anchor: Optional[GraphWrapper] = None

        super(GraphTranslationContentWrapper, self).__init__({
            'title': non_empty_text_validator,
            'abstract_md': non_empty_text_validator,
            'abstract': non_empty_text_validator,
            'graph_anchor': wrapper_validator,
        })

    def load_model_var(self, loaded_model: _S) -> None:
        super().load_model_var(loaded_model)

        self.model_class = type(loaded_model)
        self.title = loaded_model.title
        self.abstract_md = loaded_model.abstract_md
        self.abstract = loaded_model.abstract
        self.graph_anchor = GraphWrapper().load_model(loaded_model.graph_anchor)

    def set_model_class(self, model_class: Type[_S]) -> GraphTranslationContentWrapper[_S]:
        self.model_class = model_class
        return self

    def set_variables(self, **kwargs) -> GraphTranslationContentWrapper[_S]:
        the_model_class = kwargs.pop('model_class', None)
        if the_model_class is not None and issubclass(the_model_class, GraphTranslationBase):
            self.set_model_class(the_model_class)

        super().set_variables(**kwargs)
        return self

    def retrieve_model(self) -> None:
        self.model: GraphTranslationBase = self.model_class.objects.get(id=self.id)

    def make_new_model(self) -> None:
        self.model: GraphTranslationBase = self.model_class(graph_anchor=self.graph_anchor.model,
                                                            title=self.title,
                                                            abstract=self.abstract,
                                                            abstract_md=self.abstract_md,
                                                            is_published=self.is_published)

    def __str__(self):
        return f'<GraphContentWrapper\n' \
               f'model_class={self.model_class}\n' \
               f'model={self.model}\n' \
               f'title={self.title}\n' \
               f'abstract_md={self.abstract_md}' \
               f'abstract={self.abstract}\n' \
               f'graph_anchor={self.graph_anchor}>'

    def __repr__(self):
        return self.__str__()


class ENUSGraphContentWrapper(GraphTranslationContentWrapper[ENUSGraphContent]):
    model_class = ENUSGraphContent


class ZHCNGraphContentWrapper(GraphTranslationContentWrapper[ZHCNGraphContent]):
    model_class = ZHCNGraphContent


class ESGraphContentWrapper(GraphTranslationContentWrapper[ESGraphContent]):
    model_class = ESGraphContent


FixedTypeWrapper = Union[UserWrapper,
                         CategoryWrapper,
                         TutorialAnchorWrapper,
                         GraphWrapper,
                         CodeWrapper,
                         ExecResultJsonWrapper,
                         ENUSTutorialContentWrapper,
                         ZHCNTutorialContentWrapper,
                         ENUSGraphContentWrapper,
                         ZHCNGraphContentWrapper]

VariedTypeWrapper = Union[TutorialTranslationContentWrapper,
                          GraphTranslationContentWrapper]

WrappersType = Union[FixedTypeWrapper, VariedTypeWrapper]
