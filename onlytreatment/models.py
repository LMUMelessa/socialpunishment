from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

from otree_redwood.models import Group as RedwoodGroup
import csv,random
import difflib as dif
import codecs

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'onlytreatment'
    players_per_group = 5

    # Public good rounds
    pgg_rounds = 1   #10 in the real experiment. Set 1 for testing
    # Guessing game (family feud) rounds
    # !!Note: even if valuation is off set ff_rounds to 1 + rounds + 1. If valuation is off, the last round is the questionnaire2 round
    ff_rounds = 3 #12 in the real experiment (if you want 10). Set 3 for testing.


    # this is the round number of the round where the BeliefQuestions/WaitPhase/Practice Round of Family feud takes place
    transition_round = pgg_rounds + 1
    first_ff_round = transition_round + 1 # note: the first family feud question is actually played in the transition_round (ff testround)
    num_rounds = pgg_rounds + ff_rounds

    # pg - vars
    endowment = 10
    multiplier = 2
    timeoutsecs = 60

    #Transition round breakpoint code
    break_code = 5454

    ### Familyfeud
    ### The overall time for one FF round is questions_per_round * secs_per_questions
    ### The players will receive new questions until: overall time is up  OR all questions_per_round + extra_questions are answered

    questions_per_round = 2  # 2 in the real experiment
    extra_questions = 1  # 1 in the real experiment
    secs_per_question = 30  # 30 in the real experiment
    wait_between_question = 4  # 4 in the real experiment

    with codecs.open('data.csv', 'r', 'utf-8') as f:
        questions = list(csv.reader(f))


        # Questions come as a list and will be formatted in a list of dics in creating session
        # Example format how to deal with questions in the code:
        # (The respective first answer is the desired answer, which will be displayed)
        # quizload = [
        #             {'question':"Name a Place You Visit Where You Aren't Allowed to Touch Anything",
        #                's1': ["Museum gallery",'Museum', 'Gallery', 'Museum gallery'],
        #                's2': ['Zoo', 'Animal'],
        #                's3': ["Gentleman's club", 'Gentleman club', 'Stripclub', 'Strip club'],
        #                's4': ['Baseball'],
        #                's5': ['China shop']},  {...}, ...
        #              ]



class Subsession(BaseSubsession):

    def define_label(self):
        germanlabellist = ['Teilnehmer A', 'Teilnehmer B', 'Teilnehmer C' , 'Teilnehmer D' , 'Teilnehmer E']
        labellist = ['Player A', 'Player B', 'Player C', 'Player D', 'Player E']
        for group in self.get_group_matrix():
            for player in group:
                player.playerlabel = labellist[player.id_in_group-1]
                player.germanplayerlabel = germanlabellist[player.id_in_group-1]

    def creating_session(self):
        # Assign treatment
        for player in self.get_players():
            #TODO Note: setting treatment is actually not needed but I do it s. t. in the dataset they have an indicator about this being the extra app only treatment
            player.treatment = self.session.config['treatment']
           # player.participant.label = str(self.get_players().index(player)) # use this is if you don't use a participant label file

        self.group_randomly()
        # Assign the labels
        self.define_label()


        ### Family feud
        if self.round_number == 1:

            quizload = []
            # Format question data into quizload
            for question in Constants.questions:
                quizload.append({'question': question[0],
                                 's1': question[1].split('*'),
                                 's2': question[2].split('*'),
                                 's3': question[3].split('*'),
                                 's4': question[4].split('*'),
                                 's5': question[5].split('*'), })

            questions_per_round = Constants.questions_per_round
            extra_questions = Constants.extra_questions

            for round_num in range(Constants.transition_round, Constants.num_rounds + 1):
                for question_num in range(1, questions_per_round + extra_questions + 1):

                    question = quizload[0]
                    #use this for random questions
                    #question = random.choice(quizload)
                    quizload.remove(question)
                    # Save the quizload of the question in session.vars to access later
                    # ql_11 e.g. means quizload for round 1 question 1
                    self.session.vars['ql_' + str(round_num) + str(question_num)] = question

    # don't delete this!
    def vars_for_admin_report(self):
        pass


