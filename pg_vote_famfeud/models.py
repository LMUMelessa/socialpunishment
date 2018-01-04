from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from otree_redwood.models import Group as RedwoodGroup

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'pg_vote_famfeud'
    players_per_group = 5
    num_rounds = 3
    #pg - vars
    endowment = 10
    multiplier = 2



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




    pass


class Group(RedwoodGroup):


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
        _max = max(invitationslist)

        # Check if max is unique, then there is a majority
        occurence = invitationslist.count(_max)
        # Unique max, there is a majority
        if occurence == 1:
            self.all_play = False
            # Identify the player with the most exclusions
            for player in self.get_players():
                if player.myvotes == _max:
                    # The default is True
                    player.plays = False
                    # Break, as only one player has max votes because max is unique
                    break
        # Not unique, no majority
        elif occurence > 1:
            self.all_play = True


    def set_excluded_player(self):
        for player in self.get_players():
            if player.plays == False:
                self.excluded_player = player.playerlabel
                # Break, because only one player is excluded
                break


class Player(BasePlayer):

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


    # Variables where player can vote to exclude one player from the social arena game
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




