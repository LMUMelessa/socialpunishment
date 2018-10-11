from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import random


class Instructions(Page):

    timeout_seconds = Constants.timeoutsecs

    def is_displayed(self):
        if self.player.treatment == 'FF' or self.player.round_number == Constants.num_rounds:
            return False
        else:
            return True


class ControlQuestions(Page):
    timeout_seconds = 300


    form_model = 'player'

    def get_form_fields(self):
        if self.player.treatment=='exclude':
            return ['control1','control2','control3a','control3b', 'control3c', 'control3d', 'control4', 'control5', 'control6' ,'control7exclude','control8']
        elif self.player.treatment=='control':
            return ['control1', 'control2' , 'control3a','control3b','control3c','control7control', 'control8']

    def is_displayed(self):
        if self.player.treatment=="FF":
            return False
        if self.round_number == 1:
            return True
        else:
            return False


class Contribution(Page):

    form_model = models.Player
    form_fields = ['contribution']

    def vars_for_template(self):
        return {'round_number': self.player.round_number - 1}

    def is_displayed(self):
        if self.player.treatment == 'FF':
            return False
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        else:
            return True


class FirstWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_round_payoffs()

    def is_displayed(self):
        if self.player.treatment == 'FF':
            return False
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        else:
            return True


class ResultsPG(Page):

    timeout_seconds = Constants.timeoutsecs

    def vars_for_template(self):
        data = {'round_number':self.player.round_number -1 ,}
        for player in self.group.get_players():
            # Remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ','')] = player.contribution
        return data

    def is_displayed(self):
        if self.player.treatment == 'FF':
            return False
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        else:
            return True