class Group(RedwoodGroup):
    ### Public good game
    all_play = models.BooleanField(
        doc='Boolean. Defines if all player play the social arena game in a round.')

    total_cont = models.IntegerField(
        doc='The overall contribution of the group in the public good game.')

    indiv_share = models.IntegerField(
        doc='The share the players get after the public good game.')

    # Is needed so that we can display on any template the excluded player
    excluded_player = models.CharField(
        doc='The player, who is excluded from the social game.')

    # round_payoffs for pg game; function also sets total_cont and indiv_share
    def set_round_payoffs(self):
        self.total_cont = sum([p.contribution for p in self.get_players()])
        # the rounding ensures that 10.8 is 11 and not 10 as indiv_share is an integerField
        self.indiv_share = round((self.total_cont * Constants.multiplier) / Constants.players_per_group)
        for p in self.get_players():
            p.round_payoff = (Constants.endowment - p.contribution) + self.indiv_share



  ### family feud ###
    current_quest_num = models.IntegerField()
    s1_answered = models.BooleanField()
    s2_answered = models.BooleanField()
    s3_answered = models.BooleanField()
    s4_answered = models.BooleanField()
    s5_answered = models.BooleanField()
    group_ff_points = models.IntegerField(initial=0)
    question_sequence = models.CharField(initial='')

    def when_all_players_ready(self):
        # initialize the current question to question number 1 when a new family feud round starts
        self.current_quest_num = 0

        # send the whole quiz package (one question) to the channel
        self.sendquizload_toplayers()
        return

    # this will triger 'receive_question ()' function in javascript and in javascript the timers will be initialized
    # the function is called at the beginning from when_all_players_ready and under multiple questions when requested from a player through questionChannel
    def sendquizload_toplayers(self):

        # increment the current question number
        # TODO: You need save() for all database operations ingame, otherwise the changes have no effect on the database
        # TODO: see the oTree Redwood doc group.save()
        self.current_quest_num += 1
        self.save()

        # send the correct question to javascript, see the formatting in creating_session
        self.send('questionChannel', self.session.vars['ql_' + str(self.round_number) + str(self.current_quest_num)])

        ## update the question sequence, to have the question in the database
        # string sentence of the question
        question = self.session.vars['ql_' + str(self.round_number) + str(self.current_quest_num)]['question']
        #self.question_sequence = self.question_sequence + str(self.current_quest_num) + ':' + question + ';'
        #self.save()

        # at the beginning of every new question round, no solution has been found
        self.s1_answered = False
        self.save()
        self.s2_answered = False
        self.save()
        self.s3_answered = False
        self.save()
        self.s4_answered = False
        self.save()
        self.s5_answered = False
        self.save()


    # if multiple questions in a round this will be triggered from each first player in the group by the channel; e. g. the player requests a new question

    def _on_questionChannel_event(self, event=None):
        # send a new question back
        self.sendquizload_toplayers()


    # reveives all the guesses of the players, decides if guess was right and shall calculate ff_points
    # also checks if a correct guess has been found already, so no ff_points are distributed
    # sends processed information back to the players in javascript
    def _on_guessingChannel_event(self, event=None):
        # the guess of the player
        guess = event.value['guess'].lower()
        # id of the guessing player
        player_id_in_group = event.value['id']

        # player object of the guessing player
        player = self.get_player_by_id(player_id_in_group)

        player.inc_num_guesses()

        #curr quest num
        current_quest_num = self.current_quest_num

        # the current question quizload (dictionaire)
        question = self.session.vars['ql_' + str(self.round_number) + str(current_quest_num)]

        questionText = question['question']
        groupId = player.group.id_in_subsession


        # update the guess sequence of the player
        #player.guess_sequence = player.guess_sequence + str(self.current_quest_num) + ':' + str(guess) + ';'
        #player.save()

        good_guess = False
        questionindex = 0
        # check if the guess is correct, if yes and not answered correctly before, send respective information back to javascript
        for answernum in ['s1', 's2', 's3', 's4', 's5']:
            # e. g. question[s1] is a list with all the solutions for the correct word 1 of the current question
            if guess in list(map(lambda x: x.lower(), question[answernum])):  # guess is correct
                good_guess = True

            # if the guess was not in the answerlist, check for string similarity
            if good_guess == False:
                for answer in question[answernum]:
                    match = dif.SequenceMatcher(a=guess, b=answer.lower())
                    ##print(guess + " and " + answer.lower() + " have string equality of: " + str(match.ratio()))
                    if match.ratio() > 0.75:
                        good_guess = True

            if good_guess == True:
                # only take action and distribute ff_points if the correct answer has not been guessed before
                if [self.s1_answered, self.s2_answered, self.s3_answered, self.s4_answered, self.s5_answered][questionindex] != True:
                    # give the player a point (save() is called in the function)
                    player.inc_ff_points()

                    # give the group a point
                    self.group_ff_points += 1
                    self.save()

                    # update, so that the question cannot be answered again
                    if questionindex == 0:
                        self.s1_answered = True
                        self.save()
                    elif questionindex == 1:
                        self.s2_answered = True
                        self.save()
                    elif questionindex == 2:
                        self.s3_answered = True
                        self.save()
                    elif questionindex == 3:
                        self.s4_answered = True
                        self.save()
                    elif questionindex == 4:
                        self.s5_answered = True
                        self.save()

                    # determine, if now all possible answers have been found
                    finished = all(
                        [self.s1_answered, self.s2_answered, self.s3_answered, self.s4_answered, self.s5_answered])

                    # send informations back to javascript, this activates 'instructions_after_guess()'
                    self.send('guessInformations', {
                                                    'participant.code': player.participant.code,
                                                    'session.code':player.subsession.session.code,
                                                    'subsession.round_number':player.subsession.round_number,
                                                    'guess': question[answernum][0], # send the exactly correct answer back, which is the 0 element of the list
                                                    'whichword': answernum,
                                                    'idInGroup': player_id_in_group,
                                                    'correct': True,
                                                    'finished': finished,
                                                    'groupId': groupId,
                                                    'questionText':questionText,
                                                    'questionNumber': current_quest_num })

                    #print('thats finished' + str(finished))

                # TODO: note: with that design choice, if a question is answered correctly for the second time, nothing happens
                # TODO: there will be also nothing displayed in the group guess message board
                # guess was correct, but that correct guess was already made before
                else:
                    pass
                # break because no other answer has to be checked if the guess is correct
                break
            questionindex += 1

        # guess was not correct, send respective informations back
        if good_guess == False:
            self.send('guessInformations', { 'participant.code': player.participant.code,
                                             'session.code':player.subsession.session.code,
                                             'subsession.round_number':player.subsession.round_number,
                                             'guess': guess,
                                             'idInGroup': player_id_in_group,
                                             'correct': False,
                                             'groupId': groupId,
                                             'questionText': questionText,
                                             'questionNumber': current_quest_num})


    # TODO can you just leave out the period length function?
    def period_length(self):
        # take overall time * 10 so that oTree redwood, cannot abort the game, page submission is done in javascript
        # the reason is that, with multible rounds the overall time taken for the family feud game might not been exactly the same
        return (
               (Constants.questions_per_round) * ((Constants.secs_per_question + Constants.wait_between_question))) * 10


    #### Family feud end
    ######################################################################################################################






