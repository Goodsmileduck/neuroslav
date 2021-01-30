from pymodm import MongoModel, fields, connect
import settings

# Establish a connection to the database.
connect('mongodb://' + settings.DB_HOST + ':' + str(settings.DB_PORT) + '/' + settings.DB_NAME)

BASE_DIFFICULTIES = [
		(1, 'easy'),
		(2, 'hard'),
	]

LEVELS = {
	0: 'Новичок',
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
	id = fields.IntegerField(primary_key=True)
	question_type = fields.IntegerField(choices=QUESTION_TYPES)
	question = fields.CharField(max_length=2048)
	picture = fields.CharField(max_length=512)
	clue = fields.CharField(max_length=2048, blank=True)
	interesting_fact = fields.CharField(max_length=2048, blank=True)
	confirmation_picture = fields.CharField(max_length=512)

	DIFFICULTIES = BASE_DIFFICULTIES + [(3, 'mixed')]
	difficulty = fields.IntegerField(choices=DIFFICULTIES)
	right_answers = fields.EmbeddedDocumentListField('Answer')
	possible_answers = fields.EmbeddedDocumentListField('Answer', blank=True)

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
		(3, 'offer_clue'),
		(4, 'greeting_ask'),
		(5, 'continue_ask'),
		(6, 'next_question'),
		(7, 'new_level_congratulation'),
		(8, 'try_again'),
	]
	phrase_type = fields.IntegerField(choices=PHRASE_TYPES)
	phrase = fields.CharField(max_length=2048)

	def __str__(self):
		return self.phrase_type + ' - ' + self.phrase


class User(MongoModel):
	DIFFICULTIES = BASE_DIFFICULTIES
	application_id = fields.CharField(max_length=128)
	state = fields.CharField(max_length=128)
	last_question = fields.ReferenceField(Question)
	difficulty = fields.IntegerField(choices=DIFFICULTIES)

	def points(self):
		points = UserQuestion.objects.raw({'user': self._id, 'passed': True}).count()
		return points

	def level(self):
		points = self.points()
		for i in list(LEVELS.keys())[::-1]:
			if points >= i:
				return LEVELS[i]
		return None

	def gained_new_level(self):
		# Returns a pair: (BOOL: if user's just gained new level, STR: level of user)
		if self.points() in LEVELS.keys():
			return True, self.level()
		else:
			return False, self.level()


class UserQuestion(MongoModel):
	user = fields.ReferenceField(User)
	question = fields.ReferenceField(Question)
	passed = fields.BooleanField()



