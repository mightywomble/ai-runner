from flask import render_template, request, jsonify
from . import bp
from config import Config
import google.generativeai as genai
import openai

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Home')

@bp.route('/generate-script', methods=['POST'])
def generate_script():
    data = request.get_json()
    prompt = data.get('prompt')
    script_type = data.get('script_type')
    ai_provider = data.get('ai_provider')
    
    if not prompt or not script_type or not ai_provider:
        return jsonify({'error': 'Missing required data.'}), 400

    app_config = Config.get_app_config()
    full_prompt = f"Generate a {script_type} script that does the following: {prompt}. The script should be complete, correct, and ready to run. Only output the code itself, with no explanation or markdown formatting."

    try:
        if ai_provider == 'gemini':
            api_key = app_config.get('gemini_api_key')
            if not api_key:
                return jsonify({'error': 'Gemini API key is not configured in settings.'}), 500
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(full_prompt)
            script = response.text

        elif ai_provider == 'chatgpt':
            api_key = app_config.get('chatgpt_api_key')
            if not api_key:
                return jsonify({'error': 'ChatGPT API key is not configured in settings.'}), 500
            
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that only provides code."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            script = response.choices[0].message.content

        else:
            return jsonify({'error': 'Invalid AI provider.'}), 400
            
        return jsonify({'script': script})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