class Player(BasePlayer):

    ### Public Good Variables
    germanplayerlabel = models.StringField(doc="See player label.")

    playerlabel = models.CharField(
        doc='The player name. Player A - Player E',
        choices=['Player A', 'Player B', 'Player C', 'Player D', 'Player E'])

    contribution = models.IntegerField(
        doc='The players contribution in the public good game in Taler',
        verbose_name='Ihr Betrag',
        min=0,
        max=Constants.endowment)

    plays = models.BooleanField(
        doc='Determines if the player is allowed to play the guessing game in a particular round.',
        default=True
    )
    #TODO: this app is entirely 'only' treatment. But keep this s. t. there is an indicator in the database
    treatment = models.CharField(
        doc='Defines the treatment of the session. The treatment is the same for all players in one session')

    round_payoff = models.IntegerField(initial=0, doc="The amount of Taler of the player in a particular round.")

    #### Breakpoint in Transission round
    breakpoint = models.IntegerField(blank=False, doc='Breakpoint', verbose_name  = "")


    ######################################################################################################################
    ### Control Variables

    ##how often did the participant try to submit the control questions when some answers were still wrong
    # if the participant was correct on the first try, than this will be 1
    control_tries = models.IntegerField(initial=0, doc="How often did the player try to submit the control questions page when answers were still wrong. \
                                                          1 if the player had everything correct on the first try.")

    # only + nosanction + exlude + dislike + punish
    control1 = models.IntegerField(
        verbose_name="Wie viele Taler haben Sie auf Ihrem privaten Konto, wenn Sie 3 Taler auf das Gruppenkonto einzahlen?",
        min=0)

    # only + nosanction + exlude + dislike + punish
    control2 = models.IntegerField(
        verbose_name="20 Taler wurden insgesamt in das Gruppenkonto eingezahlt. Wie viele Taler erhalten Sie am Ende aus dem Gruppenkonto?",
        min=0)

    # only + nosanction + exlude + dislike + punish
    control3a = models.StringField(widget=widgets.RadioSelect(),
                                   verbose_name="Es kann sein, dass verschiedene Gruppenmitglieder unterschiedlich viele Taler aus dem Gruppenkonto erhalten.",
                                   choices=["wahr", "falsch"])

    # only + nosanction + exlude + dislike + punish
    control3b = models.StringField(widget=widgets.RadioSelect(),
                                   verbose_name="Am Ende der ersten Stufe einer jeweiligen Runde wissen Sie, wie viel jedes Gruppenmitglied ins Gruppenkonto eingezahlt hat.",
                                   choices=["wahr", "falsch"])

    # only + nosanction + exlude + dislike + punish
    control3c = models.StringField(widget=widgets.RadioSelect(),
                                   verbose_name="Sie spielen in jeder Runde in einer neuen Gruppe mit anderen Personen",
                                   choices=["wahr", "falsch"])


    ####################################################################################################################
    ###  Questionnaire1
    q1 = models.IntegerField(verbose_name="Was denken Sie, wie viele Taler sollte man zum Gruppenkonto beitragen?", min=0 , max=10)
    q2 = models.StringField(widget=widgets.RadioSelect(),verbose_name="Denken Sie, die meisten anderen sehen das auch wie Sie?", choices=["Ja",
                                                                                                             "Ich bin mir unsicher",
                                                                                                             "Nein, die meisten anderen denken man sollte mehr beitragen",
                                                                                                             "Nein, die meisten anderen denken man sollte weniger beitragen",
                                                                                                             ])
    ####################################################################################################################
    ###  Questionnaire2
    q5 = models.IntegerField(verbose_name="Bitte geben Sie Ihr Alter an", min=0, max=99)
    q7 = models.StringField(verbose_name="Bitte geben Sie Ihr Studienfach an")
    q8 = models.IntegerField(min=0,
                             verbose_name="Wie oft haben Sie bereits an einer ökonomischen Laborstudie teilgenommen (auch außerhalb dieses Labors)?")
    q9 = models.StringField(
        verbose_name="Wie viele Teilnehmerinnen oder Teilnehmer in diesem Raum haben Sie schon vor dem Experiment gekannt?")
    q10 = models.StringField(verbose_name="Möchten Sie uns noch etwas mitteilen? Hier ist die Gelegenheit dazu!",
                             blank=True)



    ####################################################################################################################

    payround = models.IntegerField(
        doc="The round number that will be payed out for the player. Note: this is an oTree round e. g. experiment_round+1.")


    ####################################################################################################################
    ### FamilyFeud
    # does the player play the bonus FF round after all rounds of the experiment according to the evaluation mechanism
    # depends on the valuationFF results
    plays_bonusFF = models.BooleanField(initial=True,
                                        doc="This determines if the player plays the bonus guessing game round at the end of the experiment. \
                                                This is true if the players willingness to pay (ff_valuation) is higher than the computer (number random_ff_valuation)")

    plays = models.BooleanField(
        doc='Determines if the player is allowed to play the guessing game in a particular round.',
        default=True
    )

    # the willingness to pay for the bonus family feud round
    ff_valuation = models.DecimalField(
        verbose_name="Bitte klicken Sie auf die Skala, um Ihre Zahlungsbereitschaft auszuwählen.",
        widget=widgets.Slider(show_value=False),
        min=0, max=6,
        decimal_places=1,
        max_digits=2,
        doc="The players' willingness to pay for the bonus round of the guessing game.",
        initial=0)

    random_ff_valuation = models.FloatField(
        doc="The computer number which will be to compared with ff_valuation to determine if the player plays the bonus round.",
        initial=0.0)

    # Number of correctly answered questions
    ff_points = models.IntegerField(initial=0,
                                    doc="The number of correct answers which the player found overall in the guessing game in one round.")


    # Number of tries (guesses) of a player
    num_guesses = models.IntegerField(initial=0)

    def inc_num_guesses(self):
        self.num_guesses += 1
        self.save()

    def inc_ff_points(self):
        self.ff_points += 1
        self.save()

    def initial_decision(self):
        return 0.5
