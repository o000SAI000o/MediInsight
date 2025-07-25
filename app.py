#Flask + SQLAlchemy Authentication System for Medinsight
from flask import Flask, render_template,request, redirect, url_for, flash, session,send_file,jsonify
from flask_sqlalchemy import SQLAlchemy
from huggingface_hub import InferenceClient
from flask_bcrypt import Bcrypt
import os
import joblib
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF


# Initialize Hugging Face client using Fireworks
chatbot_client = InferenceClient(
    provider="fireworks-ai",
    api_key=HF_TOKEN,
)


app = Flask(__name__)
app.secret_key = 'supersecretekey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#initialize DB and Bcrypt
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

tumor_model = joblib.load("models/tumor_model.pkl")
diabetes_model = joblib.load("models/diabetes_model.pkl")


#user model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # for admin panel

#Report model
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(256), nullable=False)
    model_type = db.Column(db.String(100),nullable=True)
    input_data = db.Column(db.String(256), nullable=False)
    result = db.Column(db.String(256), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
  
#create database
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin_user = User(username='admin', email='admin@example.com', password=hashed_pw, is_admin=True) #True = 1
        db.session.add(admin_user)
        db.session.commit()


    print("✅ Admin account created successfully.")
    print("✅ Database initialized successfully.")
    
# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Sign up
@app.route('/signup',methods = ['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash("Email already registered")
            return redirect(url_for('signup'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup successful. Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login
@app.route('/login',methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        print("Form data:", username, password)
        print("User from DB:", user)
        if user and bcrypt.check_password_hash(user.password,password):
            session['user'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid login credentials")
            return redirect(url_for('login'))
    return render_template('login.html')

#admin dashboard
@app.route('/admin')
def admin_dashboard():
    if 'user' not in session:
        flash("Login required")
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['user']).first()
    if not user or not user.is_admin:
        flash("Unauthorized access")
        return redirect(url_for('dashboard'))

    all_users = User.query.all()
    all_reports = Report.query.order_by(Report.timestamp.desc()).all()
    total_reports = len(all_reports)
    total_users = len(all_users)

    return render_template("admin_dashboard.html", users=all_users, reports=all_reports,
                           total_reports=total_reports, total_users=total_users)

#admin report deletion
@app.route('/admin/delete_report/<int:report_id>')
def delete_report(report_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['user']).first()
    if not user or not user.is_admin:
        flash("Unauthorized")
        return redirect(url_for('dashboard'))

    report = Report.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash("Report deleted.")
    return redirect(url_for('admin_dashboard'))


# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please log in first")
        return redirect(url_for('login'))

    user_reports = Report.query.filter_by(user=session['user']).order_by(Report.timestamp.desc()).all()

    # --- Chart Logic ---
    from collections import defaultdict
    import matplotlib.pyplot as plt
    import os

    model_data = defaultdict(lambda: {'Malignant Tumor': 0, 'Benign Tumor': 0, 'Diabetic': 0, 'Non-Diabetic': 0})

    for r in user_reports:
        if r.model_type == 'Tumor Prediction':
            model_data['Tumor'][r.result] += 1
        elif r.model_type == 'Diabetes Prediction':
            model_data['Diabetes'][r.result] += 1

    # Prepare chart
    labels = []
    benign = []
    malignant = []
    diabetic = []
    nondiabetic = []

    for model in model_data:
        labels.append(model)
        benign.append(model_data[model].get('Benign Tumor', 0))
        malignant.append(model_data[model].get('Malignant Tumor', 0))
        diabetic.append(model_data[model].get('Diabetic', 0))
        nondiabetic.append(model_data[model].get('Non-Diabetic', 0))

    x = range(len(labels))
    fig, ax = plt.subplots()
    ax.bar(x, benign, width=0.2, label='Benign Tumor', color='green')
    ax.bar([i + 0.2 for i in x], malignant, width=0.2, label='Malignant Tumor', color='red')
    ax.bar([i + 0.4 for i in x], diabetic, width=0.2, label='Diabetic', color='orange')
    ax.bar([i + 0.6 for i in x], nondiabetic, width=0.2, label='Non-Diabetic', color='blue')

    ax.set_xticks([i + 0.3 for i in x])
    ax.set_xticklabels(labels)
    ax.set_ylabel("Number of Predictions")
    ax.set_title("Prediction Result Comparison")
    ax.legend()
    plt.tight_layout()

    # Save chart
    chart_path = os.path.join("static", "compare_chart.png")
    plt.savefig(chart_path)
    plt.close()

    return render_template('dashboard.html', user=session['user'], reports=user_reports, chart_path=chart_path)

#logout
@app.route('/logout')
def logout():
    session.pop('user',None)
    flash("Logged out successfully")
    return redirect(url_for('home'))

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'error': 'No input message provided'}), 400

    try:
        completion = chatbot_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": user_input
                }
            ],
        )
        reply = completion.choices[0].message["content"]
        return jsonify({'response': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/predict/tumor',methods=['GET','POST'])
def predict_tumor():
    if 'user' not in session:
        flash("please log in first")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            size = float(request.form['size'])
            growth_rate = float(request.form['growth_rate'])
            roundness_score = float(request.form['roundness_score'])
            
            prediction = tumor_model.predict([[size,growth_rate,roundness_score]])[0]
            print("Prediction from model:", prediction)
            result = "Malignant Tumor" if prediction == 1 else "Benign Tumor"
            
            #plot chart
            fig,ax = plt.subplots()
            ax.bar(['Benign','Malignant'],[1 - prediction , prediction ], color=['green','red'])
            ax.set_title('Tumor Prediction Result')
            ax.set_ylabel('Probability')
            plt.tight_layout()
            plt.savefig('static/tumor_chart.png')
            plt.close()
            
            #save report
            new_report = Report(
                user=session['user'],
                model_type = "Tumor Prediction",
                input_data=f"size={size},growth_rate={growth_rate},roundness_score={roundness_score}",
                result=result,
                timestamp=datetime.now()
            )
            db.session.add(new_report)
            db.session.commit()
            
            return render_template('tumor_result.html', size=size, growth=growth_rate, roundness=roundness_score, result=result)

        except:
            flash("Invalid input. Please enter all fields.")
            return redirect(url_for('predict_tumor'))

    return render_template('tumor_form.html')
            
@app.route('/predict/diabetes', methods=['GET', 'POST'])
def predict_diabetes():
    if 'user' not in session:
        flash("Please log in first")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            preg = float(request.form['preg'])
            glucose = float(request.form['glucose'])
            bmi = float(request.form['bmi'])

            pred = diabetes_model.predict([[preg, glucose, bmi]])[0]
            result = "Diabetic" if pred == 1 else "Non-Diabetic"

            # Chart for prediction
            fig, ax = plt.subplots()
            ax.bar(['Non-diabetic', 'Diabetic'], [1 if pred == 0 else 0, 1 if pred == 1 else 0],
                   color=['green', 'red'])
            ax.set_title("Diabetes Prediction Result")
            ax.set_ylabel("Prediction Score")
            plt.tight_layout()

            chart_path = f"static/{session['user']}_diabetes_chart.png"
            plt.savefig(chart_path)
            plt.close()

            # Save report to DB
            new_report = Report(
                user=session['user'],
                model_type="Diabetes Prediction",
                input_data=f"preg={preg},glucose={glucose},bmi={bmi}",
                result=result,
                timestamp=datetime.now()
            )
            db.session.add(new_report)
            db.session.commit()

            return render_template('diabetes_result.html',
                                   preg=preg, glucose=glucose, bmi=bmi,
                                   result=result,
                                   chart_path=chart_path)

        except Exception as e:
            print("Error:", e)
            flash("Invalid input. Try again.")
            return redirect(url_for('predict_diabetes'))

    return render_template('diabetes_form.html')

@app.route('/chart')
def chart():
    if 'user' not in session:
        return redirect(url_for('login'))
    reports = Report.query.filter_by(user=session['user']).all()
    types = {}
    for report in reports:
        types[report.model_type] = types.get(report.model_type, 0) + 1

    fig, ax = plt.subplots()
    ax.bar(types.keys(), types.values(), color='skyblue')
    ax.set_title("Your Prediction Usage")
    ax.set_ylabel("Number of Predictions")
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/download_report/<int:report_id>')
def download_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user != session.get('user'):
        flash("Unauthorized access.")
        return redirect(url_for('dashboard'))

    # Path of chart image if it exists
    chart_path = f"static/{report.user}_diabetes_chart.png"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"MediInsight Report", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Date: {report.timestamp.strftime('%Y-%m-%d %H:%M')}", ln=2)
    pdf.cell(200, 10, txt=f"Model Type: {report.model_type}", ln=3)
    pdf.cell(200, 10, txt=f"Input Data: {report.input_data}", ln=4)
    pdf.cell(200, 10, txt=f"Result: {report.result}", ln=5)
    
    # Add chart image if it exists
    if os.path.exists(chart_path):
        pdf.image(chart_path, x=10, y=70, w=180)
    
    file_path = f"temp_report_{report.id}.pdf"
    pdf.output(file_path)
    return send_file(file_path, as_attachment=True)

@app.route('/streamlit')
def open_streamlit():
    return redirect("http://localhost:8501", code=302)
 
if __name__ == '__main__':
    app.run(debug=True,port=5050)