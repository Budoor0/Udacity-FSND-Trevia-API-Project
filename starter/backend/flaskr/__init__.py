import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# paginate question , 10 question per page


def paginateQuestions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    # CORS headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    # get all categories
    @app.route('/categories', methods=['GET'])
    def all_categories():
        try:
            categories_query = Category.query.all()
            categories_dictionary = {}

            for cat in categories_query:
                categories_dictionary[cat.id] = cat.type

            if len(categories_dictionary) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'categories': categories_dictionary
            })
        except:
            abort(400)

    # get all questions , 10 questions per page
    @app.route('/questions', methods=['GET'])
    def questions():

        categories_dictionary = {}
        categories_query = Category.query.all()
        for cat in categories_query:
            categories_dictionary[cat.id] = cat.type

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginateQuestions(request, selection)
        total_questions = len(selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': total_questions,
            'categories': categories_dictionary
        })

    # delete questions based on question_id

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id,
            })
        except:
            abort(422)

    # Add new questions
    @app.route('/questions', methods=['POST'])
    def new_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        if not (new_question and new_answer and new_difficulty):
            abort(400)
        try:
            newQuestion = Question(question=new_question, answer=new_answer,
                                   category=new_category, difficulty=new_difficulty)
            newQuestion.insert()
            formatted_questions = newQuestion.format()

            return jsonify({
                'success': True,
                'questionId': newQuestion.id,
                'question': formatted_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)

    # Search questions
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search_question = body.get('searchTerm')

        try:
            if search_question:
                serach_query = Question.query.order_by(Question.id).filter(
                    Question.question.ilike(f'%{search_question}%')).all()
                formatted_questions = [question.format()
                                       for question in serach_query]
                return jsonify({
                    'success': True,
                    'questions': formatted_questions,
                    'total_questions': len(serach_query)
                })
        except:
            abort(422)

    # get questions based on category
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def questions_by_category(category_id):
        try:
            category = Category.query.filter(
                Category.id == category_id).one_or_none()

            if category is None:
                abort(404)

            selection = Question.query.filter_by(category=category.id).all()
            formatted_questions = [question.format() for question in selection]

            return jsonify({
                'success': True,
                'questions': formatted_questions,
                'current_category': category_id,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(400)

    # get questions to play a quiz

    @app.route('/quizzes', methods=['POST'])
    def quizze():
        try:
            body = request.get_json()
            category = body.get('quiz_category')
            prQuestions = body.get('previous_questions')
            categoryId = int(category['id'])

            if (categoryId == 0):
                questions_query = Question.query.all()
            else:
                questions_query = Question.query.filter_by(
                    category=categoryId).filter(Question.id.notin_(prQuestions)).all()

            total_questions = len(questions_query)
            random_questions = questions_query[random.randrange(
                0, total_questions)].format() if total_questions > 0 else None

            return jsonify({
                'success': True,
                'question': random_questions
            })
        except:
            abort(400)

    # Handler errors
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(405)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method Not Allowed"
        }), 405

    @app.errorhandler(500)
    def InternalServerError(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500
    return app