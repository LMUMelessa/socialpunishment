from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from otree_redwood.models import Group as RedwoodGroup

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'pg_vote_famfeud'
    players_per_group = 5
    num_rounds = 3
    #pg - vars
    endowment = 10
    multiplier = 2



class Subsession(BaseSubsession):
    pass


class Group(RedwoodGroup):


    total_cont = models.CurrencyField(
        doc='The overall contribution of the group in the public good game.')

    indiv_share = models.CurrencyField(
        doc='The share the players get after the public good game.')

    # Payoffs for pg game; function also sets total_cont and indiv_share
    def set_payoffs(self):
        self.total_cont = sum([p.contribution for p in self.get_players()])
        self.indiv_share = (self.total_cont * Constants.multiplier) / Constants.players_per_group
        for p in self.get_players():
            p.payoff = (Constants.endowment - p.contribution) + self.indiv_share





class Player(BasePlayer):

    playerlabel = models.CharField(
        doc='The player name. Player A - Player E',
        choices=['Player A', 'Player B', 'Player C', 'Player D', 'Player E'])

    treatment = models.CharField(
        doc='Defines the treatment of the session. The treatment is the same for all players in one session.'
            'In "voting" player can exclude players. In "novoting" no voting stage exists',
        choices=['voting', 'novoting'])

    city = models.CharField(
        doc='Defines the city where the experiment took place ',
        choices=['münchen', 'heidelberg'])

    contribution = models.CurrencyField(
        doc='The players contribution in the public good game',
        verbose_name='What do you want to contribute to the project?',
        min=0,
        max=Constants.endowment)




