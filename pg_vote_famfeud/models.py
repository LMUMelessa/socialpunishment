from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from otree_redwood.models import Group as RedwoodGroup
import csv,random

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'pg_vote_famfeud'
    players_per_group = 5
    num_rounds = 1
    #pg - vars
    endowment = 10
    multiplier = 2

    ### familyfeud
    questions_per_round = 3
    secs_per_question = 30
    wait_between_question = 5

    with open('data.csv') as f:
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

    #TODO this is deterministic but should be fine as I group randomly?
    def define_label(self):
        labellist = ['Player A', 'Player B', 'Player C', 'Player D', 'Player E']
        for group in self.get_group_matrix():
            for player in group:
                player.playerlabel = labellist[player.id_in_group-1]

    def creating_session(self):
        # Assign treatment
        for player in self.get_players():
            player.treatment = self.session.config['treatment']
            player.city = self.session.config['city']
        #TODO: is group randomly the desired impementation?
        if self.round_number == 1:
            self.group_randomly()
        else:
            self.group_like_round(1)
        # Assign the labels
        self.define_label()

        ### family feud
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

            for round_num in range(1, Constants.num_rounds + 1):
                for question_num in range(1, questions_per_round + 1):
                    question = random.choice(quizload)
                    quizload.remove(question)
                    # Save the quizload of the question in session.vars to access later
                    # ql_11 e.g. means quizload for round 1 question 1
                    self.session.vars['ql_' + str(round_num) + str(question_num)] = question

    pass


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
        # TODO delete me..
        print('when all players ready was called...')
        # send the whole quiz package (one question) to the channel
        self.sendquizload_toplayers()
        return


        # this will triger 'receive_question ()' function in javascript and in javascript the timers will be initialized
        # the function is called at the beginning from when_all_players_ready and under multiple questions when requested from a player through questionChannel

    def sendquizload_toplayers(self):

        # increment the current question number
        # TODO: You need save() for all database operations ingame, otherwise the changes have no effect on the database
        # TODO: see the oTree Redwood doc Group.save()
        self.current_quest_num += 1
        self.save()

        # send the correct question to javascript, see the formatting in creating_session
        self.send('questionChannel', self.session.vars['ql_' + str(self.round_number) + str(self.current_quest_num)])

        ## update the question sequence, to have the question in the database
        # string sentence of the question
        question = self.session.vars['ql_' + str(self.round_number) + str(self.current_quest_num)]['question']
        # TODO: use a better string operation
        self.question_sequence = self.question_sequence + str(self.current_quest_num) + ':' + question + ';'
        self.save()

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
        # TODO Delete me
        print('I went into "_on_guessing_Channel_events_" function...')
        print('I received the guess of the player, the guess is: %s' % (event.value['guess']))

        # the guess of the player
        guess = event.value['guess'].lower()
        # id of the guessing player
        player_id_in_group = event.value['id']

        # player object of the guessing player
        player = self.get_player_by_id(player_id_in_group)

        # the current question quizload (dictionaire)
        question = self.session.vars['ql_' + str(self.round_number) + str(self.current_quest_num)]

        # update the guess sequence of the player
        # TODO: Use a better string operation
        player.guess_sequence = player.guess_sequence + str(self.current_quest_num) + ':' + str(guess) + ';'
        player.save()

        good_guess = False
        questionindex = 0
        # check if the guess is correct, if yes and not answered correctly before, send respective information back to javascript
        for answernum in ['s1', 's2', 's3', 's4', 's5']:
            # e. g. question[s1] is a list with all the solutions for the correct word 1 of the current question
            if guess in list(map(lambda x: x.lower(), question[answernum])):  # guess is correct
                good_guess = True
                # only take action and distribute ff_points if the correct answer has not been guessed before
                if [self.s1_answered, self.s2_answered, self.s3_answered, self.s4_answered, self.s5_answered][questionindex] != True:
                    # give the player a point (save() is called in the function)
                    player.inc_ff_points()

                    # give the group a point
                    self.group_ff_points += 1
                    self.save()

                    # update, so that the question cannot be answered again
                    # TODO make this assignment nice, please!
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

                    # Todo Delete me
                    print([self.s1_answered, self.s2_answered, self.s3_answered, self.s4_answered, self.s5_answered])
                    # determine, if now all possible answers have been found
                    finished = all(
                        [self.s1_answered, self.s2_answered, self.s3_answered, self.s4_answered, self.s5_answered])

                    # send informations back to javascript, this activates 'instructions_after_guess()'
                    self.send('guessInformations', {'guess': question[answernum][0],
                                                    # send the exactly correct answer back, which is the 0 element of the list
                                                    'whichword': answernum,
                                                    'idInGroup': player_id_in_group,
                                                    'correct': True,
                                                    'finished': finished})

                    print('thats finished' + str(finished))


                # TODO: note: with that design choice, if a question is answered correctly for the second time, just nothing happens
                # TODO: there will be also nothing displayed in the group guess message board
                # guess was correct, but that correct guess was already made before
                # do nothing, dont send anything out, dont distribute ff_points
                else:
                    pass
                # we can break here, because this is the space where the guess was correct, so then no other of the answers has to be checked
                break
            questionindex += 1

        # guess was not correct, send respective informations back
        if good_guess == False:
            self.send('guessInformations', {'guess': guess,
                                            'idInGroup': player_id_in_group,
                                            'correct': False})

            # TODO can you just leave out the period length function?

    def period_length(self):
        # take overall time * 10 so that oTree redwood, cannot abort the game, page submission is done in javascript
        # the reason is that, with multible rounds the overall time taken for the family feud game might not been exactly the same
        # TODO why not just putting an infinitely large number in here?
        return (
               (Constants.questions_per_round) * ((Constants.secs_per_question + Constants.wait_between_question))) * 10


    #### Family feud end


    ### Public good game
    all_play = models.BooleanField(
        doc= 'Boolean. Defines if all player play the social arena game in a round.')


    total_cont = models.CurrencyField(
        doc='The overall contribution of the group in the public good game.')

    indiv_share = models.CurrencyField(
        doc='The share the players get after the public good game.')

    # Is needed so that we can display on any template the excluded player
    excluded_player = models.CharField(
        doc='The player, who is excluded from the social game.')


    # Payoffs for pg game; function also sets total_cont and indiv_share
    def set_payoffs(self):
        self.total_cont = sum([p.contribution for p in self.get_players()])
        self.indiv_share = (self.total_cont * Constants.multiplier) / Constants.players_per_group
        for p in self.get_players():
            p.payoff = (Constants.endowment - p.contribution) + self.indiv_share


    # Assigns for all the players how many votes they had
    # The variable updated is player.myvotes
    def set_myvotes(self):
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



    # Find out if there is a majority after the voting
    # Assign for all players if they play in the second game (social game, familyfeud)
    # Assign if the second game/social game/family feud will be played with all players in the group
    # Sets group.all_play and player.plays
    def set_social_game(self):
        invitationslist = []

        # Collect all the votes
        for player in self.get_players():
            invitationslist.append(player.myvotes)


        # Find the highest number of votes a player had

        min_or_max = None

        if self.get_players()[0].treatment == 'exclude' or self.get_players()[0].treatment == 'feedback' :
            min_or_max = max(invitationslist)
        elif self.get_players()[0].treatment == 'include':
            min_or_max = min(invitationslist)

        # Check if max/min is unique, because in that case there is a majority
        occurence = invitationslist.count(min_or_max)
        # Unique max/min, there is a majority
        if occurence == 1:
            self.all_play = False
            # Identify the player with the most exclusions
            for player in self.get_players():
                if player.myvotes == min_or_max:
                    # The default is True
                    player.plays = False
                    # Break, as only one player has max/min votes because min/max is unique
                    break
        # Not unique, no majority
        elif occurence > 1:
            self.all_play = True


    # Setting the goup level -  excluded player - variable
    def set_excluded_player(self):
        for player in self.get_players():
            if player.plays == False:
                self.excluded_player = player.playerlabel
                # Break, because only one player is excluded
                break


