from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


class Instructions(Page):

    timeout_seconds = Constants.timoutsecs

    # TODO delete me
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include' or self.player.treatment == 'control' or self.player.treatment == 'feedback':
            return True
        else:
            return False

class ControlQuestions(Page):

    timeout_seconds = Constants.timoutsecs

    form_model = models.Player
    form_fields = ['control1', 'control2', 'control3' , 'control4' , 'control5']


    def is_displayed(self):
        if self.player.treatment=="FF":
            return False
        if self.round_number == 1:
            return True
        else:
            return False


class AfterControlQuestionsWaitPage(WaitPage):
    wait_for_all_groups = True




class Contribution(Page):

    form_model = models.Player
    form_fields = ['contribution']

    timeout_seconds = Constants.timoutsecs

    #TODO delete me
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include' or self.player.treatment == 'control' or self.player.treatment == 'feedback':
            return True
        else:
            return False


class FirstWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()

    # TODO delete me
    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include' or self.player.treatment == 'control' or self.player.treatment == 'feedback':
            return True
        else:
            return False


class ResultsPG(Page):

    timeout_seconds = Constants.timoutsecs

    def vars_for_template(self):
        data = {}
        for player in self.group.get_players():
            # Remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ','')] = player.contribution
            # Also display the profit the player made
            # TODO: Why am I doing this? Just use  {{player.payoff}} in the template?
            data['gameprofit'] = Constants.endowment - self.player.contribution + self.group.indiv_share
        return data

    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include' or self.player.treatment == 'control' or self.player.treatment == 'feedback':
            return True
        else:
            return False


class Vote(Page):

    timeout_seconds = Constants.timoutsecs

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
                return 'You cannot exlude a player while non exlcuding any.'
            # Enforce the player to choose an option
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

    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include' or self.player.treatment == 'feedback':
            return True
        else:
            return False


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
                print("I should have updated the payoff?")
                player.update_payoff()

    def is_displayed(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'include' or self.player.treatment == 'feedback':
            return True
        else:
            return False


class VoteResults(Page):

   timeout_seconds = Constants.timoutsecs

   def vars_for_template(self):
       data = {}
       for player in self.group.get_players():
           data[(player.playerlabel).replace(' ', '') + '_votes'] = player.myvotes
           if player.plays == True:
                data[(player.playerlabel).replace(' ', '') + '_plays'] = "Yes"
           elif player.plays == False:
               data[(player.playerlabel).replace(' ', '') + '_plays'] = "No"

       return data

   def is_displayed(self):
       if self.player.treatment == 'exclude' or self.player.treatment == 'include' or self.player.treatment == 'feedback':
           return True
       else:
           return False

   def before_next_page(self):
       # In the feedback treatment, player.plays is used to determine which player got the most negative feedback.
       # The FF game uses this to prevent players from playing in the other treatments. Instead, in the feedback treatment all players play FF.
       # Therefore, reset the variable here s. t. all can play FF in the Feedback treatment.
       if self.player.treatment == 'feedback':
           self.player.plays = True


class BeforeFamilyFeudWaitPage(WaitPage):
    wait_for_all_groups = True


class FamilyFeud(Page):
    pass

class AfterFamilyFeudWaitPage(WaitPage):
    wait_for_all_groups = True



class FamilyFeudResults(Page):


    timeout_seconds = Constants.timoutsecs

    def vars_for_template(self):

        data_dic = {'alist':[]}
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
    timeout_seconds = Constants.timoutsecs

    form_model = models.Player
    form_fields = ['ff_experience']



class Questionnaire(Page):
    form_model = models.Player
    form_fields = ['age', 'student_bool', 'subject', 'stringfield1', 'stringfield2' , 'number1']


    def is_displayed(self):
        return Constants.num_rounds == self.round_number







page_sequence = [
    Instructions,
    ControlQuestions,
    AfterControlQuestionsWaitPage,
    #Contribution,
    #FirstWaitPage,
    #ResultsPG,
    #Vote,
    #VoteWaitPage,
    #VoteResults,
    #BeforeFamilyFeudWaitPage,
    #FamilyFeud,
    #AfterFamilyFeudWaitPage,
    #FamilyFeudResults,
    RateYourExperience,
    Questionnaire,
]
