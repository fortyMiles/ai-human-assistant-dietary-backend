from user_llama_model import get_person_dialog
from data_defines import UserInfo
import re


def get_recommendation(user_id, habit, fact):
    user_info = UserInfo.query.get(user_id)
    
    prompt = (f"I am a {user_info.age} year old, sex is: {user_info.gender}. I want to {user_info.goal}. "
              f"Can you give the choice of my today breakfast, lunch and dinner, give this as a list. ")

    if user_info.allergic:
        prompt = f"I am allergic to {user_info.allergic}. " + prompt
    
    if habit: 
        prompt = (f"I am from {user_info.hometown} and I love to eat {user_info.love_foods}. If you give me any food recommendation, "
                  f"please explain how similar with food I love") + prompt
    
    if fact:
        prompt = prompt + "please give me the weigh of each food and nutrition facts of them, and why should I eat these food."
    else:
        prompt = prompt + "please give me only the weight and name of each food."

    messages = [
        {"role": "system", "content": "You are a helpful health and dietary assistant. You will give advice for their healthy diet."},
        {"role": "user", "content": prompt},
                                    
    ]

    keywords = ['breakfast', 'lunch', 'dinner']

    # Create a regex pattern to split on these words, case-insensitively
    pattern = '(?i)' + '|'.join(f"\\b{keyword}\\b" for keyword in keywords)  # Apply case-insensitivity to the entire pattern

    # Split the text

    response = get_person_dialog(messages)

    parts = re.split(pattern, response)

    response = '\n'.join([f'{keyword.capitalize()}: {part}' for keyword, part in zip(keywords, parts[1:])])

    return response


if __name__ == '__main__':
    from web_api_base import app
    with app.app_context():
        print(get_recommendation(17, True, True))
        print(get_recommendation(17, False, True))
        print(get_recommendation(17, True, False))
        print(get_recommendation(17, False, False))
        print(get_recommendation(16, True, True))
        print(get_recommendation(16, False, True))
        print(get_recommendation(16, True, False))
        print(get_recommendation(16, False, False))