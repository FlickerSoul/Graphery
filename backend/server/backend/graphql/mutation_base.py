import graphene


class SuccessBase(graphene.Mutation):
    success = graphene.Boolean(required=True)

    def mutate(self, info, *args, **kwargs):
        raise NotImplementedError
