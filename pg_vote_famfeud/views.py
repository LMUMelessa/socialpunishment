from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import random
from otree_redwood.models import Event
import codecs
import csv
import time
import datetime
from django.http import HttpResponse


class Instructions(Page):
    def is_displayed(self):
        if self.player.treatment == 'FF':
            return False
        else:
            return self.player.round_number == 1



# monitors information before a round depending on the current state of the experiment and treatment
# distinct from Instructions to allow for differnt types of timeouts
# don't show in only treatment in round 1 because there is no FF test
class InfosBeforeRound(Page):
    timeout_seconds = 30
    timer_text = "Sie werden weitergeleitet"

    def vars_for_template(self):
        return {'valuation': self.session.config['valuation']}

    def is_displayed(self):
        # don't show in only treatment in round 1 because there is no FF test round, e. g. it directly would appear again in beginning of oTree round 2
        if (self.player.treatment == 'only' and self.round_number == 1):
            return False
        elif self.player.treatment == 'FF':
            return False
        else:
            return True

class ControlQuestions(Page):

    form_model = 'player'

    def get_form_fields(self):
        if self.player.treatment=='exclude':
            return ['control_tries','control1','control2','control3a','control3b', 'control3c', 'control3d', 'control4','control5', 'control6' ,'control7exclude','control8']
        elif self.player.treatment=='only':
            return ['control_tries','control1', 'control2' , 'control3a','control3b','control3c']
        elif self.player.treatment=='nosanction':
            return ['control_tries','control1', 'control2' , 'control3a','control3b','control3c','control7control', 'control8']
        elif self.player.treatment=='dislike':
            return ['control_tries','control1', 'control2' , 'control3a','control3b','control3c','control7control', 'control8']
        elif self.player.treatment=='punish':
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

# wait_for_all_groups= True in FirstWaitPage results in error because you reference group there
class SecondWaitPage(WaitPage):
    wait_for_all_groups = True


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
        if self.player.treatment == 'exclude':
            return ['vote_A', 'vote_B', 'vote_C', 'vote_D', 'vote_E', 'exclude_none']
        if self.player.treatment == 'dislike':
            return ['vote_A', 'vote_B', 'vote_C', 'vote_D', 'vote_E', 'exclude_none']
        if self.player.treatment == 'punish':
            return ['vote_A', 'vote_B', 'vote_C', 'vote_D', 'vote_E', 'exclude_none']


    def error_message(self, values):
        vote_count = sum([values['vote_A'], values['vote_B'], values['vote_C'], values['vote_D'],values['vote_E']])
        if vote_count > 0 and values['exclude_none'] == True:
            return 'Sie können nicht für keinen und einen Teilnehmer abstimmen'
        if vote_count == 0 and values['exclude_none'] == False:
            return 'Bitte treffen Sie zuerst eine Entscheidung.'

    def vars_for_template(self):
        data = {'round_number': self.player.round_number-1}
        for player in self.group.get_players():
            # Remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ', '')] = player.contribution
        return data

    def is_displayed(self):
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        if self.player.treatment == "FF" or self.player.treatment == "nosanction" or self.player.treatment == "only":
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

        ##Note the round payoff was updated here in regard to cost of voting. I shifted this to overall payoff calculation at the end

    def is_displayed(self):
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        if self.player.treatment == "FF" or self.player.treatment == "nosanction" or self.player.treatment == "only":
            return False
        else:
            return True


#wait_for_all_groups = True in VoteWaitPage would result in error because after_all_player_arrive is then only called once
class VoteWaitPage2(WaitPage):
    wait_for_all_groups = True

    def is_displayed(self):
        if self.round_number == 1 or self.round_number == Constants.num_rounds:
            return False
        if self.player.treatment == "FF" or self.player.treatment == "nosanction" or self.player.treatment == "only":
            return False
        else:
            return True


class VoteResults(Page):

   def vars_for_template(self):
       data = {'round_number':self.player.round_number-1}
       for player in self.group.get_players():
           data[(player.playerlabel).replace(' ', '') + '_votes'] = player.myvotes

           if player.treatment == 'exclude':
               if player.plays == True:
                    data[(player.playerlabel).replace(' ', '') + '_plays'] = "Ja"
               elif player.plays == False:
                   data[(player.playerlabel).replace(' ', '') + '_plays'] = "Nein"
           else: #in other treatments all play GG, show the sanctioning
               if player.sanctioned == True:
                   data[(player.playerlabel).replace(' ', '') + '_sanctioned'] = "Ja"
               else:
                   data[(player.playerlabel).replace(' ', '') + '_sanctioned'] = "Nein"

       return data

   def is_displayed(self):
       if self.round_number == 1 or self.round_number == Constants.num_rounds:
           return False
       if self.player.treatment == 'FF' or self.player.treatment == 'nosanction' or self.player.treatment == 'only':
           return False
       else:
           return True


