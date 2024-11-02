from flask import Flask, request, render_template, jsonify, redirect, url_for
import json
from datetime import datetime
from openai import OpenAI

client = OpenAI(
    api_key='YOUR-OPENAI-API-KEY')

app = Flask(__name__)

# Store user responses and global AI feedback
responses = []
global_ai_feedback = ""


@app.route('/')
def index():
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: HTML template not found", 404



@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        global global_ai_feedback

        # Get all form data
        data = {
            # Transportation data
            'transportation': request.form.get('transportation'),
            'distance': request.form.get('distance'),

            # Energy usage
            'renewable_percentage': request.form.get('renewable_percentage'),
            'ac_hours': request.form.get('ac_hours'),

            # Consumption habits
            'plastic_items': request.form.get('plastic_items'),
            'water_consumption': request.form.get('water_consumption'),

            # Travel
            'flights_per_year': request.form.get('flights_per_year'),

            # Diet and lifestyle
            'meat_dairy_percentage': request.form.get('meat_dairy_percentage'),
            'electronics_hours': request.form.get('electronics_hours'),

            # Home efficiency
            'programmable_thermostat': request.form.get('programmable_thermostat'),
            'household_size': request.form.get('household_size'),

            # Metadata
            'timestamp': datetime.now().isoformat()
        }

        # Store the response
        responses.append(data)

        # Save to file
        try:
            with open('responses.json', 'a') as f:
                json.dump(data, f)
                f.write('\n')
        except Exception as e:
            print(f"Warning: Could not save to file - {e}")

        # Calculate impact score
        impact_score = calculate_impact_score(data)

        # Generate AI feedback with more specific prompting
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are an environmental impact analysis expert. 
                Analyze the user's data and provide specific, actionable feedback. Include:
                1. Overall impact assessment
                2. Key areas of concern
                3. Specific recommendations for improvement
                4. Potential environmental and cost savings
                Format the response with clear sections and bullet points."""},
                {"role": "user", "content": f"""
                User's Environmental Data:
                - Transportation: {data['transportation']} ({data['distance']} miles daily)
                - Renewable Energy: {data['renewable_percentage']}%
                - AC/Heating Usage: {data['ac_hours']} hours/day
                - Plastic Items Weekly: {data['plastic_items']}
                - Water Consumption: {data['water_consumption']} gallons/month
                - Flights per Year: {data['flights_per_year']}
                - Meat/Dairy Diet: {data['meat_dairy_percentage']}%
                - Electronics Usage: {data['electronics_hours']} hours/day
                - Programmable Thermostat: {data['programmable_thermostat']}
                - Household Size: {data['household_size']}

                Calculated Impact Score: {impact_score}

                Please provide a comprehensive analysis and specific recommendations."""}
            ]
        )
        print(completion.choices[0].message.content)

        # Store the feedback globally
        global_ai_feedback = completion.choices[0].message.content
        return jsonify({
            'status': 'success',
            'message': 'Data processed successfully'
        })

    except Exception as e:
        print(f"Error processing form: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def calculate_impact_score(data):
    """
    Calculate a rough environmental impact score based on the submitted data.
    Higher score means higher environmental impact.
    """
    score = 0

    try:
        # Transportation impact
        distance = float(data['distance'] or 0)
        if data['transportation'].lower() in ['car', 'automobile', 'truck']:
            score += distance * 0.404  # kg CO2 per mile
        elif data['transportation'].lower() in ['bus', 'transit']:
            score += distance * 0.14
        elif data['transportation'].lower() in ['train', 'subway', 'metro']:
            score += distance * 0.14
        elif data['transportation'].lower() in ['bicycle', 'walk', 'bike']:
            score += distance * 0

        # Energy usage impact
        renewable_percent = float(data['renewable_percentage'] or 0)
        ac_hours = float(data['ac_hours'] or 0)
        score += (100 - renewable_percent) * 0.1
        score += ac_hours * 0.5

        # Consumption impact
        plastic_items = float(data['plastic_items'] or 0)
        water_consumption = float(data['water_consumption'] or 0)
        score += plastic_items * 0.1
        score += water_consumption * 0.001

        # Travel impact
        flights = float(data['flights_per_year'] or 0)
        score += flights * 900  # Average CO2 per flight

        # Diet impact
        meat_dairy_percent = float(data['meat_dairy_percentage'] or 0)
        score += meat_dairy_percent * 0.5

        # Electronics impact
        electronics_hours = float(data['electronics_hours'] or 0)
        score += electronics_hours * 0.1

        # Home efficiency
        if data['programmable_thermostat'] == 'no':
            score += 100

        household_size = float(data['household_size'] or 1)
        score = score / household_size  # Divide by household size for per-person impact

    except Exception as e:
        print(f"Error calculating score: {e}")
        return 0

    return round(score, 2)


@app.route('/results')
def show_results():
    return redirect(url_for('end'))


@app.route('/end')
def end():
    return render_template('end.html', ai_feedback=global_ai_feedback)


@app.route('/get_responses')
def get_responses():
    """Endpoint to view all submitted responses (for debugging)"""
    return jsonify(responses)


@app.route('/clear_responses')
def clear_responses():
    """Endpoint to clear all stored responses (for debugging)"""
    global responses
    global global_ai_feedback
    responses = []
    global_ai_feedback = ""
    return "Responses and feedback cleared"



if __name__ == '__main__':
    app.run(debug=True)