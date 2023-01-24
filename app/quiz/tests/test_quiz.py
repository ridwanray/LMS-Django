import pytest
from django.urls import reverse
from rest_framework import status
from typing import Callable
from course.models import Course
from user.tests.conftest import api_client_with_credentials


pytestmark = pytest.mark.django_db


class TestCreateQuiz:
    quiz_list = reverse("quiz:quiz-list")

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_admin_create_quiz(self, user_role, course_factory, module_factory, api_client, authenticate_user):
        module = module_factory(course=course_factory())
        user = authenticate_user(roles=user_role)
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "quiz_name": "MAT 101 Quiz",
            "module": str(module.id)
        }
        response = api_client.post(
            self.quiz_list, quiz_data, format="json")
        returned_json = response.json()
        assert response.status_code == 201
        assert returned_json['quiz_name'] == "MAT 101 Quiz"
        assert returned_json['created_by']['email'] == user['user_email']

    def test_course_teacher_create_quiz(self, course_factory, module_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        course = course_factory(teachers=[user['user_instance']])
        module = module_factory(course=course)
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "quiz_name": "MAT 101 Quiz",
            "module": str(module.id)
        }
        response = api_client.post(
            self.quiz_list, quiz_data, format="json")
        returned_json = response.json()
        assert response.status_code == 201
        assert returned_json['quiz_name'] == "MAT 101 Quiz"
        assert returned_json['created_by']['email'] == user['user_email']

    def test_deny_create_quiz_to_non_course_teacher(self, course_factory, module_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        course = course_factory()
        module = module_factory(course=course)
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "quiz_name": "MAT 101 Quiz",
            "module": str(module.id)
        }
        response = api_client.post(
            self.quiz_list, quiz_data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateDeleteQuiz:

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_admin_update_quiz(self, quiz_factory, user_role, course_factory, module_factory, api_client, authenticate_user):
        module = module_factory(course=course_factory())
        user = authenticate_user(roles=user_role)
        quiz = quiz_factory(module=module, created_by=user['user_instance'])
        token = user['token']
        api_client_with_credentials(token, api_client)
        new_data = {
            "quiz_name": "Updaed MAT 101",
        }
        url = reverse("quiz:quiz-detail", kwargs={"pk": quiz.id})
        response = api_client.patch(url, new_data)
        print(response.json())
        assert response.json()['quiz_name'] == "Updaed MAT 101"

    def test_course_teacher_update_quiz(self, course_factory, quiz_factory, module_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        module = module_factory(course=course_factory(
            teachers=[user['user_instance']]))
        quiz = quiz_factory(module=module, created_by=user['user_instance'])
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "quiz_name": "Updated MAT 101",
        }
        url = reverse("quiz:quiz-detail", kwargs={"pk": quiz.id})

        response = api_client.patch(url, quiz_data)
        assert response.json()['quiz_name'] == "Updated MAT 101"

    def test_deny_course_quiz_updated_for_non_teacher(self, course_factory, quiz_factory, module_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        module = module_factory(course=course_factory())
        quiz = quiz_factory(module=module, created_by=user['user_instance'])
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "quiz_name": "Updated MAT 101",
        }
        url = reverse("quiz:quiz-detail", kwargs={"pk": quiz.id})

        response = api_client.patch(url, quiz_data)
        assert response.status_code == 404

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_admin_delete_quiz(self, user_role, course_factory, quiz_factory, module_factory, api_client, authenticate_user):
        user = authenticate_user(roles=user_role)
        module = module_factory(course=course_factory())
        quiz = quiz_factory(module=module, created_by=user['user_instance'])
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "quiz_name": "Updated MAT 101",
        }
        url = reverse("quiz:quiz-detail", kwargs={"pk": quiz.id})

        response = api_client.delete(url, quiz_data)
        assert response.status_code == 204

    def test_course_teacher_delete_quiz(self, course_factory, quiz_factory, module_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        module = module_factory(course=course_factory(
            teachers=[user['user_instance']]))
        quiz = quiz_factory(module=module, created_by=user['user_instance'])
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "quiz_name": "Updated MAT 101",
        }
        url = reverse("quiz:quiz-detail", kwargs={"pk": quiz.id})

        response = api_client.delete(url, quiz_data)
        assert response.status_code == 204

    def test_deny_delete_quiz_to_non_course_teacher(self, course_factory, quiz_factory, module_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        module = module_factory(course=course_factory())
        quiz = quiz_factory(module=module, created_by=user['user_instance'])
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "quiz_name": "Updated MAT 101",
        }
        url = reverse("quiz:quiz-detail", kwargs={"pk": quiz.id})

        response = api_client.delete(url, quiz_data)
        assert response.status_code == 404


class TestModuleQuizQuestions:

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_admin_set_module_quiz_questions(self, user_role, course_factory, quiz_factory, module_factory, api_client, authenticate_user):
        user = authenticate_user(roles=user_role)
        module = module_factory(course=course_factory())
        quiz_factory(module=module, created_by=user['user_instance'])
        token = user['token']
        api_client_with_credentials(token, api_client)
        quiz_data = {
            "questions": [
                {
                    "prompt_question": "What is your name?",
                    "answers": [
                        {
                            "text": "string",
                            "has_audio": True,
                            "is_correct": True
                        }
                    ],
                    "has_audio": True,
                   
                }
            ]
        }
        url = reverse("quiz:quiz-set-module-quiz-questions",
                      kwargs={"module_id": str(module.id)})

        response = api_client.post(url, quiz_data)
        print(response.json())