#the following two sites are needed to not surprise participant with the FF game
# the might have waited for a long time on the BeforeFamilyFeud Wait page, waiting for all the other gruoups and then the game suddenly starts
# so we tell them here again
class BeforePrepareFFWaitPage(WaitPage):
    wait_for_all_groups = True

    def is_displayed(self):
        if self.player.treatment=="only":
            return False
        # if valuation is off and you are in the last round (questionnaire round) then you must not show
        elif self.round_number == Constants.num_rounds and self.session.config['valuation']=='off':
            return False
        else: return True


# show nothing just the timout message and timout hard after 5 seconds
class PrepareFF(Page):

    timeout_seconds = 5
    timer_text = "Das Gruppenspiel startet in "

    def is_displayed(self):
        if self.player.treatment=="only":
            return False
        # if valuation is off and you are in the last round (questionnaire round) then you must not show
        elif self.round_number == Constants.num_rounds and self.session.config['valuation']=='off':
            return False
        else: return True


class FamilyFeud(Page):
    def is_displayed(self):
        if self.player.treatment=="only":
            return False
        # if valuation is off and you are in the last round (questionnaire round) then you must not show
        elif self.round_number == Constants.num_rounds and self.session.config['valuation']=='off':
            return False
        else: return True


# Defo need this because the results are displayed over all groups
class AfterFamilyFeudWaitPage(WaitPage):
    wait_for_all_groups = True
    def is_displayed(self):
        if self.player.treatment == "only":
            return False
        else: return True


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
        if self.player.treatment == "FF" or self.player.treatment == "only":
            return False
        if self.session.config["valuation"] == "off":
            return False
        if self.round_number == 1:
            return True
        else:
            return False

    def before_next_page(self):
        ## FF valuation here
        ## determine if the player is allowed to play FF one last time or if he has to watch the screen
        ## depending on his ff_valuation
        self.player.random_ff_valuation = random.choice(range(60))/10

        if self.player.random_ff_valuation > float(self.player.ff_valuation):
            self.player.plays_bonusFF = False
            # Actually this would be enough
            self.player.in_round(Constants.num_rounds).plays = False


class WaitAfterValuateFFSelect(WaitPage):

    def is_displayed(self):
        if self.player.treatment=="FF" or self.player.treatment == "only":
            return False
        if self.session.config["valuation"] == "off":
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
        if self.player.treatment=="FF" or self.player.treatment=="only":
            return False
        if self.session.config["valuation"] == "off":
            return False
        if self.round_number == 1:
            return True
        else:
            return False


class FamilyFeudResults(Page):

    #timeout_seconds = 30
    #timer_text = "Verbleibende Zeit auf dieser Seite "

    # Don't display in the valuation round (last round) and practice round (first round)
    # Don't show to players which did not play the game
    def is_displayed(self):
        if self.player.plays == False or self.player.treatment=="only":
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
               # this can be used to show more detailed information
               # corresponds to alternative FFResultsPage (see some older git version)
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

        # data_dic['alist'] has structure [[GroupID, GroupFFpoints, {'player_label': .. }],..]
        # order these lists by the groupFFpoints
        data_dic['alist'].sort(key=lambda _helplist: _helplist[1], reverse=True)
        return data_dic


class Questionnaire(Page):
    form_model = 'player'
    def get_form_fields(self):
        if self.player.treatment == 'exclude':
            return ['q1', 'q2', 'q3', 'q4', 'q5', 'q7','q8','q9','q10']
        else:
            return ['q1','q2','q5','q7','q8','q9','q10']
    def is_displayed(self):
        if self.player.treatment == "FF":
            return False
        else:    
            return Constants.num_rounds == self.round_number


