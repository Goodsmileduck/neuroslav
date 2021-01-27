from pymodm import MongoModel, fields, connect

# Establish a connection to the database.
connect('mongodb://localhost: ... ')

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
	question = fields.CharField(max_length=2048)
	picture = fields.CharField(max_length=512)
	clue = fields.CharField(max_length=2048)
	confirmation_answer = fields.CharField(max_length=2048)
	confirmation_picture = fields.CharField(max_length=512)
	DIFFICULTIES = BASE_DIFFICULTIES + [(3, 'mixed')]
	difficulty = fields.IntegerField(choices=DIFFICULTIES)


class RightAnswer(MongoModel):
	question = fields.ReferenceField(Question)
	answer = fields.CharField(max_length=512)


class Phrases(MongoModel):
	PHRASE_TYPES = [
		(1, 'right_answer'),
		(2, 'wrong_answer'),
		(3, 'offer_clue')
	]
	phrase_type = fields.IntegerField(choices=PHRASE_TYPES)
	phrase = fields.CharField(max_length=2048)


class User(MongoModel):
	DIFFICULTIES = BASE_DIFFICULTIES
	identity = fields.CharField(max_length=128)
	state = fields.CharField(max_length=128)
	last_question = fields.ReferenceField(Question)
	difficulty = fields.IntegerField(choices=DIFFICULTIES)


class UserQuestion(MongoModel):
	user = fields.ReferenceField(User)
	question = fields.ReferenceField(Question)
	passed = fields.BooleanField()


LEVELS = {
	5: 'Купец',
	10: 'Дворянин',
	15: 'Вельможа',
	20: 'Мудрец',
}