class Player(BasePlayer):


    # Public Good Variables
    playerlabel = models.CharField(
        doc='The player name. Player A - Player E',
        choices=['Player A', 'Player B', 'Player C', 'Player D', 'Player E'])

    treatment = models.CharField(
        doc='Defines the treatment of the session. The treatment is the same for all players in one session.'
            'In "voting" player can exclude players. In "novoting" no voting stage exists',
        choices=['voting', 'novoting'])

    city = models.CharField(
        doc='Defines the city where the experiment took place ',
        choices=['münchen', 'heidelberg'])

    contribution = models.CurrencyField(
        doc='The players contribution in the public good game',
        verbose_name='What do you want to contribute to the project?',
        min=0,
        max=Constants.endowment)


    myvotes = models.IntegerField(
        doc='The number of votes the player got after the public good game.')

    plays = models.BooleanField(
        doc='Determines if the player is allowed to play the social game.',
        default = True
    )


    # Variables where player can vote to exclude/invite one player from the social arena game
    vote_A = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Player A')
    vote_B = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Player B')
    vote_C = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Player C')
    vote_D = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Player D')
    vote_E = models.BooleanField(
        widget=widgets.CheckboxInput(),
        verbose_name='Player E')


    # In exlude treatment and feedback treatment
    exclude_none = models.BooleanField(widget=widgets.CheckboxInput(), verbose_name="I don't want to vote for any player.")

    ### Family Feud Variables
 
    guess_sequence = models.CharField(initial='')

    # number of correctly answered questions
    ff_points = models.IntegerField(initial=0)

    # number of tries (guesses) of a player
    num_guesses = models.IntegerField(initial=0)

    def inc_num_guesses(self):
        self.num_guesses += 1
        self.save()


    def inc_ff_points(self):
        self.ff_points += 1
        self.save()


    def initial_decision(self):
        return 0.5



