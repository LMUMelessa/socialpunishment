from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


class Instructions(Page):
    # TODO delete me
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include':
            return True
        else:
            return False


class Contribution(Page):
    form_model = models.Player
    form_fields = ['contribution']

    #TODO delete me
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include':
            return True
        else:
            return False


class FirstWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()

    # TODO delete me
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include':
            return True
        else:
            return False


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

    # TODO delete me
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include':
            return True
        else:
            return False


class Vote(Page):

    form_model = models.Player

    def get_form_fields(self):
        if self.player.treatment == 'exclude':
            return ['vote_A', 'vote_B', 'vote_C', 'vote_D', 'vote_E', 'exclude_none']
        elif self.player.treatment == 'include':
            return ['vote_A', 'vote_B','vote_C','vote_D','vote_E']


    #TODO: Be cautious, if the initial values of the vote_X are changed
    def error_message(self, values):
        vote_count = sum([values['vote_A'], values['vote_B'], values['vote_C'], values['vote_D'],values['vote_E']])
        if self.player.treatment == 'exclude':
            if vote_count > 0 and values['exclude_none'] == True:
                return 'You cannot exlude a player while non exlcuding any.'
            #enforce the player to choose an option
            if vote_count == 0 and values['exclude_none'] == False:
                return 'Please choose an option.'
        elif self.player.treatment == 'include':
            if vote_count == 0:
                return 'Please invite at least one player.'


    def vars_for_template(self):
        data = {}
        # TODO: Note Vars for template cannot be tested, therefore this has to be safe and doublechecked
        for player in self.group.get_players():
            # Remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ', '')] = player.contribution
        return data

    #TODO delete me
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include':
            return True
        else:
            return False


class VoteWaitPage(WaitPage):
    # Only needed in exclude treatment
    def is_displayed(self):
        return self.player.treatment == 'exclude'

    def after_all_players_arrive(self):
        # Count the votes for every player
        self.group.set_myvotes()
        # Assign for each player if he plays the social game
        self.group.set_social_game()
        # Set the excluded player label on a group variable, if there is one
        self.group.set_excluded_player()

    #TODO delete me:
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include':
            return True
        else:
            return False

class VoteResults(Page):


   def vars_for_template(self):
       data = {}
       for player in self.group.get_players():
           data[(player.playerlabel).replace(' ', '') + '_votes'] = player.myvotes
           if player.plays == True:
                data[(player.playerlabel).replace(' ', '') + '_plays'] = "Yes"
           elif player.plays == False:
               data[(player.playerlabel).replace(' ', '') + '_plays'] = "No"

       return data

    # TODO delete me:
   def is_displayed(self):
       if self.player.treatment == 'exclude' or self.player.treatment == 'include':
           return True
       else:
           return False




class BeforeFamilyFeudWaitPage(WaitPage):
    
    # TODO delete me:
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include':
            return True
        else:
            return False


class FamilyFeud(Page):
    pass


class FamilyFeudResults(Page):

    def vars_for_template(self):

        data_dic = {'alist':[]}
        for group in self.subsession.get_group_matrix():
            helplist = [group[0].group.id_in_subsession,group[0].group.group_ff_points,[]]
            for player in group:
               your_group = 'False'
               if self.player.group.id_in_subsession == player.group.id_in_subsession:
                   your_group = 'True'
               if player.plays == True:
                   helplist[2].append({ 'player_label':player.playerlabel, 'points':player.ff_points, 'your_group':your_group})
               elif player.plays == False:
                   helplist[2].append({'player_label': player.playerlabel, 'points': 'Was excluded', 'your_group':your_group})

            data_dic['alist'].append(helplist)
        return data_dic


    pass

page_sequence = [
    Instructions,
    Contribution,
    FirstWaitPage,
    ResultsPG,
    Vote,
    VoteWaitPage,
    VoteResults,
    BeforeFamilyFeudWaitPage,
    FamilyFeud,
    FamilyFeudResults,
]
