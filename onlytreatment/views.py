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
        return self.player.round_number == 1


# monitors information before a round depending on the current state of the experiment and treatment
# distinct from Instructions to allow for different types of timeouts
# Different to the other app/treatments, here the public good game starts directly in the first round
class InfosBeforeRound(Page):
    timeout_seconds = 30
    timer_text = "Sie werden weitergeleitet"

    def vars_for_template(self):
        return {'valuation': self.session.config['valuation']}


class ControlQuestions(Page):
    form_model = 'player'
    def get_form_fields(self):
        # Todo Check this
        return ['control_tries','control1', 'control2' ,'control3a','control3b','control3c']
    def is_displayed(self):
        return self.round_number == 1


class WaitAfterControlQuestions(WaitPage):
    wait_for_all_groups = True


class Contribution(Page):
    form_model = models.Player
    form_fields = ['contribution']
    def vars_for_template(self):
        return {'round_number': self.player.round_number}
    def is_displayed(self):
        return self.round_number < Constants.transition_round


class FirstContributionWaitPage(WaitPage):
    def after_all_players_arrive(self):
        # Function specificly for updating payoff after the public good game
        self.group.set_round_payoffs()
    def is_displayed(self):
        return self.round_number < Constants.transition_round


# wait_for_all_groups= True in FirstWaitPage results in error because you reference group there
class SecondContributionWaitPage(WaitPage):
    wait_for_all_groups = True
    def is_displayed(self):
        return self.round_number < Constants.transition_round


class ResultsPG(Page):

    def vars_for_template(self):
        data = {'round_number':self.player.round_number, 'left_on_account': Constants.endowment - self.player.contribution}
        for player in self.group.get_players():
            # Remove whitespace from label so that it can be displayed in the template
            data[(player.playerlabel).replace(' ','')] = player.contribution
        return data

    def is_displayed(self):
       return self.round_number < Constants.transition_round


class Questionnaire1(Page):
    form_model = models.Player
    form_fields = ['q1','q2']
    def is_displayed(self):
        return self.round_number == Constants.transition_round


class Breakpoint(Page):
    form_model = models.Player
    form_fields = ['breakpoint']

    def error_message(self, values):
        # the Code is in models.py Constants class
        if values['breakpoint'] != Constants.break_code:
            return "Bitte warten Sie, bis sie den richtigen Code erhalten."

    def is_displayed(self):
        return self.round_number == Constants.transition_round


class BeforePrepareFFWaitPage(WaitPage):
    wait_for_all_groups = True
    def is_displayed(self):
        # if valuation is off and you are in the last round  (questionnaire round) then you must not show
        if self.round_number == Constants.num_rounds and self.session.config['valuation'] == 'off':
            return False
        elif self.round_number >= Constants.transition_round:
            return True
        else:
            return False


class PrepareFF(Page):

    timeout_seconds = 5
    timer_text = "Das Gruppenspiel startet in "

    def is_displayed(self):
        # if valuation is off and you are in the last round  (questionnaire round) then you must not show
        if self.round_number == Constants.num_rounds and self.session.config['valuation']=='off':
            return False
        elif self.round_number >= Constants.transition_round:
            return True
        else:
            return False


class FamilyFeud(Page):
    def is_displayed(self):
        # if valuation is off and you are in the last round  (questionnaire round) then you must not show
        if self.round_number == Constants.num_rounds and self.session.config['valuation'] == 'off':
            return False
        elif self.round_number >= Constants.transition_round:
            return True
        else:
            return False

# Defo need this because the results are displayed over all groups
class AfterFamilyFeudWaitPage(WaitPage):
    wait_for_all_groups = True
    def is_displayed(self):
        # if valuation is off and you are in the last round  (questionnaire round) then you must not show
        if self.round_number == Constants.num_rounds and self.session.config['valuation'] == 'off':
            return False
        elif self.round_number >= Constants.transition_round:
            return True
        else:
            return False


# Willingness to pay for bonus Family Feud Round
# Determines if the player plays the Bonus Family Feud round
# player.plays_in round(last round is set) is set
# Also, player.plays_bonusFF is set, but this is only done for convenience player.in_round(lastround).plays would be sufficient
class ValuateFFSelect(Page):

    form_model = models.Player
    form_fields = ['ff_valuation']

    def vars_for_template(self):
        return {'time':Constants.questions_per_round * Constants.secs_per_question}

    def is_displayed(self):
        if self.session.config["valuation"] == "off":
            return False
        elif self.round_number == Constants.transition_round:
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
            # Actually this would be enough but you use plays_bonusFF in the template so don't take that out
            self.player.in_round(Constants.num_rounds).plays = False


class WaitAfterValuateFFSelect(WaitPage):

    def is_displayed(self):
        if self.session.config["valuation"] == "off":
            return False
        elif self.round_number == Constants.transition_round:
            return True
        else:
            return False

    wait_for_all_groups = True


class ValuateFFResult(Page):

    timeout_seconds = 30
    timer_text = "Sie werden weitergeleitet in "

    def is_displayed(self):
        if self.session.config["valuation"] == "off":
            return False
        elif self.round_number == Constants.transition_round:
            return True
        else:
            return False


