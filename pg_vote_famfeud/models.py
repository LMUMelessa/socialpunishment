from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from otree_redwood.models import Group as RedwoodGroup
import csv,random
import difflib as dif
import codecs

author = 'Natcoop'

doc = """
Public Good + Family Feud
"""


class Constants(BaseConstants):
    name_in_url = 'pg_vote_famfeud'
    players_per_group = 5
    num_rounds = 12 #never change to something smaller 3 #note: if you want to play 10 rounds of the experiment you need 12 here!
    #pg - vars
    endowment = 10
    multiplier = 2
    timeoutsecs = 60
    cost_for_vote = 0.5 #don't change this! It is hardcoded as 0.5(Taler) the ControlQuestions
    punishment_value = 1
    ### Familyfeud

    ### The overall time for one FF round is questions_per_round * secs_per_questions
    ### The players will receive new questions until: overall time is up  OR all questions_per_round + extra_questions are answered

    questions_per_round = 2 #2 in the real experiment
    extra_questions = 1 #1 in the real experiment
    secs_per_question = 30 #30 in the "
    wait_between_question = 4 #4 in the "


    with codecs.open('data.csv', 'r', 'latin-1') as f:
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
            player.treatment = self.session.config['treatment']
            player.city = self.session.config['city']
           # player.participant.label = str(self.get_players().index(player)) #outcomment when done via participant_label.txt file


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

            for round_num in range(1, Constants.num_rounds + 1):
                for question_num in range(1, questions_per_round + extra_questions + 1):

                    question = quizload[0]
                    #use this for random questions
                    #question = random.choice(quizload)
                    quizload.remove(question)
                    # Save the quizload of the question in session.vars to access later
                    # ql_11 e.g. means quizload for round 1 question 1
                    self.session.vars['ql_' + str(round_num) + str(question_num)] = question




class Group(RedwoodGroup):

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
        # TODO: see the oTree Redwood doc group.save() note changed spelling from Gruppe zu gruppe weil es sonst einen fehler gab
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
        # TODO, do i need all the saves or is 1 enough?
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

        # the current question quizload (dictionaire)
        question = self.session.vars['ql_' + str(self.round_number) + str(self.current_quest_num)]

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
                                                    'finished': finished})

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
                                             'correct': False})

    # TODO can you just leave out the period length function?
    def period_length(self):
        # take overall time * 10 so that oTree redwood, cannot abort the game, page submission is done in javascript
        # the reason is that, with multible rounds the overall time taken for the family feud game might not been exactly the same
        return (
               (Constants.questions_per_round) * ((Constants.secs_per_question + Constants.wait_between_question))) * 10


    #### Family feud end
    ######################################################################################################################

    ### Public good game
    all_play = models.BooleanField(
        doc= 'Boolean. Defines if all player play the social arena game in a round.')


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
        self.indiv_share = (self.total_cont * Constants.multiplier) / Constants.players_per_group
        for p in self.get_players():
            p.round_payoff = (Constants.endowment - p.contribution) + self.indiv_share


    # Assigns for all the players how many votes they had
    # The variable updated is player.myvotes
    # Note: votes have different meanings, this depends on the treatment
    def set_myvotes(self):
        # Set the votes a player received from the other players
        for set_player in self.get_players():
            vote_count = 0
            # Screen the invitations of all players
            for voter in self.get_players():
                votesdic = {'Player A': voter.vote_A,
                            'Player B': voter.vote_B,
                            'Player C': voter.vote_C,
                            'Player D': voter.vote_D,
                            'Player E': voter.vote_E}
                # Check if the voter did vote for the set_player
                if votesdic[set_player.playerlabel] == True:
                    vote_count += 1
            set_player.myvotes = vote_count

        # Set the votes a player distributed towards the other players (they impose costs)
        for player in self.get_players():
            player.ivoted = sum([player.vote_A, player.vote_B, player.vote_C, player.vote_D, player.vote_E])


    # New version of the function after 08.09.2018
    # Assign for all players if they play in the second game (social game, familyfeud)
    # Assign if the second game/social game/family feud will be played with all players in the group
    # Sets group.all_play and player.plays
    def set_social_game(self):
            for player in self.get_players():
                if player.myvotes >= 3:
                    player.sanctioned = True
                    if player.treatment == 'exclude':
                        player.plays = False


    # # Version of the function before 08.09.2018 - after that the exclusion mechanism changed, at least in exclusion treatment
    # # Find out if there is a majority after the voting
    # # Assign for all players if they play in the second game (social game, familyfeud)
    # # Assign if the second game/social game/family feud will be played with all players in the group
    # # Sets group.all_play and player.plays
    # def set_social_game(self):
    #     invitationslist = []
    #
    #     # Collect all the votes
    #     for player in self.get_players():
    #         invitationslist.append(player.myvotes)
    #
    #
    #     # Find the highest number of votes a player had
    #
    #     min_or_max = None
    #
    #     if self.get_players()[0].treatment == 'exclude' or self.get_players()[0].treatment == 'feedback' :
    #         min_or_max = max(invitationslist)
    #     elif self.get_players()[0].treatment == 'include':
    #         min_or_max = min(invitationslist)
    #
    #     # Check if max/min is unique, because in that case there is a majority
    #     occurence = invitationslist.count(min_or_max)
    #     # Unique max/min, there is a majority
    #     if occurence == 1:
    #         self.all_play = False
    #         # Identify the player with the most exclusions
    #         for player in self.get_players():
    #             if player.myvotes == min_or_max:
    #                 # The default is True
    #                 player.plays = False
    #                 # Break, as only one player has max/min votes because min/max is unique
    #                 break
    #     # Not unique, no majority
    #     elif occurence > 1:
    #         self.all_play = True


    # Setting the goup level -  excluded player - variable



