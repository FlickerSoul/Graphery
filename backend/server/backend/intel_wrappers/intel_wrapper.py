import json
from typing import Optional, Iterable, Mapping, Type, Union

from backend.intel_wrappers.validators import dummy_validator, category_validator, name_validator, url_validator, \
    categories_validator
from backend.model.TranslationModels import TranslationBase, GraphTranslationBase
from backend.model.TutorialRelatedModel import Category, Tutorial, Graph, Code, ExecResultJson
from backend.model.UserModel import User
from backend.intel_wrappers.wrapper_bases import AbstractWrapper, PublishedWrapper


def finalize_prerequisite_wrapper(model_wrapper: AbstractWrapper, overwrite: bool = False) -> None:
    model_wrapper.prepare_model()
    model_wrapper.get_model(overwrite=overwrite)
    model_wrapper.finalize_model()


def finalize_prerequisite_wrapper_iter(model_wrappers: Iterable[AbstractWrapper]) -> None:
    for model_wrapper in model_wrappers:
        finalize_prerequisite_wrapper(model_wrapper)


class UserWrapper(AbstractWrapper):
    model_class: Type[User] = User

    def __init__(self):
        self.id: Optional[str] = None
        self.username: Optional[str] = None
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.role: Optional[int] = None

        AbstractWrapper.__init__(self, {
            'email': dummy_validator,
            'username': dummy_validator,
            'password': dummy_validator,
            'role': dummy_validator,
        })

    def load_model(self, loaded_model: User) -> 'UserWrapper':
        super().load_model(loaded_model)
        self.id = loaded_model.id
        self.username = loaded_model.username
        self.email = loaded_model.email
        self.password = loaded_model.password
        self.role = loaded_model.role
        return self

    def overwrite_model(self) -> None:
        if not self.model_exists():
            return

        field_list = [field for field in self.validators.keys() if field != 'password']
        for field in field_list:
            setattr(self.model, field, getattr(self, field))
        if len(self.password) <= 20:
            self.model.set_password(self.password)

    def retrieve_model(self) -> None:
        self.model = User.objects.get(id=self.id)

    def make_new_model(self) -> None:
        self.model = User.objects.create_user(username=self.username,
                                              email=self.email,
                                              password=self.password,
                                              role=self.role)

    def __str__(self):
        return f'<UserWrapper\n' \
               f'email={self.email}\n' \
               f'username={self.username}\n' \
               f'password={self.password}>'

    def __repr__(self):
        return self.__str__()


class CategoryWrapper(PublishedWrapper):
    model_class: Type[Category] = Category

    def __init__(self):
        self.id: Optional[str] = None
        self.category: Optional[str] = None

        PublishedWrapper.__init__(self, {
            'id': dummy_validator,
            'category': category_validator
        })

    def load_model(self, loaded_model: Category) -> 'CategoryWrapper':
        super().load_model(loaded_model)
        self.id = loaded_model.id
        self.category = loaded_model.category
        return self

    def retrieve_model(self) -> None:
        self.model: Category = self.model_class.objects.get(id=self.id)

    def make_new_model(self) -> None:
        self.model: Category = self.model_class(category=self.category, is_published=self.is_published)

    def __str__(self):
        return '<CategoryWrapper category_name={}>'.format(self.category)

    def __repr__(self):
        return self.__str__()


class TutorialAnchorWrapper(PublishedWrapper):
    model_class: Type[Tutorial] = Tutorial

    def __init__(self):
        self.id: Optional[str] = None
        self.url: Optional[str] = None
        self.name: Optional[str] = None
        self.categories: Optional[Iterable[CategoryWrapper]] = None

        PublishedWrapper.__init__(self, {
            'id': dummy_validator,
            'url': url_validator,
            'name': name_validator,
            'categories': categories_validator,
        })

    def load_model(self, loaded_model: Tutorial) -> 'TutorialAnchorWrapper':
        super().load_model(loaded_model)
        self.id = loaded_model.id
        self.url = loaded_model.url
        self.name = loaded_model.name
        self.categories = [CategoryWrapper().load_model(cat) for cat in loaded_model.categories.all()]
        return self

    def retrieve_model(self) -> None:
        self.model: Tutorial = self.model_class.objects.get(id=self.id)

    def make_new_model(self) -> None:
        self.model: Tutorial = self.model_class(url=self.url, name=self.name, is_published=False)

    def prepare_model(self) -> None:
        finalize_prerequisite_wrapper_iter(self.categories)

    def finalize_model(self) -> None:
        self.save_model()
        self.model.categories.set(wrapper.model for wrapper in self.categories)
        self.save_model()

    def __str__(self):
        return f'<TutorialWrapper\n' \
               f'url={self.url}\n' \
               f'name={self.name}\n' \
               f'categories={self.categories}>'

    def __repr__(self):
        return self.__str__()


