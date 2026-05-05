from flask import Flask, request, render_template, redirect, url_for, session
from flask_mail import Mail, Message
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired



conn = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "Batata2028",
    database = "nutriplanner"
)

cursor = conn.cursor()

app = Flask(__name__)
app.config["SECRET_KEY"] = "nutriplanner"
app.secret_key = "senhasecreta"
# Configuração do email
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = "nutriplanner@gmail.com"
app.config["MAIL_PASSWORD"] = "jsadnjheLSKDDAS"
app.config["MAIL_DEFAULT_SENDER"] = "nutriplanner@gmail.com"

mail = Mail(app)

# ---------- Translation english to portuguese ------
meal_translations = {
    "breakfast": "Café da manhã",
    "morning snack": "Lanche da manhã",
    "lunch": "Almoço",
    "afternoon snack": "Lanche da tarde",
    "dinner": "Jantar"
}

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    email = request.form.get("gmail")
    password = request.form.get("password")

    print("Email recebido:", email)
    print("Senha recebido:", password)

    cursor.execute("SELECT id, pass_hash FROM user_login WHERE email = %s", (email,))
    row = cursor.fetchone()
    if not row:
        return render_template("login.html", login_error=True)

    user_id, pass_hash = row

    if not check_password_hash (pass_hash, password):
        return render_template("login.html", login_error = True)
    
    session["user_id"] = user_id
    
    return redirect(url_for("perfil", user_id=user_id))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    email = request.form.get("gmail")
    password = request.form.get("password")
    repeat_password = request.form.get("repeat_password")

    if not email or not password or not repeat_password:
        return render_template("register.html", login_error = True)

    if password != repeat_password:
        return render_template("register.html", login_error = True)
    
    pass_hash = generate_password_hash(password)

    cursor.execute("INSERT INTO user_login (email, pass_hash) VALUES (%s, %s)", (email, pass_hash))
    user_login_id = cursor.lastrowid

    session["user_id"] = user_login_id

    return redirect(url_for("perfil"))

def to_int_or_none(value):
    if value == "":
        return None
    return float(value)

