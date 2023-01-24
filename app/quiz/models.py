from django.db import models
from core.models import AuditableModel

class Quiz(AuditableModel):
    module = models.OneToOneField("course.Module", related_name="module_quiz", on_delete=models.CASCADE, blank=True, null=True)
    quiz_name = models.CharField(max_length=255) 
    created_by =  models.ForeignKey("user.User", related_name='created_quizzes',on_delete=models.CASCADE
	)
    
    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['id','module']
    
    @property    
    def question_count(self)->int:
        return self.questions.count()
    
    def __str__(self):
        return (self.quiz_name)
 
 
class Question(AuditableModel):
	quiz = models.ForeignKey(
		Quiz, 
		related_name='questions',
		on_delete=models.CASCADE
	)
	prompt_question = models.CharField(max_length=255, blank=True, null=True)
	has_audio = models.BooleanField(default=False)
	question_audio_record = models.FileField(storage='audio-questions/', blank=True, null=True)

	class Meta:
		ordering = ['id']

	def __str__(self):
		return self.prompt_question


class Answer(AuditableModel):
	question = models.ForeignKey(
		Question, 
		related_name='answers', 
		on_delete=models.CASCADE
	)
	text = models.CharField(max_length=255)
	is_correct = models.BooleanField(default=False)
	has_audio = models.BooleanField(default=False)
	answer_audio_record = models.FileField(storage='audio-answers/', blank=True, null=True)

	def __str__(self):
		return f'{self.text}'


class TakenQuiz(AuditableModel):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name='taken_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='taken_quizzes')
    score = models.FloatField()
    date_taken = models.DateTimeField(auto_now_add=True)
    percentage_score = models.FloatField(default=0.00)
    def __str__(self):
        return f'{self.quiz} - {self.user}'
	