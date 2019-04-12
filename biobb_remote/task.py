""" Base module to handle remote tasks """


class Task():
    """ Classe to handle task execution """
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def execute(self, credentials):
