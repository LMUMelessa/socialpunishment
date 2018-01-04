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
            # Remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ','')] = player.contribution
            # Also display the profit the player made
            data['gameprofit'] = Constants.endowment - self.player.contribution + self.group.indiv_share
        return data


class Vote(Page):
    # Only needed in the voting treatment
    def is_displayed(self):
        return self.player.treatment == 'voting'

    form_model = models.Player
    form_fields = ['vote_A', 'vote_B','vote_C','vote_D','vote_E']

    #TODO: Be cautious, if the initial values of the vote_X are changed
    def error_message(self, values):
        vote_count = sum([values['vote_A'], values['vote_B'], values['vote_C'], values['vote_D'],values['vote_E']])
        if vote_count > 1:
            return 'You can only vote for one player, who you want to exclude.'

    def vars_for_template(self):
        data = {}
        # TODO: Note Vars for template cannot be tested, therefore this has to be safe and doublechecked
        for player in self.group.get_players():
            # Remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ', '')] = player.contribution
        return data


class VoteWaitPage(WaitPage):
    # Only needed in voting treatment
    def is_displayed(self):
        return self.player.treatment == 'voting'

    def after_all_players_arrive(self):
        # Count the votes for every player
        self.group.set_myvotes()
        # Assign for each player if he plays the social game
        self.group.set_social_game()
        # Set the excluded player label on a group variable, if there is one
        self.group.set_excluded_player()


class VoteResults(Page):
   # Only needed in voting treatment
   def is_displayed(self):
       return self.player.treatment == 'voting'
   def vars_for_template(self):
       data = {}
       for player in self.group.get_players():
           data[(player.playerlabel).replace(' ', '') + '_votes'] = player.myvotes
           data[(player.playerlabel).replace(' ', '') + '_plays'] = player.plays
       return data








page_sequence = [
    Instructions,
    Contribution,
    FirstWaitPage,
    ResultsPG,
    Vote,
    VoteWaitPage,
    VoteResults
]
