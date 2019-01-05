from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import random


class Instructions(Page):

    def is_displayed(self):
        if self.player.treatment == 'FF':
            return False
        else:
            return True

    def vars_for_template(self):
        if self.player.round_number == Constants.num_rounds:
            if self.player.plays:
                return {'last_round':'plays'}
            else:
                return {'last_round': 'doesnt'}
        else:
            return {'last_round':'false'}


class ControlQuestions(Page):

    form_model = 'player'

    def get_form_fields(self):
        if self.player.treatment=='exclude':
            return ['control_tries','control1','control2','control3a','control3b', 'control3c', 'control3d', 'control4', 'control6' ,'control7exclude','control8']
        elif self.player.treatment == 'excludemany':
            return ['control_tries', 'control1', 'control2', 'control3a', 'control3b', 'control3c', 'control3d',
                    'control4m', 'control5', 'control6', 'control7exclude', 'control8']
        elif self.player.treatment=='control':
            return ['control_tries','control1', 'control2' , 'control3a','control3b','control3c','control7control', 'control8']

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
        # Function specificly for updating payoff after the public good game
        self.group.set_round_payoffs()

    def is_displayed(self):
        if self.player.treatment == 'FF':
            return False
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        else:
            return True


class ResultsPG(Page):

    def vars_for_template(self):
        data = {'round_number':self.player.round_number - 1 , 'left_on_account': Constants.endowment - self.player.contribution}
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

    form_model = models.Player

    def get_form_fields(self):
        if self.player.treatment == 'exclude' or self.player.treatment == 'feedback' or self.player.treatment == 'excludemany':
            return ['vote_A', 'vote_B', 'vote_C', 'vote_D', 'vote_E', 'exclude_none']
        elif self.player.treatment == 'include':
            return ['vote_A', 'vote_B','vote_C','vote_D','vote_E']


    #TODO: Be cautious, if the initial values of the vote_X are changed
    def error_message(self, values):
        vote_count = sum([values['vote_A'], values['vote_B'], values['vote_C'], values['vote_D'],values['vote_E']])
        if self.player.treatment == 'exclude':
            if vote_count > 0 and values['exclude_none'] == True:
                return 'Sie können nicht für keinen und einen Teilnehmer abstimmen.'
            # Enforce the player to choose an option
            if vote_count == 0 and values['exclude_none'] == False:
                return 'Bitte stimmen Sie ab.'
            # Enforce that the player can only vote for one other player
            if vote_count > 1:
                return 'Sie können nur für einen Teilnehmer abstimmen.'
        elif self.player.treatment == 'excludemany':
            if vote_count > 0 and values['exclude_none'] == True:
                return 'Sie können nicht für keinen und einen Teilnehmer abstimmen.'
            # Enforce the player to choose an option
            if vote_count == 0 and values['exclude_none'] == False:
                return 'Bitte stimmen Sie ab.'
        elif self.player.treatment == 'include':
            if vote_count == 0:
                return 'Bitte treffen Sie eine Wahl.'




    def vars_for_template(self):
        data = {'round_number': self.player.round_number-1}
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

        ##Note the round payoff was updated here in regard to cost of voting. I shift this to overall payoff calculation at the end

    def is_displayed(self):
        if self.player.treatment == 'FF' or self.player.treatment == 'control':
            return False
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        else:
            return True


class VoteResults(Page):

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


# Willingness to pay for bonus Family Feud Round
# Determines if the player plays the Bonus Family Feud round
# player.plays_in round(11 /last round is set) this is after Experiment round 10 (or last experiment round)!
# Also, player.plays_bonusFF is set, but this is only done for convenience player.in_round(11).plays would be sufficient
class ValuateFFSelect(Page):

    form_model = models.Player
    form_fields = ['ff_valuation']

    def vars_for_template(self):
        return {'time':Constants.questions_per_round * Constants.secs_per_question}

    def is_displayed(self):
        if self.player.treatment == "FF":
            return False
        if self.round_number == 1:
            return True
        else:
            return False

    def before_next_page(self):
        ## FF valuation here
        ## determine if the player is allowed to play FF one last time or if he has to watch the screen
        ## depending on his ff_valuation
        self.player.random_ff_valuation = random.choice(range(600))/100

        if self.player.random_ff_valuation > float(self.player.ff_valuation):
            self.player.plays_bonusFF = False
            # Actually this would be enough
            self.player.in_round(Constants.num_rounds).plays = False


class WaitAfterValuateFFSelect(WaitPage):

    def is_displayed(self):
        if self.player.treatment=="FF":
            return False
        if self.round_number == 1:
            return True
        else:
            return False

    wait_for_all_groups = True


class ValuateFFResult(Page):

    timeout_seconds = 10
    timer_text = "Sie werden weitergeleitet in "

    def is_displayed(self):
        if self.player.treatment=="FF":
            return False
        if self.round_number == 1:
            return True
        else:
            return False



class BeforeFamilyFeudWaitPage(WaitPage):
    wait_for_all_groups = True


class FamilyFeud(Page):
    pass

