from pypokerengine.players import BasePokerPlayer
import random as rand
import pprint

class Agent22Player(BasePokerPlayer):

    # Street name constant
    STREET_ZERO_CARD = "preflop"
    STREET_THREE_CARD = "flop"
    STREET_FOUR_CARD = "turn"
    STREET_FIVE_CARD = "river"

    # Action name constant
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"

    # Action index constant
    FOLD_INDEX = 0
    CALL_INDEX = 1
    RAISE_INDEX = 2

    # Game constant (declared here as it is difficult to check during game)
    # ENGINE BUG: The engine uses 20 for preflop, flop and 40 for turn, river 
    # instead of 10 like the project specification stated
    RAISE_AMOUNT_PREFLOP = 20
    RAISE_AMOUNT_FLOP = 20
    RAISE_AMOUNT_TURN = 40
    RAISE_AMOUNT_RIVER = 40

    # Limited poker constant
    NUM_STREET_PER_ROUND = 4
    NUM_RAISE_PER_STREET = 4
    NUM_RAISE_PER_ROUND_PER_PLAYER = 4

    # Player turn constant
    PLAYER_TURN = True
    OPPONENT_TURN = False

    # Street index
    STREET_INDEX_DICT = {
    	STREET_ZERO_CARD: 0,
    	STREET_THREE_CARD: 1,
    	STREET_FOUR_CARD: 2,
    	STREET_FIVE_CARD: 3
    }

    # Raise amount dictionary
    RAISE_AMOUNT_DICT = {
    	STREET_ZERO_CARD: RAISE_AMOUNT_PREFLOP,
    	STREET_THREE_CARD: RAISE_AMOUNT_FLOP,
    	STREET_FOUR_CARD: RAISE_AMOUNT_TURN,
    	STREET_FIVE_CARD: RAISE_AMOUNT_RIVER,
    	0: RAISE_AMOUNT_PREFLOP,
    	1: RAISE_AMOUNT_FLOP,
    	2: RAISE_AMOUNT_TURN,
    	3: RAISE_AMOUNT_RIVER
    }

    # Hold card probability look up table
    # To search: self.PREFLOP_EXPECTED_VALUE[is_same_shape][lower_card_number][higher_card_number]
    """ TO BE FILLED HERE """
    PREFLOP_PROBABILITY = {
    	# Same shape (suited)
    	True: {
    		# Lower card number
    		"2": {
    			# Higher card number
    			"3": -0.2803, "4": -0.2634	, "5": -0.2430	, "6": -0.2466	, "7": -0.2369	,
    			"8": -0.1946, "9": -0.1517	, "T": -0.1032	, "J": -0.0524	, "Q": 0.0034	,
    			"K": 0.0642	, "A": 0.1476
    		},
    		"3": {
    			"4": -0.2272
    			# ...
    		}
    		# ...
    	},
    	# Different shape (unsuited)
    	False: {
    		# Lower card number
    		"2": {
    			# Higher card number
    			"2": 0.0067	, "3": -0.3539	, "4": -0.3360	, "5": -0.3143	, "6": -0.3185	,
    			"7": -0.3083, "8": -0.2634	, "9": -0.2180	, "T": -0.1666	, "J": -0.1130	,
    			"Q": -0.0541, "K": 0.0102	, "A": 0.0986
    		},
    		"3": {
    			"3": 0.0739
    			# ...
    		}
    		# ...
    	}
    }


    def __init__(self):
        BasePokerPlayer.__init__(self)
        # To be re-initialized at the start of each game
        # Agent info
        # self.uuid is already initialized by the engine
        self.name = "agent22"
        self.seat_pos = 0
        # Rule info
        self.small_blind_amount = 0
        self.big_blind_amount = 0
        self.max_round = 1000
        # To be re-initialized at the start of each round
        # Round info
        self.round_count = 0
        self.big_blind_seat_pos = 0
        self.hole_card = []
        self.player_stack_at_start_of_round = 10000
        self.opponent_stack_at_start_of_round = 10000
        # To be re-initialized at the start of each street
        # Street info
        self.street = self.STREET_ZERO_CARD
        self.is_start_of_street = True
        self.community_card = []
        self.player_bet_at_start_of_street = 0
        self.opponent_bet_at_start_of_street = 0
        self.remaining_raise_this_street = self.NUM_RAISE_PER_STREET
        self.remaining_player_raise_this_round = self.NUM_RAISE_PER_ROUND_PER_PLAYER
        self.remaining_opponent_raise_this_round = self.NUM_RAISE_PER_ROUND_PER_PLAYER 
        self.winning_probability = 0.5
        self.drawing_probability = 0
        # To be re-initialized at the start of each update
        # Current info
        self.player_stack = 10000
        self.opponent_stack = 10000
        self.player_bet = 0
        self.opponent_bet = 0
        self.last_action = {}
        # Pre-calculating and populating data for estimating the future raising amount
        self.avg_raise_amount_remaining_street = []
        self.pre_calculate_avg_raise_amount_remaining_street()

    def declare_action(self, valid_actions, hole_card, round_state):
        call_action_info = valid_actions[self.best_action(valid_actions)]
        action = call_action_info["action"]
        return action  # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
    	# initialize game infomation
    	self.small_blind_amount = game_info["rule"]["small_blind_amount"]
    	self.big_blind_amount = 2 * self.small_blind_amount
    	self.max_round = game_info["rule"]["max_round"]
        # initialize personal data
        for i in range(0, len(game_info["seats"])):
            if game_info["seats"][i]["uuid"] == self.uuid:
                self.seat_pos = i
                self.name = game_info["seats"][i]["name"]
    	# initialize money stack
    	self.player_stack_at_start_of_round = game_info["rule"]["initial_stack"]
    	self.opponent_stack_at_start_of_round = game_info["rule"]["initial_stack"]
    	self.player_stack = self.player_stack_at_start_of_round
    	self.opponent_stack = self.opponent_stack_at_start_of_round
        # DEBUG
        # pprint.pprint(game_info)
        # print("-----GAME START-----")
        # print("name: " + str(self.name))
        # print("uuid: " + str(self.uuid))
        # print("small_blind_amount: " + str(self.small_blind_amount))
        # print("big_blind_amount: " + str(self.big_blind_amount))
        # print("max_round: " + str(self.max_round))
        # print("seat_pos: " + str(self.seat_pos))
        # print("--------------------")
        # pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        # Initialize round info
        self.round_count = round_count
        self.hole_card = list(hole_card)
        self.remaining_player_raise_this_round = self.NUM_RAISE_PER_ROUND_PER_PLAYER
        self.remaining_opponent_raise_this_round = self.NUM_RAISE_PER_ROUND_PER_PLAYER
        # Initialize last action
        self.last_action = {}
        # Initialize for preflop street
        self.player_bet_at_start_of_street = 0
        self.opponent_bet_at_start_of_street = 0
        self.remaining_raise_this_street = self.NUM_RAISE_PER_STREET
        # Update stack and initialize small/big blind bet
        for i in range(0, len(seats)):
            if seats[i]["uuid"] == self.uuid:
            	self.player_stack = seats[i]["stack"]
                self.player_bet = self.player_stack_at_start_of_round - self.player_stack
                # big blind/all in is considered as a raise
                if self.player_bet > self.small_blind_amount:
                	self.remaining_raise_this_street -= 1
                	self.big_blind_seat_pos = i
            else:
                self.opponent_stack = seats[i]["stack"]
                self.opponent_bet = self.opponent_stack_at_start_of_round - self.opponent_stack
                # big blind/all in is considered as a raise
                if self.opponent_bet > self.small_blind_amount:
                	self.remaining_raise_this_street -= 1
                	self.big_blind_seat_pos = i
        # DEBUG
        # pprint.pprint(hole_card)
        # pprint.pprint(seats)
        # print("-----ROUND START-----")
        # print("round_count: " + str(self.round_count))
        # print("big_blind_seat_pos: " + str(self.big_blind_seat_pos))
        # print("hole_card: ")
        # pprint.pprint(self.hole_card)
        # print("player_stack_at_start_of_round: " + str(self.player_stack_at_start_of_round))
        # print("opponent_stack_at_start_of_round: " + str(self.opponent_stack_at_start_of_round))
        # print("---------------------")
        # pass

    def receive_street_start_message(self, street, round_state):
        # Initialize street info
        self.street = street
        self.is_start_of_street = True
        self.community_card = list(round_state["community_card"])
        # Initialize for non-preflop street
        if self.street != self.STREET_ZERO_CARD:
        	self.remaining_raise_this_street = self.NUM_RAISE_PER_STREET
        	self.player_bet_at_start_of_street = self.player_bet
        	self.opponent_bet_at_start_of_street = self.opponent_bet
        # Update stacks
        for i in range(0, len(round_state["seats"])):
            if round_state["seats"][i]["uuid"] == self.uuid:
            	self.player_stack = round_state["seats"][i]["stack"]
            else:
            	self.opponent_stack = round_state["seats"][i]["stack"]
        # Recalculate winning probability
        self.re_calculate_probability()
        # DEBUG
        # pprint.pprint(round_state)
        # print("-----STREET START-----")
        # print("street: " + str(self.street))
        # print("raise_amount: " + str(self.raise_amount(self.street)))
        # print("avg_raise_amount_remaining_street: " + str(self.avg_raise_amount_remaining_street[self.STREET_INDEX_DICT[self.street]]))
        # pprint.pprint(self.community_card)
        # print("player_bet_at_start_of_street: " + str(self.player_bet_at_start_of_street))
        # print("opponent_bet_at_start_of_street: " + str(self.opponent_bet_at_start_of_street))
        # print("player_bet: " + str(self.player_bet))
        # print("opponent_bet: " + str(self.opponent_bet))
        # print("----------------------")
        # pass

    # ENGINE BUG (RARE): Poker game might send update message 2 times
    # In order to update number of remaining raise while dealing with this bug,
    # we make use of the fact that a player cannot preform 2 identical raise action 
    # subsequently withour letting the opponent do anything
    def receive_game_update_message(self, action, round_state):
    	# Check for repeating bug
    	if ((action != self.last_action) or (self.is_start_of_street == True)):
    		# Update bet amount
    		if action["player_uuid"] == self.uuid:
    			if action["action"] != self.FOLD:
    				self.player_bet = self.player_bet_at_start_of_street + action["amount"]
    			if action["action"] == self.RAISE:
    				self.remaining_raise_this_street -= 1
    				self.remaining_player_raise_this_round -= 1
    		else:
    			if action["action"] != self.FOLD:
    				self.opponent_bet = self.opponent_bet_at_start_of_street + action["amount"]
    			if action["action"] == self.RAISE:
    				self.remaining_raise_this_street -= 1
    				self.remaining_opponent_raise_this_round -= 1
    		# Update stacks
    		for i in range(0, len(round_state["seats"])):
				if round_state["seats"][i]["uuid"] == self.uuid:
					self.player_stack = round_state["seats"][i]["stack"]
            	else:
            		self.opponent_stack = round_state["seats"][i]["stack"]
    		# An action has been preformed since the start of the street
    		self.is_start_of_street = False
        # Update last action
        self.last_action = dict(action)
  	    # DEBUG
        # pprint.pprint(action)
        # pprint.pprint(round_state)
        # print("-----GAME UPDATE-----")
        # print("player_bet: " + str(self.player_bet))
        # print("opponent_bet: " + str(self.opponent_bet))
        # print("player_stack: " + str(self.player_stack))
        # print("opponent_stack: " + str(self.opponent_stack))
        # print("remaining_raise_this_street: " + str(self.remaining_raise_this_street))
        # print("remaining_player_raise_this_round: " + str(self.remaining_player_raise_this_round))
        # print("remaining_opponent_raise_this_round: " + str(self.remaining_opponent_raise_this_round))
        # print("---------------------")
        # pass

    def receive_round_result_message(self, winners, hand_info, round_state):
    	# Update stacks
    	for i in range(0, len(round_state["seats"])):
            if round_state["seats"][i]["uuid"] == self.uuid:
            	self.player_stack = round_state["seats"][i]["stack"]
            	self.player_stack_at_start_of_round = self.player_stack
            else:
            	self.opponent_stack = round_state["seats"][i]["stack"]
            	self.opponent_stack_at_start_of_round = self.opponent_stack
        # DEBUG
        # pprint.pprint(winners)
        # pprint.pprint(hand_info)
        # pprint.pprint(round_state)
        # print("-----ROUND RESULT-----")
        # print("player_stack: " + str(self.player_stack))
        # print("opponent_stack: " + str(self.opponent_stack))
        # print("----------------------")
        # pass

    def raise_amount(self, street):
    	# Default result: RAISE_AMOUNT_PREFLOP
    	result = self.RAISE_AMOUNT_DICT.get(street, self.RAISE_AMOUNT_PREFLOP)
    	return result

    # First call of the heuristic minimax search, return best action index
    # Special case: call in the very first turn of the street will not end the street
    def best_action(self, valid_actions):
    	bet_diff = self.opponent_bet - self.player_bet
    	# Initialize with fold action
    	best_outcome = (-1) * self.player_bet
    	best_action_index = self.FOLD_INDEX
    	# Check call action
    	call_outcome = 0
    	if self.is_start_of_street == True:
    		call_outcome = self.heuristic_minimax(
    							self.OPPONENT_TURN,
    							self.opponent_bet,
    							self.opponent_bet,
    							self.player_stack - bet_diff,
    							self.opponent_stack,
    							self.remaining_player_raise_this_round,
    							self.remaining_opponent_raise_this_round,
    							self.remaining_raise_this_street)
    	else:
    		call_outcome = self.expected_outcome(
    							self.opponent_bet,
    							self.player_stack - bet_diff,
    							self.opponent_stack,
    							self.remaining_player_raise_this_round,
    							self.remaining_opponent_raise_this_round)
    	if call_outcome >= best_outcome:
    		best_outcome = call_outcome
    		best_action_index = self.CALL_INDEX
    	# Check raise action
    	if len(valid_actions) == 3:
    		raise_outcome = 0
    		raise_amount_this_street = self.raise_amount(self.street)
    		player_has_enough_money = (self.player_stack >= (bet_diff + raise_amount_this_street))
    		opponent_has_enough_money = (self.opponent_stack >= raise_amount_this_street)
    		if (player_has_enough_money and opponent_has_enough_money):
    			raise_outcome = self.heuristic_minimax(
    								self.OPPONENT_TURN,
    								self.opponent_bet + raise_amount_this_street,
    								self.opponent_bet,
    								self.player_stack - bet_diff - raise_amount_this_street,
    								self.opponent_stack,
    								self.remaining_player_raise_this_round - 1,
    								self.remaining_opponent_raise_this_round,
    								self.remaining_raise_this_street - 1)
    		else:
    			last_raise_amount = min(self.player_stack - bet_diff, self.opponent_stack)
    			raise_outcome = self.heuristic_minimax(
    								self.OPPONENT_TURN,
    								self.opponent_bet + last_raise_amount,
    								self.opponent_bet,
    								self.player_stack - bet_diff - last_raise_amount,
    								self.opponent_stack,
    								self.remaining_player_raise_this_round - 1,
    								self.remaining_opponent_raise_this_round,
    								self.remaining_raise_this_street - 1)
    		if raise_outcome >= best_outcome:
    			best_outcome = raise_outcome
    			best_action_index = self.RAISE_INDEX
    	return best_action_index


    # Special case in the first turn of the street is already checked in best_action
    def heuristic_minimax(self,
    					player_turn,
    					player_bet,
    					opponent_bet,
    					player_stack,
    					opponent_stack,
    					remaining_player_raise_this_round,
    					remaining_opponent_raise_this_round,
    					remaining_raise_this_street
    					):
    	best_outcome = 0
    	call_outcome = 0
    	raise_outcome = 0
    	raise_amount_this_street = self.raise_amount(self.street)
    	# Max player
    	if player_turn == self.PLAYER_TURN:
    		best_outcome = (-1) * player_bet
    		bet_diff = opponent_bet - player_bet
    		# Check call outcome
    		call_outcome = self.expected_outcome(
    							opponent_bet,
    							player_stack - bet_diff,
    							opponent_stack,
    							remaining_player_raise_this_round,
    							remaining_opponent_raise_this_round)
    		if call_outcome >= best_outcome:
    			best_outcome = call_outcome
    		# Check raise outcome
    		if remaining_raise_this_street > 0:
    			if remaining_player_raise_this_round > 0:
    				if ((player_stack > bet_diff) and (opponent_stack > 0)):
    					player_has_enough_money = (player_stack >= (bet_diff + raise_amount_this_street))
    					opponent_has_enough_money = (opponent_stack >= raise_amount_this_street)
    					if (player_has_enough_money and opponent_has_enough_money):
    						raise_outcome = self.heuristic_minimax(
    											self.OPPONENT_TURN,
    											opponent_bet + raise_amount_this_street,
    											opponent_bet,
    											player_stack - bet_diff - raise_amount_this_street,
    											opponent_stack,
    											remaining_player_raise_this_round - 1,
    											remaining_opponent_raise_this_round,
    											remaining_raise_this_street - 1)
    					else:
    						last_raise_amount = min(player_stack - bet_diff, opponent_stack)
    						raise_outcome = self.heuristic_minimax(
    											self.OPPONENT_TURN,
    											opponent_bet + last_raise_amount,
    											opponent_bet,
    											player_stack - bet_diff - last_raise_amount,
    											opponent_stack,
    											remaining_player_raise_this_round - 1,
    											remaining_opponent_raise_this_round,
    											remaining_raise_this_street - 1)
    					if raise_outcome >= best_outcome:
    						best_outcome = raise_outcome
    	# Min player
    	else:
    		best_outcome = opponent_bet
    		bet_diff = player_bet - opponent_bet
    		# Check call outcome
    		call_outcome = self.expected_outcome(
    							player_bet,
    							player_stack,
    							opponent_stack - bet_diff,
    							remaining_player_raise_this_round,
    							remaining_opponent_raise_this_round)
    		if call_outcome <= best_outcome:
    			best_outcome = call_outcome
    		# Check raise outcome
    		if remaining_raise_this_street > 0:
    			if remaining_opponent_raise_this_round > 0:
    				if ((opponent_stack > bet_diff) and (player_stack > 0)):
    					opponent_has_enough_money = (opponent_stack >= (bet_diff + raise_amount_this_street))
    					player_has_enough_money = (player_stack >= raise_amount_this_street)
    					if (player_has_enough_money and opponent_has_enough_money):
    						raise_outcome = self.heuristic_minimax(
    											self.PLAYER_TURN,
    											player_bet,
    											player_bet + raise_amount_this_street,
    											player_stack,
    											opponent_stack - bet_diff - raise_amount_this_street,
    											remaining_player_raise_this_round,
    											remaining_opponent_raise_this_round - 1,
    											remaining_raise_this_street - 1)
    					else:
    						last_raise_amount = min(opponent_stack - bet_diff, player_stack)
    						raise_outcome = self.heuristic_minimax(
    											self.PLAYER_TURN,
    											player_bet,
    											player_bet + last_raise_amount,
    											player_stack,
    											opponent_stack - bet_diff - last_raise_amount,
    											remaining_player_raise_this_round,
    											remaining_opponent_raise_this_round - 1,
    											remaining_raise_this_street - 1)
    					if raise_outcome >= best_outcome:
    						best_outcome = raise_outcome
    	return best_outcome

    def expected_outcome(self, 
    					bet_amount,
    					player_stack, 
    					opponent_stack,
    					remaining_player_raise_this_round, 
    					remaining_opponent_raise_this_round):
    	street_index = self.STREET_INDEX_DICT[self.street]
    	num_street = street_index + 1
    	num_remaining_street = self.NUM_STREET_PER_ROUND - num_street
    	avg_raise_amount_remaining_street = self.avg_raise_amount_remaining_street[street_index]
    	num_player_raise = self.NUM_RAISE_PER_ROUND_PER_PLAYER - remaining_player_raise_this_round
    	num_opponent_raise = self.NUM_RAISE_PER_ROUND_PER_PLAYER - remaining_opponent_raise_this_round
    	expected_num_player_future_raise = min(remaining_player_raise_this_round, float(num_player_raise) / num_street * num_remaining_street)
    	expected_num_opponent_future_raise = min(remaining_opponent_raise_this_round, float(num_opponent_raise) / num_street * num_remaining_street)
    	expected_increase_bet = min(player_stack, opponent_stack, (expected_num_player_future_raise + expected_num_opponent_future_raise) * avg_raise_amount_remaining_street)
    	expected_bet = bet_amount + expected_increase_bet
    	expected_value = self.evaluate_value(expected_bet, num_opponent_raise + expected_num_player_future_raise)
    	return expected_value

    def evaluate_value(self, bet_amount, num_opponent_raise):
    	if self.street == self.STREET_ZERO_CARD:
    		# To be replaced with expected value look up table
    		# value = bet_amount * self.PREFLOP_EXPECTED_VALUE[is_same_shape][first_card_number][second_card_number]
    		value = bet_amount * (2 * self.winning_probability + self.drawing_probability - 1)
    	else:
    		# E = P(W) * B - (1 - P(W) - P(D)) * B
    		value = bet_amount * (2 * self.winning_probability + self.drawing_probability - 1)
    	return value

    def re_calculate_probability(self):
    	# Trivial implementation
    	if self.street == self.STREET_ZERO_CARD:
    		self.winning_probability = 0.5
    		self.drawing_probability = 0
    	else:
    		# To be replaced with specific probability calculation
    		self.winning_probability = 0.5
    		self.drawing_probability = 0

    def pre_calculate_avg_raise_amount_remaining_street(self):
    	total_raise_amount_value = 0
    	for i in range(0, self.NUM_STREET_PER_ROUND):
    		total_raise_amount_value += self.RAISE_AMOUNT_DICT[i]
    	num_remaining_street = self.NUM_STREET_PER_ROUND
    	for i in range(0, self.NUM_STREET_PER_ROUND):
    		total_raise_amount_value -= self.RAISE_AMOUNT_DICT[i]
    		num_remaining_street -= 1
    		avg_raise_value = 0
    		if num_remaining_street != 0:
    			avg_raise_value = float(total_raise_amount_value) / num_remaining_street
    		self.avg_raise_amount_remaining_street.append(avg_raise_value)

def setup_ai():
    return Agent22Player()