class GraphWrapper(PublishedWrapper):
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
            'url': dummy_validator,
            'name': dummy_validator,
            'categories': dummy_validator,
            'authors': dummy_validator,
            'priority': dummy_validator,
            'cyjs': dummy_validator,
            'tutorials': dummy_validator
        })

    def load_model(self, loaded_model: Graph) -> 'GraphWrapper':
        super().load_model(loaded_model)
        self.url = loaded_model.url
        self.name = loaded_model.name
        self.categories = [CategoryWrapper().load_model(cat) for cat in loaded_model.categories.all()]
        self.authors = [UserWrapper().load_model(user) for user in loaded_model.authors.all()]
        self.priority = loaded_model.priority
        self.cyjs = json.loads(loaded_model.cyjs) if isinstance(loaded_model.cyjs, str) else loaded_model.cyjs
        self.tutorials = [TutorialAnchorWrapper().load_model(tutorial_anchor)
                          for tutorial_anchor in loaded_model.tutorials.all()]
        return self

    def retrieve_model(self) -> None:
        self.model: Graph = self.model_class.objects.get(url=self.url, name=self.name)

    def make_new_model(self) -> None:
        self.model: Graph = self.model_class(url=self.url, name=self.name,
                                             priority=self.priority, cyjs=self.cyjs,
                                             is_published=False)

    def prepare_model(self) -> None:
        finalize_prerequisite_wrapper_iter(self.categories)
        finalize_prerequisite_wrapper_iter(self.tutorials)
        finalize_prerequisite_wrapper_iter(self.authors)

    def finalize_model(self) -> None:
        self.save_model()

        self.model.categories.set(wrapper.model for wrapper in self.categories)
        self.model.tutorials.set(wrapper.model for wrapper in self.tutorials)
        self.model.authors.set(wrapper.model for wrapper in self.authors)

        self.save_model()

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


class CodeWrapper(AbstractWrapper):
    model_class: Type[Code] = Code

    def __init__(self):
        self.tutorial: Optional[TutorialAnchorWrapper] = None
        self.code: Optional[str] = None

        AbstractWrapper.__init__(self, {
            'tutorial': dummy_validator,
            'code': dummy_validator
        })

    def load_model(self, loaded_model: Code) -> 'CodeWrapper':
        super().load_model(loaded_model=loaded_model)
        self.tutorial = TutorialAnchorWrapper().load_model(loaded_model.tutorial)
        self.code = loaded_model.code
        return self

    def retrieve_model(self) -> None:
        self.model: Code = self.model_class.objects.get(tutorial=self.tutorial.model)

    def make_new_model(self) -> None:
        self.model: Code = self.model_class(tutorial=self.tutorial.model, code=self.code)

    def __str__(self):
        return f'<CodeWrapper\n' \
               f'tutorial={self.tutorial}\n' \
               f'code={self.code}>'

    def __repr__(self):
        return self.__str__()


class ExecResultJsonWrapper(AbstractWrapper):
    model_class: Type[ExecResultJson] = ExecResultJson

    def __init__(self):
        self.code: Optional[CodeWrapper] = None
        self.graph: Optional[GraphWrapper] = None
        self.json: Optional[Mapping] = None

        AbstractWrapper.__init__(self, {
            'code': dummy_validator,
            'graph': dummy_validator,
            'json': dummy_validator,
        })

    def load_model(self, loaded_model: ExecResultJson) -> 'ExecResultJsonWrapper':
        super().load_model(loaded_model=loaded_model)
        self.code = CodeWrapper().load_model(loaded_model.code)
        self.graph = GraphWrapper().load_model(loaded_model.graph)
        json_value = loaded_model.json
        self.json = json.loads(json_value) if isinstance(json_value, str) else json_value
        return self

    def retrieve_model(self) -> None:
        # TODO Unresolved attribute reference 'objects' for class 'ExecResultJson' ?????
        self.model: ExecResultJson = self.model_class.objects.get(code=self.code.model, graph=self.graph.model)

    def make_new_model(self) -> None:
        self.model: ExecResultJson = self.model_class(code=self.code.model, graph=self.graph.model, json=self.json)

    def __str__(self):
        return f'<ExecResultWrapper\n' \
               f'code={self.code}\n' \
               f'graph={self.graph}\n' \
               f'json={self.json}>'

    def __repr__(self):
        return self.__str__()