# Do payoff calculation here
class CalculatePayoffAfterQuestionnaireWaitPage(WaitPage):

    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def after_all_players_arrive(self):

        for player in self.group.get_players():
            # Select a round from the 10 playing rounds (e.g. cut off the practice round and the bonusFF round)
            if Constants.num_rounds > 3:
                ## Note: Payround is the oTree round not the experiment round!
                payround = random.choice(range(2, Constants.num_rounds, 1))
                player.payround = payround #is accessed at showpayoffdetails
                punish_costs = 0
                if player.treatment == 'punish':
                    if player.in_round(payround).sanctioned:
                        punish_costs = Constants.punishment_value
                player.payoff = player.in_round(payround).round_payoff - (player.in_round(payround).ivoted * Constants.cost_for_vote) - punish_costs
            else:
                payround = 2
                player.payround = payround
                punish_costs = 0
                if player.treatment == 'punish':
                    if player.in_round(payround).sanctioned:
                        punish_costs = Constants.punishment_value
                player.payoff = player.in_round(payround).round_payoff - (player.in_round(payround).ivoted * Constants.cost_for_vote) - punish_costs

            # If player plays the bonus FF round then subtract the computer number from the players payoff
            # Note: the computer number is in Euro, but oTree expects points because it later converts Points to Euro in the Admin-Mask
            # Therefore, the computer number has to be converted to Points by 1/c/p
            # Note: the in_round(1) because this variable is set in round 1 only
            if self.session.config["valuation"]=="on":
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
        #you have to do this here again because in player.payoff the valuation costs are already subtracted; also for debugging purpose
        punish_costs = 0
        if self.player.treatment == 'punish':
            if self.player.in_round(self.player.payround).sanctioned:
                punish_costs = Constants.punishment_value
        taler = self.player.in_round(self.player.payround).round_payoff - (self.player.in_round(self.player.payround).ivoted * Constants.cost_for_vote) - punish_costs
        part_fee = self.session.config['participation_fee']

        # If the player did play the bonus round of FF then the random_ff_valuation will be subtracted
        # Here we show him this in the 2nd last page of the experiment
        # You cannot just use the payoff because we want to show the player the different elements that determine the overall payoff
        #TODO: Note: if valuation=off in session.config, it is all fine! randomffvaluation and ffvaluation are both 0
        #TODO: ==> diff is 0 then also ==> in the template if diff=0 in ShowPayoffDetails the BonusFF round will not be mentioned.
        #TODO: This means it is sufficient to shut off valuation, nothing has to be changed in regard to display logic here or in the template
        if random_ff_valuation < ff_valuation:
            return{'payoff_in_payround_taler':taler ,
                    'euro': (round(c(taler).to_real_world_currency(self.session),2)),
                    'part_fee':part_fee,
                    'diff': self.player.in_round(1).random_ff_valuation, # Will be subtracted if he played bonus FF, this has happend in player.payoff already
                    'all': round(part_fee + float(self.player.payoff) * self.session.config['real_world_currency_per_point'],2), # Note you have to calc this because self.payoff does not regard the participation fee
                   'payround': self.player.payround-1,
                   'number': self.player.participant.label}
        else:
            return {'payoff_in_payround_taler': taler,
                    'euro':(round(c(taler).to_real_world_currency(self.session),2)),
                    'part_fee': part_fee,
                    'diff': 0,
                    'all':round(part_fee + float(self.player.payoff) * self.session.config['real_world_currency_per_point'],2),
                    'payround':self.player.payround-1,
                    'number': self.player.participant.label}


class EndPage(Page):

    def is_displayed(self):
        if self.player.treatment == "FF":
            return False
        if self.player.round_number == Constants.num_rounds:
            return True
        else:
            return False
    def vars_for_template(self):
        return {'number':self.player.participant.label}


# returns the http csv. file response for downloading the guessing game data
# it is essentially the download response if the download_guess data link is clicked in AdminReport
def downloadguess(request):
    date = str(datetime.datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y_at%H:%M'))
    response = HttpResponse(content_type='text/csv')
    # decide the file name
    response['Content-Disposition'] = 'attachment; filename="{}_guessdata.csv"'.format(date)
    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))
    writer.writerow(["participantID", "sessionID", "round_number", "guess", "correct", "groupId", "questionText", "question_number"])
    # 'Event' is the database table! E. g. database access here
    for event in Event.objects.all():
        if event.value.__class__ == dict:
            datadic = event.value
            if 'participant.code' in datadic.keys():
                writer.writerow([datadic['participant.code'], datadic['session.code'],datadic['subsession.round_number'],
                                 datadic['guess'], datadic['correct'], datadic['groupId'], datadic['questionText'], datadic['questionNumber']])
    return response

page_sequence = [
    Instructions,
    ControlQuestions, #After this page there will be the FamilyFeud page and this has a group waitpage before
    InfosBeforeRound,
    Contribution,
    FirstWaitPage,
    SecondWaitPage,
    ResultsPG,
    Vote,
    VoteWaitPage,
    VoteWaitPage2,
    VoteResults,
    BeforePrepareFFWaitPage,
    PrepareFF,
    FamilyFeud,
    ValuateFFSelect,
    WaitAfterValuateFFSelect,  #TODO: I think, we don't need this
    ValuateFFResult,
    AfterFamilyFeudWaitPage,
    FamilyFeudResults,
    Questionnaire,
    CalculatePayoffAfterQuestionnaireWaitPage, #Payoff calculation is done here
    ShowPayoffDetails,
    EndPage,
]