@app.route("/perfil>", methods= ["GET", "POST"])
def perfil():
    user_id = session.get("user_id")

    cursor.execute("SELECT email FROM user_login WHERE id = %s",(user_id,))
    row = cursor.fetchone()
    gmail = row[0] 

    if request.method == "GET":
        saved = request.args.get("saved") == "1"

        cursor.execute("SELECT name, birthday, height, weight, gender,goal_id, goal_pace_id, " \
        "exercise_id, principal_meal_id,eats_sweet_daily, vegetable, legumes "\
        "FROM user_profile "\
        "WHERE user_id = %s ", (user_id,))

        profile_row = cursor.fetchone()
                
        if profile_row:

            cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
            user_profile_id = cursor.fetchone()[0]

            cursor.execute("SELECT meal_id FROM user_profile_meal WHERE profile_id = %s ", (user_profile_id,))

            meal_row = cursor.fetchall()
            meal_ids= [str (row[0]) for row in meal_row]
            

            profile_information = {
                "name": profile_row[0],
                "birthday": profile_row[1],
                "height": profile_row[2],
                "weight": profile_row[3],
                "gender": profile_row[4],
                "goal_id": profile_row[5],
                "goal_pace_id": profile_row[6],
                "exercise_id": profile_row[7],
                "principal_meal_id": profile_row[8],
                "eats_sweet_daily": profile_row[9],
                "vegetable": profile_row[10],
                "legumes": profile_row[11],
                "meals" : meal_ids,
                }
                    
        else:
            profile_information = {
                "name": "",
                "birthday": "",
                "height": "",
                "weight": "",
                "gender": "",
                "goal_id": "",
                "goal_pace_id": "",
                "exercise_id": "",
                "principal_meal_id": "",
                "eats_sweet_daily": "",
                "vegetable": "",
                "legumes": "",
                "meal" : "",
            }

        return render_template(
            "perfil.html",
            gmail=gmail,
            perfil=profile_information,
            saved=saved
            )
    
    if request.method == "POST":
        cursor.execute("SELECT user_id FROM user_profile WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()

        name = request.form.get("name")
        birthday = request.form.get("birthday")
        height = to_int_or_none(request.form.get("height"))
        weight = float(request.form.get("weight")) if request.form.get("weight") not in ("", None) else None
        gender = request.form.get("gender")
        goal_id = request.form.get("goal")
        goal_pace_id= request.form.get("goal_pace")
        exercise_id = request.form.get("exercise")
        principal_meal_id = request.form.get("principal_meal")
        eats_sweet_daily = request.form.get("eats_sweet")
        vegetable = to_int_or_none(request.form.get("vegetable"))
        legumes = to_int_or_none(request.form.get("legumes"))
        meals = request.form.getlist("meals")

        if not row:
            cursor.execute("" \
            "INSERT INTO user_profile "
                "(user_id, name, birthday, height, weight, gender, " \
                "goal_id, goal_pace_id, exercise_id, principal_meal_id, eats_sweet_daily, vegetable, legumes) " \
            "VALUES " \
                "(%s, %s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s,%s)", 
            (user_id, name, birthday, height, weight, gender,goal_id, 
            goal_pace_id, exercise_id, principal_meal_id, eats_sweet_daily, vegetable, legumes))
            
            conn.commit()

            cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
            user_profile_id = cursor.fetchone()[0]

            for meal in meals:
                cursor.execute("INSERT INTO user_profile_meal (profile_id, meal_id) VALUES (%s, %s)", 
                (user_profile_id, meal))
            
            conn.commit()

        else: 
            cursor.execute("" \
            "update user_profile "
            " set name = %s, " \
                "birthday = %s, " \
                "height = %s, " \
                "weight = %s, " \
                "gender = %s, " \
                "goal_id = %s, " \
                "goal_pace_id = %s, " \
                "exercise_id = %s, " \
                "principal_meal_id = %s, " \
                "eats_sweet_daily = %s, " \
                "vegetable = %s," \
                "legumes = %s " \
            "where user_id = %s ", 
            (name, birthday, height, weight, gender,goal_id, 
            goal_pace_id, exercise_id, principal_meal_id, eats_sweet_daily, vegetable,legumes, user_id))
            
            conn.commit()

            cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
            user_profile_id = cursor.fetchone()[0]

            cursor.execute("delete from user_profile_meal where profile_id = %s", (user_profile_id,))

            for meal in meals:
                cursor.execute("insert into user_profile_meal (profile_id, meal_id ) values ( %s, %s)", 
                (user_profile_id, meal))
            conn.commit()

    return redirect(url_for("perfil", saved=1))
    
@app.route("/change_login", methods=["GET", "POST"])
def change_login():
    user_id = session.get("user_id")

    cursor.execute("SELECT email FROM user_login WHERE id = %s",(user_id,))
    primary_email = cursor.fetchone()[0] 

    if request.method == "GET":
        return render_template("change_login.html", email=primary_email)
    
    old_email = request.form.get("old_gmail")
    new_gmail = request.form.get("new_gmail")
    password = request.form.get("password")
    
    if request.method == "POST":

        cursor.execute("select pass_hash from user_login where id = %s", (user_id,))
        pass_hash = cursor.fetchone()[0]

        if old_email != primary_email:
            return redirect( url_for('change_login', email_error = True))
        
        if not check_password_hash (pass_hash, password):
            return redirect( url_for('change_login', password_error = True))
        
        cursor.execute("update user_login set email = %s where id = %s", (new_gmail, user_id,))
        conn.commit()
        
    
    return redirect(url_for("change_login", user_id=user_id, saved=1))
        
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
def generate_token(email):
    return serializer.dumps(email, salt="reset-password")

def send_email(email, token):
    link = url_for("reset_password", token=token, _external=True)
    msg = Message(
        subject="Redefinicao de Senha",
        recipients=[email]
    )
    msg.body = f"""
    Olá!
    Click no link abaixo para redefinir sua senha:
    {link}
    
    Se voce nao solicitou a redefinicao de senha ignore este email.
    """
    mail.send(msg)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")
    
    email = request.form.get("gmail")

    cursor.execute("SELECT id FROM user_login WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        token = generate_token(email)
        send_email(email, token)

    return "Se o email existir, enviamos o link."
        

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="reset-password", max_age=3600)
    except SignatureExpired:
        return "O link expirou."
    except BadSignature:
        return "Link inválido."

    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    new_password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not new_password or not confirm_password:
        return "Preencha todos os campos."

    if new_password != confirm_password:
        return "As senhas não coincidem."

    password_hash = generate_password_hash(new_password)

    cursor.execute(
        "UPDATE user_login SET password = %s WHERE email = %s",
        (password_hash, email)
    )
    conn.commit()

    return "Senha redefinida com sucesso."
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/planner", methods=["GET", "POST"])
def planner():
    user_id = session.get("user_id")
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
    user_profile_id =cursor.fetchone()["id"]

    if request.method == "GET":
        saved = request.args.get("saved") == "1"

        cursor.execute("SELECT meal.id, meal.meal_name " \
            "FROM user_profile_meal " \
            "INNER JOIN meal ON user_profile_meal.meal_id = meal.id "
            "WHERE user_profile_meal.profile_id = %s", (user_profile_id,))

        choice_meal = cursor.fetchall()     
        cursor.close()

        for meals in choice_meal:
            meals["meal_pt"] = meal_translations.get(meals["meal_name"],meals["meal_name"])

            print("meals", meals)

        """ -------------- Protein ------------"""


        return render_template("planner.html", choice_meal=choice_meal,saved=saved)


    """return render_template(
        "planner.html",
        meals=meals,
        saved=saved,
    )
"""
if __name__ == "__main__":
    import os
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)

