from typing import Dict
from user.models import User
from course.models import Module
from .models import Question, Answer, TakenQuiz


def score_test_attempt(questions_count:int, validated_data: Dict):
    score = 0
    submissions = validated_data.get('submissions')    
    for submission in submissions:
        question: Question = submission.get('question')
        correct_answer: Answer = question.answers.filter(is_correct=True)
        if correct_answer:
            if correct_answer[0] == submission.get('answer'):
                score += 1
    
    score_percent = (score/questions_count) * 100

    data_dict = {"score": score, 
                "score_percent": score_percent, 
                "total_question": questions_count
                }
    
    return data_dict

