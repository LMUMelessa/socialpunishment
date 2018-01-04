from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


class Instructions(Page):
    pass

class Contribution(Page):
    form_model = models.Player
    form_fields = ['contribution']

class FirstWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()

class ResultsPG(Page):
    def vars_for_template(self):
        data = {}
        #TODO: Note: Vars for template cannot be tested, therefore this has to be safe and doublechecked
        for player in self.group.get_players():
            #remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ','')] = player.cont
            #also display the profit the player made
            data['gameprofit'] = Constants.endowment - self.player.contribution + self.group.indiv_share
        return data










page_sequence = [
    Instructions,
    Contribution,
    FirstWaitPage,
    ResultsPG
]
