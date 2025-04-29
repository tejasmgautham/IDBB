from flask import Flask, request, jsonify,render_template
import mysql.connector
# import random
#import string
import uuid
from flask_mail import Mail, Message
import requests


app = Flask(__name__)

# Database connection
db = mysql.connector.connect(
    host="",
    user="",
    password="",  # Replace with your MySQL password
    database=""
)

cursor = db.cursor()

#Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Change for other email providers
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ''  # Replace with your email
app.config['MAIL_PASSWORD'] = ''  # Use an App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
# app.config['MAIL_SERVER'] = 'smtp.email.ap-mumbai-1.oci.oraclecloud.com'
# app.config['MAIL_PORT'] = 587  # 587 for STARTTLS
# app.config['MAIL_USE_TLS'] = True  # STARTTLS
# app.config['MAIL_USE_SSL'] = False  # Ensure SSL is off if using TLS
# app.config['MAIL_USERNAME'] = 'ocid1.user.oc1..aaaaaaaa4zswntidzg2jjywqndd3hmfnbmx4ks5uz4io4mwtadjqgw3ujyjq@ocid1.tenancy.oc1..aaaaaaaa2eeffgicyik23ru764tcszp7asfxsfow3rlo7yzu6rhm67ub5stq.zs.com'  # Full username if truncated
# app.config['MAIL_PASSWORD'] = '1m;hn3AlC7:<bTp](&$7'
# app.config['MAIL_DEFAULT_SENDER'] = 'sfa@pharmit.live'

mail = Mail(app)

def generate_universal_id():
    return str(uuid.uuid4().hex)  # 32-character unique ID

@app.route("/")
def index():
    return render_template("index.html")  # Serve the HTML file

# Send Confirmation Email
def send_email(email, first_name, universal_id):
    subject = "Registration Successful!"
    body = f"""
    Hello {first_name},

    You have successfully registered on our app.
    Your unique ID (e.g., Aadhaar-like) is: {universal_id}

    Best Regards,
    Your ID_App Team
    """
    msg = Message(subject, recipients=[email])
    msg.body = body
    mail.send(msg)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    phone = data.get("phone")
    #print(type(username),username)
    #print(type(phone), phone)


    if not (username and first_name and last_name and email):
        return jsonify({"error": "All fields are required!"}), 400

    universal_id = generate_universal_id()

    try:
        # Save to your local database
        cursor.execute(
            "INSERT INTO users (username, first_name, last_name, email, phone, universal_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, first_name, last_name, email, phone, universal_id)
        )
        db.commit()

        # Send Email Confirmation
        send_email(email, first_name, universal_id)

        # Forward to App1 for Keycloak registration
        app1_response = requests.post("http://localhost:5016/register", json={
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone":phone,
            "externalId": universal_id,
        })

        if app1_response.status_code == 200:
            return jsonify({"message": "User registered successfully!"}), 201
        else:
            return jsonify({
                "error": "User saved locally, but Keycloak registration failed",
                "details": app1_response.json()
            }), 500

    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already exists!"}), 400
        
        
if __name__ == '__main__':
    port=5015
    app.run(debug=True,port=port)