class TutorialTranslationContentWrapper(PublishedWrapper):
    def __init__(self):
        self.model_class: Optional[Type[TranslationBase]] = None

        self.title: Optional[str] = None
        self.authors: Optional[Iterable[UserWrapper]] = None
        self.tutorial_anchor: Optional[TutorialAnchorWrapper] = None
        self.abstract: Optional[str] = None
        self.content_md: Optional[str] = None
        self.content_html: Optional[str] = None

        PublishedWrapper.__init__(self, {
            'title': dummy_validator,
            'authors': dummy_validator,
            'tutorial_anchor': dummy_validator,
            'abstract': dummy_validator,
            'content_md': dummy_validator,
            'content_html': dummy_validator,
        })

    def load_model(self, loaded_model: TranslationBase) -> 'TutorialTranslationContentWrapper':
        super().load_model(loaded_model=loaded_model)
        self.title = loaded_model.title
        self.authors = [UserWrapper().load_model(user_model) for user_model in loaded_model.authors.all()]
        self.tutorial_anchor = TutorialAnchorWrapper().load_model(loaded_model.tutorial_anchor)
        self.abstract = loaded_model.abstract
        self.content_md = loaded_model.content_md
        self.content_html = loaded_model.content_html
        return self

    def set_model_class(self, model_class: Type[TranslationBase]) -> 'TutorialTranslationContentWrapper':
        self.model_class = model_class
        return self

    def set_variables(self, **kwargs) -> 'TutorialTranslationContentWrapper':
        the_model_class = kwargs.pop('model_class', None)
        if the_model_class is not None and issubclass(the_model_class, TranslationBase):
            self.set_model_class(the_model_class)

        super().set_variables(**kwargs)
        return self

    def retrieve_model(self) -> None:
        self.model: TranslationBase = self.model_class.objects.get(tutorial_anchor=self.tutorial_anchor.model)

    def make_new_model(self) -> None:
        self.model: TranslationBase = self.model_class(title=self.title,
                                                       tutorial_anchor=self.tutorial_anchor.model,
                                                       abstract=self.abstract,
                                                       content_md=self.content_md,
                                                       content_html=self.content_html)

    def prepare_model(self) -> None:
        finalize_prerequisite_wrapper_iter(self.authors)

    def finalize_model(self) -> None:
        self.save_model()
        self.model.authors.set(wrapper.model for wrapper in self.authors)
        self.save_model()

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


class GraphTranslationContentWrapper(PublishedWrapper):
    def __init__(self):
        self.model_class: Optional[Type[GraphTranslationBase]] = None

        self.title: Optional[str] = None
        self.abstract: Optional[str] = None
        self.graph_anchor: Optional[GraphWrapper] = None

        PublishedWrapper.__init__(self, {
            'title': dummy_validator,
            'abstract': dummy_validator,
            'graph_anchor': dummy_validator,
        })

    def load_model(self, loaded_model: GraphTranslationBase) -> 'GraphTranslationContentWrapper':
        super().load_model(loaded_model=loaded_model)
        self.title = loaded_model.title
        self.abstract = loaded_model.abstract
        self.graph_anchor = GraphWrapper().load_model(loaded_model.graph_anchor)
        return self

    def set_model_class(self, model_class: Type[GraphTranslationBase]) -> 'GraphTranslationContentWrapper':
        self.model_class = model_class
        return self

    def set_variables(self, **kwargs) -> 'GraphTranslationContentWrapper':
        the_model_class = kwargs.pop('model_class', None)
        if the_model_class is not None and issubclass(the_model_class, GraphTranslationBase):
            self.set_model_class(the_model_class)

        super().set_variables(**kwargs)
        return self

    def retrieve_model(self) -> None:
        self.model: GraphTranslationBase = self.model_class.objects.get(graph_anchor=self.graph_anchor.model)

    def make_new_model(self) -> None:
        self.model: GraphTranslationBase = self.model_class(graph_anchor=self.graph_anchor.model,
                                                            title=self.title,
                                                            abstract=self.abstract)

    def __str__(self):
        return f'<GraphContentWrapper\n' \
               f'model_class={self.model_class}\n' \
               f'model={self.model}\n' \
               f'title={self.title}\n' \
               f'abstract={self.abstract}\n' \
               f'graph_anchor={self.graph_anchor}>'

    def __repr__(self):
        return self.__str__()


FixedTypeWrapper = Union[UserWrapper,
                         CategoryWrapper,
                         TutorialAnchorWrapper,
                         GraphWrapper,
                         CodeWrapper,
                         ExecResultJsonWrapper]

VariedTypeWrapper = Union[TutorialTranslationContentWrapper,
                          GraphTranslationContentWrapper]

WrappersType = Union[FixedTypeWrapper, VariedTypeWrapper]