class Player(BasePlayer):


    ### Public Good Variables

    germanplayerlabel = models.StringField(doc="See player label.")

    playerlabel = models.CharField(
        doc='The player name. Player A - Player E',
        choices=['Player A', 'Player B', 'Player C', 'Player D', 'Player E'])

    treatment = models.CharField(
        doc='Defines the treatment of the session. The treatment is the same for all players in one session.'
            'In "exclude", player can vote exclude players. In "control", no voting exists',
        choices=['voting', 'novoting'])

    city = models.CharField(
        doc='Defines the city where the experiment took place ',
        choices=['münchen', 'heidelberg'])

    contribution = models.IntegerField(
        doc='The players contribution in the public good game in Taler',
        verbose_name='Ihr Betrag',
        min=0,
        max=Constants.endowment)


    myvotes = models.IntegerField(
        doc='The number of votes the player got after the public good game.')

    ivoted = models.IntegerField(doc='The number of votes the player distributed to other players. This could be in {0,4} depending on the implementation.',
                                 initial=0)

    plays = models.BooleanField(
        doc='Determines if the player is allowed to play the guessing game in a particular round.',
        default = True
    )

    #set in set_socialgame()
    sanctioned = models.BooleanField(doc='Determines if the player was sanctioned after the vote. Sanctioning means Exclusion, Rüge or monitary punishment.',
                                     default=False)

    # does the player play the bonus FF round after all rounds of the experiment according to the evaluation mechanism
    # depends on the valuationFF results
    plays_bonusFF = models.BooleanField(initial=True,
                                        doc="This determines if the player plays the bonus guessing game round at the end of the experiment. \
                                             This is true if the players willingness to pay (ff_valuation) is higher than the computer (number random_ff_valuation)")


    round_payoff = models.IntegerField(initial=0, doc="The amount of Taler of the player in a particular round.")

    # Variables where player can vote to exclude/invite one player from the social arena game
    vote_A = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Teilnehmer A',
        doc="The player voted for Player A")
    vote_B = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Teilnehmer B',
        doc="The player voted for Player B")
    vote_C = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Teilnehmer C',
        doc="The player voted for Player C")
    vote_D = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Teilnehmer D',
        doc="The player voted for Player D")
    vote_E = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Teilnehmer E',
        doc="The player voted for Player E")


    exclude_none = models.BooleanField(widget=widgets.CheckboxInput(),
                                       verbose_name="Ich möchte für kein Gruppenmitglied stimmen.",
                                       doc = "The player wanted not to vote for any other player.")


    # RateYourExperience after every FamilyFeud game
    ff_experience = models.IntegerField(verbose_name="Bitte klicken Sie auf die Skala, um Ihre Erfahrung während des letzten Gruppenspiels zu bewerten. 1 bedeutet schlecht und 5 gut.",
                                        widget=widgets.Slider(show_value=False) , min=1, max=5,
                                        doc="After the guessing game the players have to rate their experience on a scale from 1(bad) to 5(good)")


    # the willingness to pay for the bonus family feud round
    ff_valuation = models.DecimalField(verbose_name="Bitte klicken Sie auf die Skala, um ihre Zahlungsbereitschaft auszuwählen.",
                                       widget=widgets.Slider(show_value=False),
                                       min=0, max=6,
                                       decimal_places=1,
                                       max_digits = 2,
                                       doc="The players' willingness to pay for the bonus round of the guessing game.",
                                       initial=0)

    random_ff_valuation = models.FloatField(doc="The computer number which will be to compared with ff_valuation to determine if the player plays the bonus round.",
                                            initial=0.0)


    ## the round number that will be payed out for the player
    payround = models.IntegerField(doc="The round number that will be payed out for the player. Note: this is an oTree round e. g. experiment_round+1.")





    ######################################################################################################################
    ### Questionnaire variables


    q1 = models.IntegerField(verbose_name="Was denken Sie, wie viele Taler sollte man zum Gruppenkonto beitragen?", min=0 , max=10)
    q2 = models.StringField(widget=widgets.RadioSelect(),verbose_name="Denken Sie, die meisten anderen sehen das auch wie Sie?", choices=["Ja",
                                                                                                             "Ich bin mir unsicher",
                                                                                                             "Nein, die meisten anderen denken man sollte mehr beitragen",
                                                                                                             "Nein, die meisten anderen denken man sollte weniger beitragen",
                                                                                                             ])

    #only in exclude
    q3 = models.StringField(widget=widgets.RadioSelect(),verbose_name="In jeder Runde hatten Sie die Möglichkeit, Gruppenmitglieder vom Gruppenspiel auszuschließen. Welche Überlegungen haben Sie dabei angestellt? (Bitte wählen Sie die Option, die am besten passt.)",
                            choices=["Ich habe rein zufällig meine Stimme vergeben",
                                    "Ich wollte Gruppenmitglieder für Ihr Verhalten in der vorherigen Stufe bestrafen",
                                    "Ich wollte andere von der Last des Gruppenspiels befreien",
                                    "Ich wollte ausprobieren was passiert",
                                    "Ich habe in keiner Runde eine Stimme abgegeben"])

    #only in exclude
    q4 = models.StringField(widget=widgets.RadioSelect(),
        verbose_name="Was denken Sie, warum haben andere Teilnehmer dafür gestimmt, Gruppenmitglieder auszuschließen?",
        choices=["Rein zufällig",
                 "Sie wollten Gruppenmitglieder für Ihr Verhalten in der vorherigen Stufe bestrafen",
                 "Sie wollten andere von der Last des Gruppenspiels befreien",
                 "Sie wollten andere von der Last des Gruppenspiels befreien",
                 "Sie wollten ausprobieren was passiert"])

    q5 = models.IntegerField(verbose_name="Bitte geben Sie ihr Alter an", min=0, max=99)
    q7 = models.StringField(verbose_name="Bitte geben Sie ihr Studienfach an")
    q8 = models.IntegerField(min=0,verbose_name="Wie oft haben Sie bereits an einer ökonomischen Laborstudie teilgenommen (auch außerhalb dieses Labors)?")
    q9 = models.StringField(verbose_name="Wie viele Teilnehmerinnen oder Teilnehmer in diesem Raum haben Sie schon vor dem Experiment gekannt?")
    q10 = models.StringField(verbose_name="Möchten Sie uns noch etwas mitteilen? Hier ist die Gelegenheit dazu!")



    ######################################################################################################################
    ### Control Variables


    ##how often did the participant try to submit the control questions when some answers were still wrong
    # if the participant was correct on the first try, than this will be 1
    control_tries = models.IntegerField(initial=0, doc="How often did the player try to submit the control questions page when answers were still wrong. \
                                                       1 if the player had everything correct on the first try.")


    # only + nosanction + exlude + dislike + punish
    control1 = models.IntegerField(verbose_name="Wie viele Taler haben Sie auf Ihrem privaten Konto, wenn Sie 3 Taler auf das Gruppenkonto einzahlen?",
                                   min=0)

    # only + nosanction + exlude + dislike + punish
    control2 = models.IntegerField(verbose_name="20 Taler wurden insgesamt in das Gruppenkonto eingezahlt. Wie viele Taler erhalten Sie am Ende aus dem Gruppenkonto?",
                                   min=0)

    # only + nosanction + exlude + dislike + punish
    control3a = models.StringField(widget=widgets.RadioSelect(),verbose_name="Es kann sein, dass verschiedene Gruppenmitglieder unterschiedlich viele Taler aus dem Gruppenkonto erhalten.",
                                   choices=["wahr", "falsch"])

    # only + nosanction + exlude + dislike + punish
    control3b = models.StringField(widget=widgets.RadioSelect(),
        verbose_name="Am Ende der ersten Stufe einer jeweiligen Runde wissen Sie, wie viel jedes Gruppenmitglied ins Gruppenkonto eingezahlt hat.",
        choices=["wahr", "falsch"])

    # only + nosanction + exlude + dislike + punish
    control3c = models.StringField(widget=widgets.RadioSelect(),
        verbose_name="Sie spielen in jeder Runde in einer neuen Gruppe mit anderen Personen",
        choices=["wahr", "falsch"])

    # exclude
    control3d = models.StringField(widget=widgets.RadioSelect(),
        verbose_name="Sollten Sie in einer Runde vom Gruppenspiel ausgeschlossen werden, so können Sie in der nächsten Runde nicht an der Aufteilungsentscheidung teilnehmen.",
        choices=["wahr", "falsch"])

    # exclude
    control4 = models.IntegerField(widget=widgets.RadioSelectHorizontal(),
                                   verbose_name="Für den Ausschluss von wie vielen Gruppenmitgliedern können Sie maximal stimmen?",
                                   choices=[0, 1, 2, 3, 4, 5])

    #exclude
    control5 = models.StringField(widget=widgets.RadioSelectHorizontal(),
        verbose_name="Wie viele Taler kostet es Sie, wenn Sie ein Gruppenmitglied ausschließen?",
        choices=["0 Taler  ", "0,5 Taler  ", "1 Taler  ", "1,5 Taler  ", "2 Taler  "])

    #exclude
    control6 = models.StringField(widget=widgets.RadioSelect(),
        verbose_name="Sie erhalten zwei Stimmen. Dürfen Sie an dem Gruppenspiel teilnehmen?",
        choices=["ja", "nein"])

    # nosanction + dislike + punishment
    control7control = models.StringField(widget=widgets.RadioSelect(),
        verbose_name="Mit wem spielen Sie das Gruppenspiel?",
        choices=["Alleine",
                 "Mit 4 Teilnehmern, die in Stufe 1 dieser Runde nicht in meiner Gruppe waren",
                 "Mit den 4 Teilnehmern, die in Stufe 1 dieser Runde in meiner Gruppe waren"])

    #exclude
    control7exclude = models.StringField(widget=widgets.RadioSelect(),
        verbose_name="Mit wem spielen Sie das Gruppenspiel?",
        choices=["Alleine",
                 "Mit 4 Teilnehmern, die in Stufe 1 dieser Runde nicht in meiner Gruppe waren",
                 "Mit den Teilnehmern meiner Gruppe, die nicht ausgeschlossen wurden",
                 "Mit den ausgeschlossenen Gruppenmitgliedern aus dieser Runde"])

    # nosanction + exclude + dislike + punishment
    control8 = models.StringField(widget=widgets.RadioSelect(),
        verbose_name="Was passiert, wenn Sie einen richtigen Begriff im Gruppenspiel eingeben?",
        choices=["Nichts",
                 "Er wird allen Gruppenmitgliedern gezeigt und ich verdiene einen Taler",
                 "Er wird allen Gruppenmitgliedern gezeigt und die Gruppe bekommt einen Spielpunkt"])






    ######################################################################################################################


    ### Family Feud Variables
    guess_sequence = models.CharField(initial='')

    # Number of correctly answered questions
    ff_points = models.IntegerField(initial=0, doc="The number of correct answers which the player found overall in the guessing game in one round.")

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






