from typing import Optional

import graphene
from django.contrib.auth.models import AbstractUser
from django.db import transaction

from graphql import GraphQLError
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash

from backend.graphql.decorators import anonymous_required
from backend.graphql.mutation_base import SuccessMutationBase
from backend.graphql.utils import process_model_wrapper
from backend.intel_wrappers.intel_wrapper import UserWrapper
from backend.intel_wrappers.validators import password_validator
from backend.model.MetaModel import InvitationCodeModel
from backend.graphql.decorators import login_required
from backend.graphql.types import UserType
from backend.model.UserModel import User


class Register(SuccessMutationBase):
    class Arguments:
        email = graphene.String(required=True)
        username = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        password = graphene.String(required=True)
        invitation_code = graphene.String(required=True)

    user = graphene.Field(UserType, required=True)

    @staticmethod
    def check_existence(email: str, username: str):
        if User.objects.filter(email=email).exists():
            raise GraphQLError('The email %s is already registered.' % email)
        if User.objects.filter(username=username).exists():
            raise GraphQLError('The username %s is already registered.' % username)

    @anonymous_required
    @graphene.resolve_only_args
    def mutate(self, email: str, username: str, password: str, invitation_code: str,
               first_name: str = '', last_name: str = ''):
        email = email.strip()
        username = username.strip()
        password = password.strip()
        invitation_code = invitation_code.strip()
        first_name = first_name.strip()
        last_name = last_name.strip()

        Register.check_existence(email, username)

        if not invitation_code:
            raise GraphQLError("You have to enter an invitation code!")

        invitation_model: Optional[InvitationCodeModel] = InvitationCodeModel.objects.get(
            invitation_code=invitation_code
        )

        if invitation_model is None or not invitation_model.usable:
            raise GraphQLError("Invitation code %s is not valid." % invitation_code)

        role: int = invitation_model.role

        try:
            password_validator(password)
        except AssertionError as e:
            raise GraphQLError(f'Malformed password. Error: {e}')

        with transaction.atomic():
            user_wrapper: UserWrapper = process_model_wrapper(UserWrapper,
                                                              email=email, username=username, role=role,
                                                              first_name=first_name, last_name=last_name)

            user_wrapper.model.set_password(password)
            user_wrapper.save_model()

        return Register(success=True, user=user_wrapper.model)


class Login(SuccessMutationBase):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)

    @anonymous_required
    def mutate(self, info, username, password):
        user = authenticate(username=username, password=password)
        if user is not None:
            login(info.context, user)
        return Login(success=user is not None, user=user)


class Logout(SuccessMutationBase):
    @login_required
    def mutate(self, info):
        user = info.context.user
        if user.is_authenticated:
            logout(info.context)
            return Login(success=True)
        else:
            raise GraphQLError('Not Logged In')


class ChangePassword(SuccessMutationBase):
    class Arguments:
        old_password = graphene.String(required=True)
        new_password = graphene.String(required=True)

    user = graphene.Field(UserType)

    @login_required
    def mutate(self, info, old_password: str, new_password: str):
        user: AbstractUser = info.context.user
        if not user.is_authenticated:
            raise GraphQLError('You must login to change your password!')

        try:
            password_validator(new_password)
        except AssertionError as e:
            raise GraphQLError(f'Malformed password. Error: {e}')

        if not user.check_password(old_password):
            raise GraphQLError('The old password is incorrect!')

        with transaction.atomic():
            user.set_password(new_password)

            user.save()

            update_session_auth_hash(info.context, user)

        return ChangePassword(success=True, user=user)

