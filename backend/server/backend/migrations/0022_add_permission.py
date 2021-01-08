# Generated by Django 3.1.5 on 2021-01-07 23:05

from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.db.models import Q, QuerySet

from backend.model.MetaModel import InvitationCodeModel
from backend.model.TutorialRelatedModel import Uploads
from backend.model.UserModel import User, ROLES

ADMIN_GROUP_NAME = 'admin group'
AUTHOR_GROUP_NAME = 'author group'
TRANSLATOR_GROUP_NAME = 'translator group'
VISITOR_GROUP_NAME = 'visitor group'


def config_helper(name, query_set):
    group, created = Group.objects.get_or_create(name=name)
    if created:
        group.permissions.set(query_set)


def configure_permission(*args):
    admin_permissions = Permission.objects.all()
    config_helper(
        name=ADMIN_GROUP_NAME,
        query_set=admin_permissions
    )

    author_permissions: QuerySet = Permission.objects.filter(
        # no delete permission for authors
        (Q(name__startswith='Can add') | Q(name__startswith='Can view') | Q(name__startswith='Can change')) &
        # backend app permission only
        Q(content_type__app_label=User._meta.app_label) &
        # cannot access user and invitation code
        ~(Q(content_type__model=User._meta.model_name) | Q(content_type__model=InvitationCodeModel._meta.model_name))
    )
    config_helper(
        name=AUTHOR_GROUP_NAME,
        query_set=author_permissions
    )

    translator_permissions: QuerySet = author_permissions.filter(
        # can only add or change translations and graph content
        (
                (Q(name__startswith='Can add') | Q(name__startswith='Can change')) &
                (Q(content_type__model=Uploads._meta.model_name) | Q(content_type__model__endswith='translation') |
                 Q(content_type__model__endswith='graph content'))
        )
        # and can view almost anything
        | Q(name__startswith='Can view')
    )
    config_helper(
        name=TRANSLATOR_GROUP_NAME,
        query_set=translator_permissions
    )

    visitor_permissions = translator_permissions.filter(
        # can only view most of the content
        Q(name__startswith='Can view')
    )
    config_helper(
        name=VISITOR_GROUP_NAME,
        query_set=visitor_permissions
    )


def add_helper(role, name):
    users = User.objects.filter(role=role)
    group = Group.objects.get(name=name)
    for user in users:
        user.groups.add(group)


def add_current_users_to_groups(*args):
    for pair in zip(
        [ROLES.VISITOR, ROLES.TRANSLATOR, ROLES.AUTHOR, ROLES.ADMINISTRATOR],
        [VISITOR_GROUP_NAME, TRANSLATOR_GROUP_NAME, AUTHOR_GROUP_NAME, ADMIN_GROUP_NAME]
    ):
        add_helper(*pair)


class Migration(migrations.Migration):
    dependencies = [
        ('backend', '0021_code_name'),
    ]

    operations = [
        migrations.RunPython(configure_permission),
        migrations.RunPython(add_current_users_to_groups)
    ]