class FamilyFeudResults(Page):

    #timeout_seconds = 30
    #timer_text = "Verbleibende Zeit auf dieser Seite "

    # Don't display in the valuation round and practice round
    # Don't show to players which did not play the game
    def is_displayed(self):
        # don't show in practice round and last round (so, fine for valuation on or off because this only matters in last round)
        if self.round_number == Constants.num_rounds or self.player.round_number == Constants.transition_round:
            return False
        elif self.round_number > Constants.transition_round:
            return True
        else:
            return False

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


class Questionnaire2(Page):
    form_model = models.Player
    form_fields = ['q5','q7','q8','q9','q10']
    def is_displayed(self):
        return self.round_number == Constants.num_rounds


# Do payoff calculation here
class CalculatePayoffAfterQuestionnaireWaitPage(WaitPage):

    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def after_all_players_arrive(self):

        for player in self.group.get_players():
            # Select a round from the PGG rounds (different than in the treatments app)
            if Constants.num_rounds > 4: #4 in the testing scenario where there is only 1 pgg round
                ## Select one of the pgg rounds randomly
                payround = random.choice(range(1, Constants.pgg_rounds+1, 1))
                player.payround = payround #is accessed at showpayoffdetails
                player.payoff = player.in_round(payround).round_payoff
            # In testing
            else:
                payround = 1
                player.payround = payround
                player.payoff = player.in_round(payround).round_payoff

            # If player plays the bonus FF round then subtract the computer number from the players payoff
            # Note: the computer number is in Euro, but oTree expects points because it later converts Points to Euro in the Admin-Mask
            # Therefore, the computer number has to be converted to Points by 1/c/p
            # Note: the in_round(1) because this variable is set in round 1 only
            if self.session.config["valuation"]=="on":
                if player.in_round(Constants.transition_round).plays_bonusFF:
                    player.payoff = player.payoff - (1 /float(self.session.config['real_world_currency_per_point']) * float(player.in_round(Constants.transition_round).random_ff_valuation))


# Use to display the payoff informations to the player
# Payoff calculation has been done (in After Questionnaire) if players arrive here
# class ShowPayoffDetails(Page):
class ShowPayoffDetails(Page):

    #timeout_seconds = Constants.timeoutsecs
    #timer_text = "Verbleibende Zeit auf dieser Seite "

    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        random_ff_valuation = self.player.in_round(Constants.transition_round).random_ff_valuation
        ff_valuation = float(self.player.in_round(Constants.transition_round).ff_valuation)
        #you have to do this here again because in player.payoff the valuation costs are already subtracted; also for debugging purpose
        taler = self.player.in_round(self.player.payround).round_payoff
        part_fee = self.session.config['participation_fee']

        # If the player did play the bonus round of FF then the random_ff_valuation will be subtracted
        # Here we show him this in the 2nd last page of the experiment
        # You cannot just use the payoff because we want to show the player the different elements that determine the overall payoff
        #TODO: Note: if valuation=off in session.config, it is all fine! randomffvaluation and ffvaluation are both 0
        #TODO: ==> diff is 0 then also ==> in the template if diff=0 in ShowPayoffDetails the BonusFF round will not be mentioned.
        #TODO: This means it is sufficient to shut off valuation, nothing has to be changed in regard to display logic here or in the template
        if random_ff_valuation < ff_valuation:
            return{'payoff_in_payround_taler':taler ,
                    'euro': (round(c(taler).to_real_world_currency(self.session),1)),
                    'part_fee':part_fee,
                    'diff': self.player.in_round(Constants.transition_round).random_ff_valuation, # Will be subtracted if he played bonus FF, this has happend in player.payoff already
                    'all': round(part_fee + float(self.player.payoff) * self.session.config['real_world_currency_per_point'],1), # Note you have to calc this because self.payoff does not regard the participation fee
                   'payround': self.player.payround,
                   'number': self.player.participant.label}
        else:
            return {'payoff_in_payround_taler': taler,
                    'euro':(round(c(taler).to_real_world_currency(self.session),1)),
                    'part_fee': part_fee,
                    'diff': 0,
                    'all':round(part_fee + float(self.player.payoff) * self.session.config['real_world_currency_per_point'],1),
                    'payround':self.player.payround,
                    'number': self.player.participant.label}


class EndPage(Page):
    def is_displayed(self):
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
    ControlQuestions,
    WaitAfterControlQuestions,
    InfosBeforeRound,
    Contribution,
    FirstContributionWaitPage,
    SecondContributionWaitPage,
    ResultsPG,
    Questionnaire1,
    Breakpoint,
    BeforePrepareFFWaitPage,
    PrepareFF,
    AfterFamilyFeudWaitPage,
    FamilyFeud,
    ValuateFFSelect,
    WaitAfterValuateFFSelect,
    ValuateFFResult,
    FamilyFeudResults,
    Questionnaire2,
    CalculatePayoffAfterQuestionnaireWaitPage,
    ShowPayoffDetails,
    EndPage
]
