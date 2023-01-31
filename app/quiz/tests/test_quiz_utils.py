import pytest
from quiz.utils import score_test_attempt

pytestmark = pytest.mark.django_db

 
 #set 4 questions
 #provide correct an

def test_score_quiz_attempt(question_factory, answer_factory, quiz_factory, user_factory):
    quiz = quiz_factory(created_by = user_factory())
    
    q1 = question_factory(quiz = quiz)
    q1_correct_answer = answer_factory(question = q1, is_correct = True)
    
    q2 = question_factory(quiz = quiz)
    q2_correct_answer =  answer_factory(question = q2, is_correct = True)
    
    q3 = question_factory(quiz = quiz)
    q3_correct_answer =  answer_factory(question = q3, is_correct = True)
    
    q4 = question_factory(quiz = quiz)
    q4_correct_answer =  answer_factory(question = q4, is_correct = True)
    
    random_answers = answer_factory.create_batch(5, question=q1)
    data ={
        "submissions":
            [
                {
                    "question": q1,
                    "answer":random_answers[0]
                },
                {
                    "question": q2,
                    "answer": random_answers[0]
                },
                {
                    "question": q3,
                    "answer": q3_correct_answer
                },
                {
                    "question": q4,
                    "answer": q4_correct_answer
                }
            ]
    }
    
    result: dict = score_test_attempt(4, data)  
    assert result.get('score') == 2
    assert result.get('score_percent') == 50.0
    assert result.get('total_question') == 4
 