BASE_DIFFICULTIES = [
		(1, 'easy'),
		(2, 'hard'),
	]

class Question(MongoModel):
	QUESTION_TYPES = [
		(1, 'audio'),
		(2, 'yes/no'),
		(3, 'picture'),
	]
	question_type = fields.IntegerField(choices=QUESTION_TYPES)
	question 
	picture  
	clue 
	confirmation_answer 
	confirmation_picture
	DIFFICULTIES = BASE_DIFFICULTIES + [(3, 'mixed')]
	difficulty = (choices=DIFFICULTIES)


class RightAnswer():
	question = fields.ReferenceField(Question)
	answer


class Phrases():
	PHRASE_TYPES = [
		(1, 'right_answer'),
		(2, 'wrong_answer'),
		(3, 'offer_clue')
	]
	phrase_type = fields.IntegerField(choices=PHRASE_TYPES)
	phrase


class User():
	DIFFICULTIES = BASE_DIFFICULTIES
	identity
	state
	last_question = fields.ReferenceField(Question)
	difficulty = (choices=DIFFICULTIES)


class UserQuestion():
	user = fields.ReferenceField(User)
	question = fields.ReferenceField(Question)
	passed = fields.BooleanField()