class Vote(Page):

    timeout_seconds = Constants.timeoutsecs

    form_model = models.Player

    def get_form_fields(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'feedback':
            return ['vote_A', 'vote_B', 'vote_C', 'vote_D', 'vote_E', 'exclude_none']
        elif self.player.treatment == 'include':
            return ['vote_A', 'vote_B','vote_C','vote_D','vote_E']


    #TODO: Be cautious, if the initial values of the vote_X are changed
    def error_message(self, values):
        vote_count = sum([values['vote_A'], values['vote_B'], values['vote_C'], values['vote_D'],values['vote_E']])
        if self.player.treatment == 'exclude':
            if vote_count > 0 and values['exclude_none'] == True:
                return 'Sie können nicht für keinen und einen Spieler wählen.'
            # Enforce the player to choose an option
            if vote_count == 0 and values['exclude_none'] == False:
                return 'Please choose an option.'
        elif self.player.treatment == 'include':
            if vote_count == 0:
                return 'Please invite at least one player.'


    def vars_for_template(self):
        data = {'round_number': self.player.round_number-1}
        # TODO: Note Vars for template cannot be tested, therefore this has to be safe and doublechecked
        for player in self.group.get_players():
            # Remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ', '')] = player.contribution
        return data

    def is_displayed(self):
        if self.player.treatment == 'FF' or self.player.treatment == 'control':
            return False
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        else:
            return True


class VoteWaitPage(WaitPage):

    def after_all_players_arrive(self):
        # Count the votes for every player
        # And the votes every player made
        self.group.set_myvotes()
        # Assign for each player if he plays the social game
        self.group.set_social_game()
        # Update the payoffs as voting is costly in feedback and exclusion treatment
        if self.group.get_players()[0].treatment == "feedback" or self.group.get_players()[0].treatment == "exclude":
            for player in self.group.get_players():
                player.update_round_payoff()

    def is_displayed(self):
        if self.player.treatment == 'FF' or self.player.treatment == 'control':
            return False
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        else:
            return True


class VoteResults(Page):

   timeout_seconds = Constants.timeoutsecs

   def vars_for_template(self):
       data = {'round_number':self.player.round_number-1}
       for player in self.group.get_players():
           data[(player.playerlabel).replace(' ', '') + '_votes'] = player.myvotes
           if player.plays == True:
                data[(player.playerlabel).replace(' ', '') + '_plays'] = "Ja"
           elif player.plays == False:
               data[(player.playerlabel).replace(' ', '') + '_plays'] = "Nein"
       return data

   def is_displayed(self):
       if self.player.treatment == 'FF' or self.player.treatment == 'control':
           return False
       if self.round_number == 1 or self.round_number == Constants.num_rounds:
           return False
       else:
           return True

   def before_next_page(self):
       # In the feedback treatment, player.plays is used to determine which player got the most negative feedback.
       # The FF game uses this to prevent players from playing in the other treatments. Instead, in the feedback treatment all players play FF.
       # Therefore, reset the variable here s. t. all can play FF in the Feedback treatment.
       if self.player.treatment == 'feedback':
           self.player.plays = True


class ValuateFFSelect(Page):

    timeout_seconds = Constants.timeoutsecs

    form_model = models.Player
    form_fields = ['ff_valuation']

    def is_displayed(self):
        if self.player.treatment == "FF":
            return False
        if self.round_number == Constants.num_rounds:
            return True
        else:
            return False

    def before_next_page(self):

        ## I also do the complete payoff calculation here
        ## Determine from which round the payoff will be taken randomly for every player
        ## Then set the payoff to this particular round_payoff

        #Select a round from the 10 playing rounds (e.g. cut off the practive round and the valuation_ff round)
        if Constants.num_rounds > 3:

            payround = random.choice(range(2,Constants.num_rounds,1))
            self.player.payoff = self.player.in_round(payround).round_payoff
        else:
            payround = 2
            self.player.payoff = self.player.in_round(payround).round_payoff


        ## FF valuation here
        ## determine if the player is allowed to play FF one last time or if he has to watch the screen
        ## depending on his
        self.player.random_ff_valuation = random.choice(range(600))/100



        if self.player.random_ff_valuation > float(self.player.ff_valuation):
            self.player.plays = False
        else:
            # Player plays again, subtract the computer number his overall payoff
            # First recalculate to points
            self.player.payoff = self.player.payoff - (1/ float(self.session.config['real_world_currency_per_point'])* float(self.player.random_ff_valuation))



class WaitAfterValuateFFSelect(WaitPage):

    def is_displayed(self):
        if self.player.treatment=="FF":
            return False
        if self.round_number == Constants.num_rounds:
            return True
        else:
            return False

    wait_for_all_groups = True


class ValuateFFResult(Page):

    timeout_seconds = 15

    def is_displayed(self):
        if self.player.treatment=="FF":
            return False
        if self.round_number == Constants.num_rounds:
            return True
        else:
            return False



class BeforeFamilyFeudWaitPage(WaitPage):
    wait_for_all_groups = True


class FamilyFeud(Page):
    pass

# defo need this because the results are displayed over all groups
class AfterFamilyFeudWaitPage(WaitPage):
    wait_for_all_groups = True



class FamilyFeudResults(Page):

    timeout_seconds = Constants.timeoutsecs

    #don't display in the valuation round (last round) and practice round (first round)
    def is_displayed(self):
        if self.player.round_number == Constants.num_rounds or self.player.round_number == 1:
            return False
        else:
            return True



    def vars_for_template(self):

        data_dic = {'round_number':self.player.round_number-1,'alist':[]}
        for group in self.subsession.get_group_matrix():
            helplist = [group[0].group.id_in_subsession,group[0].group.group_ff_points,[]]
            for player in group:
               your_group = 'False'
               if self.player.group.id_in_subsession == player.group.id_in_subsession:
                   your_group = 'True'
               thats_you = 'False'
               if (your_group == 'True') and (self.player.id_in_group == player.id_in_group):
                   thats_you = 'True'
               pointinfo = None
               if player.plays == True:
                   pointinfo = player.ff_points
               else:
                   pointinfo = 'Was excluded'
               helplist[2].append({ 'player_label':player.playerlabel, 'points':pointinfo, 'your_group':your_group, 'thats_you':thats_you})
            data_dic['alist'].append(helplist)
        return data_dic



class RateYourExperience(Page):


    timeout_seconds = Constants.timeoutsecs

    def vars_for_template(self):
        return {'round_number':self.player.round_number -1}

    def is_displayed(self):
        if self.player.treatment=="FF":
            return False

        #don't show in the valuation round and in the practice round
        if self.player.round_number == Constants.num_rounds or self.player.round_number == 1:
            return False
        else:
            return True

    form_model = models.Player
    form_fields = ['ff_experience']



class Questionnaire(Page):


    form_model = 'player'

    def get_form_fields(self):
        if self.player.treatment == 'exclude':
            return ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7','q8','q9','q10']
        elif self.player.treatment == 'control':
            return ['q1','q2','q5','q6','q7','q8','q9','q10']



    def is_displayed(self):
        return Constants.num_rounds == self.round_number

class EndPage(Page):
    def is_displayed(self):
        if self.player.round_number == Constants.num_rounds:
            return True
        else:
            return False








page_sequence = [
    Instructions,
    ControlQuestions,#After this page there will be the FamilyFeud page and this has a group waitpage before
    Contribution,
    FirstWaitPage,
    ResultsPG,
    Vote,
    VoteWaitPage,
    VoteResults,
    ValuateFFSelect,
    WaitAfterValuateFFSelect,
    ValuateFFResult,
    BeforeFamilyFeudWaitPage,
    FamilyFeud,
    AfterFamilyFeudWaitPage,
    FamilyFeudResults,
    RateYourExperience,
    Questionnaire,
    EndPage,
]