# Defo need this because the results are displayed over all groups
class AfterFamilyFeudWaitPage(WaitPage):
    wait_for_all_groups = True



class FamilyFeudResults(Page):

    #timeout_seconds = 30
    #timer_text = "Verbleibende Zeit auf dieser Seite "

    # Don't display in the valuation round (last round) and practice round (first round)
    # Don't show to players which did not play the game
    def is_displayed(self):
        if self.player.plays == False:
            return False
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
        if self.player.treatment == 'exclude' or self.player.treatment == 'excludemany':
            return ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7','q8','q9','q10']
        elif self.player.treatment == 'control':
            return ['q1','q2','q5','q6','q7','q8','q9','q10']

    def is_displayed(self):
        if self.player.treatment == "FF":
            return False
        else:    
            return Constants.num_rounds == self.round_number


# Do payoff calculation here
class AfterQuestionnaireWaitPage(WaitPage):

    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def after_all_players_arrive(self):

        for player in self.group.get_players():
            # Select a round from the 10 playing rounds (e.g. cut off the practice round and the bonusFF round)
            if Constants.num_rounds > 3:
                ## Note: Payround is the oTree round not the experiment round!
                payround = random.choice(range(2, Constants.num_rounds, 1))
                player.payround = payround #is accessed at showpayoffdetails
                player.payoff = player.in_round(payround).round_payoff - player.in_round(payround).ivoted * Constants.cost_for_vote
            else:
                payround = 2
                player.payround = payround
                player.payoff = player.in_round(payround).round_payoff - player.in_round(payround).ivoted * Constants.cost_for_vote

            # If player plays the bonus FF round then subtract the computer number from the players payoff
            # Note: the computer number is in Euro, but oTree expects points because it later converts Points to Euro in the Admin-Mak
            # Therefore, the computer number has to be converted to Points by 1/c/p
            # Note: the in_round(1) because this variable is set in round 1 only
            if player.in_round(1).plays_bonusFF:
                player.payoff = player.payoff - (1 /float(self.session.config['real_world_currency_per_point']) * float(player.in_round(1).random_ff_valuation))



# Use to display the payoff informations to the player
# Payoff calculation has been done (in After Questionnaire) if players arrive here
# class ShowPayoffDetails(Page):
class ShowPayoffDetails(Page):

    #timeout_seconds = Constants.timeoutsecs
    #timer_text = "Verbleibende Zeit auf dieser Seite "

    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        random_ff_valuation = self.player.in_round(1).random_ff_valuation
        ff_valuation = float(self.player.in_round(1).ff_valuation)
        #you have to do this here again because in player.payoff the valuation casts are already subtracted; also for debugging purpose
        taler = self.player.in_round(self.player.payround).round_payoff - self.player.in_round(self.player.payround).ivoted * Constants.cost_for_vote
        part_fee = self.session.config['participation_fee']

        # If the player did play the bonus round of FF then the random_ff_valuation will be subtracted
        # Here we show him this in the 2nd last page of the experiment
        # You cannot just use the payoff because we want to show the player the different elements that determine the overall payoff
        if random_ff_valuation < ff_valuation:
            return{'payoff_in_payround_taler':taler ,
                    'euro': '{0:.2f}'.format(round(taler * self.session.config['real_world_currency_per_point'],2)),
                    'part_fee':part_fee,
                    'diff': self.player.in_round(1).random_ff_valuation, # Will be subtracted if he played bonus FF
                    'all': round(part_fee + float(self.player.payoff) * self.session.config['real_world_currency_per_point'],2), # Note you have to calc this because self.payoff does not regard the participation fee
                   'payround': self.player.payround-1,
                   'number': self.player.participant.label}
        else:
            return {'payoff_in_payround_taler': taler,
                    'euro': '{0:.2f}'.format(round(taler * self.session.config['real_world_currency_per_point'],2)),
                    'part_fee': part_fee,
                    'diff': 0,
                    'all':round(part_fee + float(self.player.payoff) * self.session.config['real_world_currency_per_point'],2),
                    'payround':self.player.payround-1,
                    'number': self.player.participant.label}


class EndPage(Page):
    def is_displayed(self):
        if self.player.round_number == Constants.num_rounds:
            return True
        else:
            return False

    def vars_for_template(self):
        return {'number':self.player.participant.label}



page_sequence = [
    #Instructions,
    #ControlQuestions, #After this page there will be the FamilyFeud page and this has a group waitpage before
    Contribution,
    FirstWaitPage,
    ResultsPG,
    Vote,
    VoteWaitPage,
    VoteResults,
    #BeforeFamilyFeudWaitPage,
    #FamilyFeud,
    #ValuateFFSelect,
    #WaitAfterValuateFFSelect,  #I think, we don't need this
    #ValuateFFResult,
    #AfterFamilyFeudWaitPage,
    #FamilyFeudResults,
    #RateYourExperience,
    #Questionnaire,
    AfterQuestionnaireWaitPage, #Payoff calculation is done here
    ShowPayoffDetails,
    EndPage,
]
