from pymodm import MongoModel, fields, connect
import settings

# Establish a connection to the database.
connect('mongodb://' + settings.DB_HOST + ':' + str(settings.DB_PORT) + '/' + settings.DB_NAME)

BASE_DIFFICULTIES = [
		(1, 'easy'),
		(2, 'hard'),
	]

LEVELS = {
	5: 'Купец',
	10: 'Дворянин',
	15: 'Вельможа',
	20: 'Мудрец',
}


class Question(MongoModel):
	QUESTION_TYPES = [
		(1, 'audio'),
		(2, 'yes/no'),
		(3, 'picture'),
	]
	id = fields.IntegerField()
	question_type = fields.IntegerField(choices=QUESTION_TYPES)
	question = fields.CharField(max_length=2048)
	picture = fields.CharField(max_length=512)
	clue = fields.CharField(max_length=2048)
	confirmation_answer = fields.CharField(max_length=2048)
	confirmation_picture = fields.CharField(max_length=512)
	DIFFICULTIES = BASE_DIFFICULTIES + [(3, 'mixed')]
	difficulty = fields.IntegerField(choices=DIFFICULTIES)
	right_answers = fields.EmbeddedDocumentListField('Answer')
	possible_answers = fields.EmbeddedDocumentListField('Answer')

	def __str__(self):
		return self.question


class Answer(MongoModel):
	answer = fields.CharField(max_length=512)

	def __str__(self):
		return self.answer


class Phrase(MongoModel):
	PHRASE_TYPES = [
		(1, 'right_answer'),
		(2, 'wrong_answer'),
		(3, 'offer_clue')
	]
	phrase_type = fields.IntegerField(choices=PHRASE_TYPES)
	phrase = fields.CharField(max_length=2048)

	def __str__(self):
		return self.phrase_type + ' - ' + self.phrase


class User(MongoModel):
	DIFFICULTIES = BASE_DIFFICULTIES
	identity = fields.CharField(max_length=128)
	state = fields.CharField(max_length=128)
	last_question = fields.EmbeddedDocumentField(Question)
	difficulty = fields.IntegerField(choices=DIFFICULTIES)

	def points(self):
		points = self.user_question_set.raw({'passed': True}).count()  # ???
		return points

	def level(self):
		points = self.points
		for i in list(LEVELS.keys())[::-1]:
			if points >= i:
				return LEVELS[i]
		return None


class UserQuestion(MongoModel):
	user = fields.ReferenceField(User)
	question = fields.ReferenceField(Question)
	passed = fields.BooleanField()



