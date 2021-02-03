from pymodm import MongoModel, fields, connect
import settings, random
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
	tts = fields.CharField(max_length=2048, blank=True)
	picture = fields.CharField(max_length=512)
	clue = fields.CharField(max_length=2048, blank=True)
	clue_tts = fields.CharField(max_length=2048, blank=True)
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
	YOU_HAD_CLUE_ASK = 9
	FALLBACK_1 = 10


class Phrase(MongoModel):
	PHRASE_TYPES = [a.value for a in PhraseType]
	phrase_type = fields.IntegerField(choices=PHRASE_TYPES)
	phrase = fields.CharField(max_length=2048)

	def __str__(self):
		return self.phrase_type + ' - ' + self.phrase

	@staticmethod
	def random_phrase(phrase_type):
		if isinstance(phrase_type, PhraseType):
			phrase_type = phrase_type.value
		return random.choice(list(Phrase.objects.raw({'phrase_type': phrase_type}))).phrase

	@staticmethod
	def give_you_are_right():
		return Phrase.random_phrase(PhraseType.YOU_ARE_RIGHT)

	@staticmethod
	def give_you_are_wrong():
		return Phrase.random_phrase(PhraseType.YOU_ARE_WRONG)

	@staticmethod
	def give_offer_clue():
		return Phrase.random_phrase(PhraseType.OFFER_CLUE)

	@staticmethod
	def give_greeting():
		return Phrase.random_phrase(PhraseType.GREETING)

	@staticmethod
	def give_continue_ask():
		return Phrase.random_phrase(PhraseType.CONTINUE_ASK)

	@staticmethod
	def give_next_question():
		return Phrase.random_phrase(PhraseType.NEXT_QUESTION)

	@staticmethod
	def give_next_question():
		return Phrase.random_phrase(PhraseType.NEXT_QUESTION)

	@staticmethod
	def give_new_level_congratulation():
		return Phrase.random_phrase(PhraseType.NEW_LEVEL_CONGRATULATION)

	@staticmethod
	def give_try_again():
		return Phrase.random_phrase(PhraseType.TRY_AGAIN)

	@staticmethod
	def give_you_had_clue_ask():
		return Phrase.random_phrase(PhraseType.YOU_HAD_CLUE_ASK)

	@staticmethod
	def give_fallback_1():
		return Phrase.random_phrase(PhraseType.FALLBACK_1)


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



