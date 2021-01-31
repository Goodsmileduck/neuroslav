from pymodm import MongoModel, fields, connect
import settings
from enum import Enum, unique

# Establish a connection to the database.
connect('mongodb://' + settings.DB_HOST + ':' + str(settings.DB_PORT) + '/' + settings.DB_NAME)

BASE_DIFFICULTIES = [
		(1, 'easy'),
		(2, 'hard'),
	]
MIXED_DIFFICULTY = 3

LEVELS = {
	0: 'Новичок',
	3: 'Купец',
	6: 'Боярин',
	10: 'Приказчик',
	15: 'Дворянин',
	20: 'Вельможа',
	25: 'Мудрец',
	30: 'Старец',
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

	DIFFICULTIES = BASE_DIFFICULTIES + [(MIXED_DIFFICULTY, 'mixed')]
	difficulty = fields.IntegerField(choices=DIFFICULTIES)
	right_answers = fields.EmbeddedDocumentListField('Answer')
	possible_answers = fields.EmbeddedDocumentListField('Answer', blank=True)

	def __str__(self):
		return self.question


class Answer(MongoModel):
	answer = fields.CharField(max_length=512)

	def __str__(self):
		return self.answer


@unique
class PhraseType(Enum):
	YOU_ARE_RIGHT = 1
	YOU_ARE_WRONG = 2
	OFFER_CLUE = 3
	GREETING = 4
	CONTINUE_ASK = 5
	NEXT_QUESTION = 6
	NEW_LEVEL_CONGRATULATION = 7
	TRY_AGAIN = 8


class Phrase(MongoModel):
	PHRASE_TYPES = [a.value for a in PhraseType]
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
		# Returns a tuple: (BOOL: if user's just gained new level, STR: level of user, INT: points)
		points = self.points()
		return points in LEVELS.keys(), self.level(), points


class UserQuestion(MongoModel):
	user = fields.ReferenceField(User)
	question = fields.ReferenceField(Question)
	passed = fields.BooleanField()



