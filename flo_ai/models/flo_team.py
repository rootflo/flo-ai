from flo_ai.models.flo_member import FloMember


class FloTeam:
    def __init__(self, name: str, members: list[FloMember]) -> None:
        self.name = name
        self.members = members

    class Builder:
        def __init__(self, name: str, members: list[FloMember]) -> None:
            self.name = name
            self.members = members
            self.member_names = list(map(lambda x: x.name, self.members))

        def build(self):
            return FloTeam(name=self.name, members=self.members)
