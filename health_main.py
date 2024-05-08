from data_defines import db, app, UserInfo, Recommendations
from flask import request, jsonify, render_template
from get_recommendation import get_recommendation
from sqlalchemy import func
import numpy as np
import os

# Routes


@app.route('/userinfo/', methods=['POST'])
def manage_user_info():
    data = request.get_json()
    user_id = data.get('user_id')

    # Remove weight and height from the data
    if 'weight' in data:
        del data['weight']
    if 'height' in data:
        del data['height']

    if user_id is not None:
        user = UserInfo.query.get(user_id)
        if user:
            # Update existing user
            for key, value in data.items():
                if value is None or str(value).lower() == 'null' or(str(value).lower() == 'none') or str(value) == '':
                    continue
                setattr(user, key, value)
            db.session.commit()
            return jsonify({"message": "User updated successfully", "user_id": user.user_id}), 200
        else:
            return jsonify({"error": "User not found"}), 404
    else:
        # Create new user
        user = UserInfo(**data)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User created successfully", "user_id": user.user_id}), 201


@app.route('/userinfo', methods=['GET'])
def user_info():
    users = UserInfo.query.all()
    return jsonify([user.__dict__ for user in users]), 200


@app.route('/recommendation/', methods=['POST', 'PUT'])
def recommendations():
    if request.method == 'POST':
        data = request.get_json()
        user_id = data['user_id']
        habit = data['based_on_habits']
        fact = data['based_on_function_facts']

        content = get_recommendation(user_id, habit, fact)
        data['content'] = content
        data['save'] = False

        recommendation = Recommendations(**data)
        db.session.add(recommendation)
        db.session.commit()
        return jsonify({
            "recommendation_id": recommendation.recommendation_id,
            "content": content
        }), 201


@app.route('/recommendation/save/', methods=['PUT'])
def save_recommendation():
    if request.method == 'PUT':
        data = request.get_json()
        recommendation_id = data['recommendation_id']
        recommendation = Recommendations.query.get(recommendation_id)
        if not recommendation:
            return jsonify({"error": "Recommendation not found"}), 404
        recommendation.save = True
        db.session.commit()
        return jsonify({"message": "Recommendation save successfully", "recommendation_id": recommendation.recommendation_id}), 200


def recommendation_to_dict(recommendation):
    return {
        "recommendation_id": recommendation.recommendation_id,
        "user_id": recommendation.user_id,
        "datetime": recommendation.datetime.isoformat() if recommendation.datetime else None,
        "content": recommendation.content,
        "based_on_habits": recommendation.based_on_habits,
        "based_on_function_facts": recommendation.based_on_function_facts,
        "rank": 1 if recommendation.rank is None else recommendation.rank,
        "rate": 0 if recommendation.rate is None else recommendation.rate,
        "save": recommendation.save
    }


@app.route('/recommendation/user/<int:user_id>/', methods=['GET'])
def recommendation_info_by_id(user_id):
    subquery = db.session.query(
        Recommendations.based_on_habits,
        Recommendations.based_on_function_facts,
        func.max(Recommendations.datetime).label('max_datetime')
    ).filter(
        Recommendations.user_id == user_id,
        Recommendations.save == True
    ).group_by(
        Recommendations.based_on_habits,
        Recommendations.based_on_function_facts
    ).subquery()

    # Main query to fetch the records
    results = db.session.query(Recommendations).join(
        subquery,
        (Recommendations.based_on_habits == subquery.c.based_on_habits) &
        (Recommendations.based_on_function_facts == subquery.c.based_on_function_facts) &
        (Recommendations.datetime == subquery.c.max_datetime)
    ).filter(
        Recommendations.user_id == user_id,
        Recommendations.save == True
    ).all()

    # results = db.session.query(Recommendations).filter(
    #     Recommendations.user_id == user_id,
    #     Recommendations.save == True
    # ).all()

    recommendations_dict_list = sorted([recommendation_to_dict(rec) for rec in results], key=lambda x: x['rank'])

    return jsonify(recommendations_dict_list)


@app.route('/update_recommendations/rank/', methods=['POST'])
def update_recommendations():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    responses = []
    index = 0
    for item in data:
        recommendation = Recommendations.query.filter_by(recommendation_id=item.get('recommendation_id')).first()
        if recommendation:
            # Update existing recommendation
            index += 1
            for key, value in item.items():
                # Prevent updating primary key and ensure key exists in the model
                if key in recommendation.__table__.columns.keys() and key != 'recommendation_id':
                    if key =='rank':
                        value = int(index)
                        setattr(recommendation, key, value)
            db.session.commit()
            responses.append({"recommendation_id": recommendation.recommendation_id, "status": "updated"})
        else:
            responses.append({"recommendation_id": item.get('recommendation_id'), "status": "not found"})

    return jsonify(responses)


@app.route('/update_recommendations/rate/', methods=['POST'])
def update_recommendations_rate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    responses = []
    index = 0
    for item in data:
        recommendation = Recommendations.query.filter_by(recommendation_id=item.get('recommendation_id')).first()
        if recommendation:
            # Update existing recommendation
            index += 1
            for key, value in item.items():
                # Prevent updating primary key and ensure key exists in the model
                if key in recommendation.__table__.columns.keys() and key != 'recommendation_id':
                    if key =='rate':
                        setattr(recommendation, key, value)
            db.session.commit()
            responses.append({"recommendation_id": recommendation.recommendation_id, "status": "updated"})
        else:
            responses.append({"recommendation_id": item.get('recommendation_id'), "status": "not found"})

    return jsonify(responses)


def generate_type(habit, function):
    return f"habit({'Y' if habit else 'N'}) function({'Y' if function else 'N'})"


# Function to calculate statistics for rate and rank
def get_survey_data():
    combinations = [(False, False), (False, True), (True, False), (True, True)]
    rate_results = []
    rank_results = []

    result_num = 0

    for habit, function in combinations:
        # Querying rates for current combination
        rates = db.session.query(Recommendations.rate).filter(
            Recommendations.based_on_habits == habit,
            Recommendations.based_on_function_facts == function
        ).all()

        rates = [rate[0] for rate in rates if rate[0] is not None]
        result_num += len(rates)

        # Calculating mean and std dev for rates

        if rates:
            mean_rate = np.mean(rates)
            std_dev_rate = np.std(rates)
        else:
            mean_rate, std_dev_rate = 0, 0

        rate_results.append({
            "type": generate_type(habit, function),
            "mean": mean_rate,
            "std": std_dev_rate
        })

        # Querying ranks for current combination
        ranks = db.session.query(Recommendations.rank).filter(
            Recommendations.based_on_habits == habit,
            Recommendations.based_on_function_facts == function
        ).all()
        ranks = [rank[0] for rank in ranks if rank[0] is not None]

        # Calculating top1 and top2 percentages
        total_ranks = len(ranks)
        if total_ranks > 0:
            top1_count = ranks.count(1)
            top2_count = sum(1 for rank in ranks if rank <= 2)
            top1_percent = (top1_count / total_ranks) * 100
            top2_percent = (top2_count / total_ranks) * 100
        else:
            top1_percent, top2_percent = 0, 0

        rank_results.append({
            "type": generate_type(habit, function),
            "top1 %": top1_percent,
            "top2 %": top2_percent
        })

    return {"num": result_num, "rate": rate_results, "rank": rank_results}


@app.route('/survey/', methods=['GET'])
def survey_data():
    survey_results = get_survey_data()
    return jsonify(survey_results)


@app.route('/result/', methods=['GET'])
def result():
    return render_template('survey.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
