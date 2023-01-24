from typing import Dict, List
from rest_framework import serializers
from django.db import transaction
from user.serializers import BasicUserInfoSerializer
from core.utils.validators import is_admin
from course.serializers import CourseSerializer
from course.models import Module
from core.utils.validators import is_course_student
from user.models import User
from .models import Quiz, Question, Answer, TakenQuiz
from django.db.models.fields.files import File


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            'id',
            'text',
            'has_audio',
            'answer_audio_record',
            'is_correct',
        ]
        extra_kwargs = {
            "created_by": {"write_only": True}
        }
        model = Answer


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        fields = ['id', 'quiz', 'prompt_question',
                  'answers', 'has_audio', 'question_audio_record']
        model = Question
        extra_kwargs = {
            "quiz": {"read_only": True}
        }


class QuizCreateSerializer(serializers.Serializer):
    quiz_name = serializers.CharField(max_length=200, required=True)
    module = serializers.PrimaryKeyRelatedField(
        queryset=Module.objects.all(), required=True
    )
    created_by = BasicUserInfoSerializer(read_only=True)


    def validate(self, attrs):
        user: User = self.context["request"].user
        module: Module = attrs.get("module")
        teachers = module.course.teachers.all()
        if user not in teachers and not is_admin(user):
            raise serializers.ValidationError(
                {"module": "You can only create a quiz for a course you teach."})
        return super().validate(attrs)

    def create(self, validated_data):
        user: User = self.context["request"].user
        quiz_name: str = validated_data.get("quiz_name")
        module: Module = validated_data.get("module")
        insance = Quiz.objects.create(
            module=module, quiz_name=quiz_name, created_by=user)
        return insance


class QuizUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = "__all__"
        extra_kwargs = {
            "created_by": {"read_only": True}
        }
    
    
    def validate(self, attrs):
        user: User = self.context["request"].user
        module: Module = self.instance.module
        teachers = module.course.teachers.all()
        if user not in teachers and not is_admin(user):
            raise serializers.ValidationError(
                {"module": "You can only create/edite/delete a quiz for a course you teach."})
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class QuizSerializer(serializers.ModelSerializer):
    course = serializers.ReadOnlyField(source='module.course')

    class Meta:
        fields = [
            'id',
            'module',
            'quiz_name',
            'course',
            'question_count'
        ]
        model = Quiz

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['question_count'] = instance.question_count
        return data


class QuizDetailsSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(read_only=True, many=True)

    class Meta:
        fields = "__all__"
        model = Quiz

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class TakenQuizSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = TakenQuiz


class CreatModuleQuizQuestionSerializer(serializers.Serializer):
    questions = QuestionSerializer(write_only=True, many=True)

    def validate(self, attrs):
        user: User = self.context["request"].user
        module: Module = self.context.get('module')
        if module.quiz is None:
            raise serializers.ValidationError(
                {"module": "No quiz found for this module. Create one to continue"})
        if user not in module.course.teachers.all() and not is_admin(user):
            raise serializers.ValidationError(
                {"module": "You need to be a teacher to set questions."})
        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        quiz = self.context.get('module').module_quiz
        questions_list: List[Dict] = validated_data.get('questions')
        for question in questions_list:
            question_data = {
                'quiz': quiz,
                'prompt_question': question.get('prompt_question'),
                'has_audio': question.get('has_audio'),
                'question_audio_record': question.get('question_audio_record')

            }
            question_instance = Question.objects.create(**question_data)
            answers = [Answer(question=question_instance,
                              text=answer['text'], has_audio=answer['has_audip'],
                              answer_audio_record=answer['answer_audio_record'],
                              is_correct=answer.get('is_correct', False)
                              ) for answer in question.get('answers')]

            Answer.objects.bulk_create(answers)
        return validated_data


class BaseQuizAttemptSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(), required=True
    )
    answer = serializers.PrimaryKeyRelatedField(
        queryset=Answer.objects.all(), required=True
    )


class AttemptQuizSerializer(serializers.Serializer):
    submissions = BaseQuizAttemptSerializer(many=True, required=True)

    def validate(self, attrs):
        user: User = self.context["request"].user
        module: Module = self.context.get('module')
        is_course_student(user, module)
        if TakenQuiz.objects.filter(user=user, quiz__module=module).exists():
            raise serializers.ValidationError(
                {"module": "You are taken this quiz before"})
        return super().validate(attrs)

    def create(self, validated_data):
        user: User = self.context["request"].user
        module: Module = self.context.get('module')
        total_question_count = module.module_quiz.question_count()
        # TODO: check for zero division exception i.e. question count is zero
        score_count = 0
        submissions = validated_data.get('submissions')
        for submission in submissions:
            question: Question = submission.get('question')
            correct_answer: Answer = question.answers.filter(is_correct=True)
            if correct_answer == submission.get('answer'):
                score_count += 1

        score_percent = (score_count/total_question_count) * 100

        TakenQuiz.objects.create(user=user, quiz=module.module_quiz, score=score_count,
                                 percentage_score=score_percent)

        return {"score": score_count, 
                "score_percent": score_percent, 
                "total_question": total_question_count
                }
