import os
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import calculos
from datetime import date, datetime
import json
from mysql.connector import IntegrityError

app = Flask(__name__)

load_dotenv()
def get_connection():
    conn = mysql.connector.connect(
        host = os.getenv("DB_HOST", "zephyr.proxy.rlwy.net"),
        user = os.getenv("DB_USER", "root"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv("DB_NAME", "railway"),
        port = int(os.getenv("DB_PORT", 16836)),
        ssl_disabled=True
    )
    return conn

conn = get_connection()
cursor = conn.cursor(dictionary=True)
@app.route("/")
def index():
    return redirect("/nutriplanner")

@app.route("/nutriplanner")
def nutriplanner():
    return  render_template("nutriplanner.html")
    
# segurança
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# email
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

print("SECRET_KEY:", os.getenv("SECRET_KEY"))
print("MAIL_USERNAME:", os.getenv("MAIL_USERNAME"))
print("SECRET_KEY exists?", os.getenv("SECRET_KEY") is not None)
print("MAIL_USERNAME exists?", os.getenv("MAIL_USERNAME") is not None)
print("All env keys sample:", [k for k in os.environ.keys() if "MAIL" in k or "SECRET" in k or "DB" in k])
mail = Mail(app)

# ---------- Translation english to portuguese ------
meal_translations = {
    "breakfast": "Café da manhã",
    "morning snack": "Lanche da manhã",
    "lunch": "Almoço",
    "afternoon snack": "Lanche da tarde",
    "dinner": "Jantar"
}
meal_map = {
    1: "Café da manhã",
    2: "Lanche da manhã",
    3: "Almoço",
    4: "Lanche da tarde",
    5: "Jantar"
}

#-----------------------
@app.route("/login", methods=["GET","POST"])
def login():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == "GET":
        return render_template("login.html")
    
    email = request.form.get("gmail")
    password = request.form.get("password")


    cursor.execute("SELECT id, pass_hash FROM user_login WHERE email = %s", (email,))
    row = cursor.fetchone()
    # ----------- if not exist -----------
    if not row:
        return render_template("login.html", login_error=True)

    user_id = row["id"]
    pass_hash = row["pass_hash"]
    # ----------- if not check with the pass_hash -----------
    if not check_password_hash (pass_hash, password):
        return render_template("login.html", login_error = True)
    
    session["user_id"] = user_id
    
    return redirect(url_for("menu", user_id=user_id))

#------------------ REGISTER -------------------
@app.route("/register", methods=["GET","POST"])
def register():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

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
    conn.commit()
    user_login_id = cursor.lastrowid

    session["user_id"] = user_login_id
    conn.commit()
    return redirect(url_for("perfil"))

# -------- FUNCTION OF STRING TO INT --------
def to_int_or_none(value):
    if value == "":
        return None
    return float(value)

@app.route("/menu/",methods= ["GET", "POST"])
def menu():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = session.get("user_id")
    
    cursor.execute("SELECT name FROM user_profile WHERE user_id = %s",(user_id,))
    row = cursor.fetchone()
    
    if not row:
        return redirect(url_for("perfil"))

    primary_name = row["name"]
    name = primary_name.split()[0]
    session["name"] = name
    
    return render_template("menu.html", name=name)

#------------- PERFIL ---------------
@app.route("/perfil/", methods= ["GET", "POST"])
def perfil():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = session.get("user_id")

    saved = request.args.get("saved") == "1"

    cursor.execute("SELECT email FROM user_login WHERE id = %s",(user_id,))
    row = cursor.fetchone()
    gmail = row["email"] 

    if request.method == "GET":
        #----------- IF PERFIL ALRED EXIST RETURN VALUES ------------------
        cursor.execute("SELECT name, birthday, height, weight, gender,goal_id, goal_pace_id, " \
        "exercise_id, principal_meal_id,eats_sweet_daily, vegetable, legumes "\
        "FROM user_profile "\
        "WHERE user_id = %s ", (user_id,))
        profile_row = cursor.fetchone()
        
                
        if profile_row:
            primary_name = profile_row["name"]
            name = primary_name.split()[0].capitalize()
            cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
            user_profile_id = cursor.fetchone()
            user_profile_id = user_profile_id["id"]
            

            cursor.execute("SELECT meal_id FROM user_profile_meal WHERE profile_id = %s ", (user_profile_id,))

            meal_row = cursor.fetchall()
            
            meal_ids= [str (row["meal_id"]) for row in meal_row]

            profile_information = {
                "name": profile_row['name'],
                "birthday": profile_row['birthday'],
                "height": profile_row['height'],
                "weight": profile_row['weight'],
                "gender": profile_row['gender'],
                "goal_id": profile_row['goal_id'],
                "goal_pace_id": profile_row['goal_pace_id'],
                "exercise_id": profile_row['exercise_id'],
                "principal_meal_id": profile_row['principal_meal_id'],
                "eats_sweet_daily": profile_row['eats_sweet_daily'],
                "vegetable": profile_row['vegetable'],
                "legumes": profile_row['legumes'],
                "meals" : meal_ids,
                }
        #----------- ELSE DON'T EXIST RETURN EMPTY ---------            
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
            saved=saved,
            name=name
            )
    
    if request.method == "POST":
        # --------- SEND INFORMATION TO DATABANK ----------
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

        # ---------- IF THE USER IS NEW ---------------
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
            user_profile_id = cursor.fetchone()
            user_profile_id = user_profile_id["id"]
            for meal in meals:
                cursor.execute("INSERT INTO user_profile_meal (profile_id, meal_id) VALUES (%s, %s)", 
                (user_profile_id, meal))
            
            conn.commit()

        # ----------- IF THE USER WANT TO UPDATE ----------
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
            user_profile_id = cursor.fetchone()
            user_profile_id = user_profile_id["id"]

            cursor.execute("delete from user_profile_meal where profile_id = %s", (user_profile_id,))

            for meal in meals:
                cursor.execute("insert into user_profile_meal (profile_id, meal_id ) values ( %s, %s)", 
                (user_profile_id, meal))
            conn.commit()

    return redirect(url_for("perfil", saved=1, name=name))

# ----------- CHANGE EMAIL ------------    
@app.route("/change_login", methods=["GET", "POST"])
def change_login():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = session.get("user_id")

    cursor.execute("SELECT email FROM user_login WHERE id = %s",(user_id,))
    primary_email = cursor.fetchone()["email"]

    if request.method == "GET":
        return render_template("change_login.html", email=primary_email)
    
    old_email = request.form.get("old_gmail")
    new_gmail = request.form.get("new_gmail")
    password = request.form.get("password")
    
    if request.method == "POST":

        cursor.execute("select pass_hash from user_login where id = %s", (user_id,))
        pass_hash = cursor.fetchone()['pass_hash']

        if old_email != primary_email:
            return redirect( url_for('change_login', email_error = True))
        
        if not check_password_hash (pass_hash, password):
            return redirect( url_for('change_login', password_error = True))
        
        cursor.execute("update user_login set email = %s where id = %s", (new_gmail, user_id,))
        conn.commit()
        
    
    return redirect(url_for("change_login", user_id=user_id, saved=1))

# ---------- CHANGE PASSWORD WITH TOKEN -------       
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
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
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

# ---------- LOGOUT SITE --------    
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("nutriplanner"))

# --------------- PLANNER FOOD --------
@app.route("/manager_meals", methods=["GET"])
def manager_meals():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = request.args.get("error")
    user_id = session.get("user_id")

    cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
    user_profile_id =cursor.fetchone()["id"]

    if request.method == "GET":
        saved = request.args.get("saved") == "1"

        #-------------- SELECT THE USER'S MEALS CHOICES ------------
        cursor.execute("SELECT meal.id, meal.meal_name " \
            "FROM user_profile_meal " \
            "INNER JOIN meal ON user_profile_meal.meal_id = meal.id "
            "WHERE user_profile_meal.profile_id = %s", (user_profile_id,))

        choice_meal = cursor.fetchall()     

        for meals in choice_meal:
            meals["meal_pt"] = meal_translations.get(meals["meal_name"],meals["meal_name"])



        # ------------ SELECT THE GROUPS NAMES IN DB --------------
        cursor.execute("SELECT id, name FROM group_name")
        groups = cursor.fetchall()

        # --------------- SELECT SUBGROUPS WITH GROUP NAME AND WITHOUT ----------
        groups_subgroups = {}
        for row in groups:
            id_query = row['id']
            name = row['name']
            cursor.execute("SELECT id, name " \
            "FROM subgroup " \
            "WHERE group_name_id = %s ", (id_query,))
            groups_subgroups[name] = cursor.fetchall()   

        # ------------ SELECT THE SUBGROUPS NAMES IN DB --------------
        cursor.execute("SELECT id, name FROM subgroup")
        subgroups = cursor.fetchall()

        # ------------------ SELECT FOODS WITH SUBGROUP NAME -------------
        foods = {}
        for row in subgroups:
            id_subgroup = row['id']
            name_food = row['name']
            cursor.execute("SELECT id, name " \
            "FROM food " \
            "WHERE subgroup_id = %s ", (id_subgroup, ))
            foods[id_subgroup] = cursor.fetchall()

        # ---------------- SELECT FOOD_METHODS id's  ----------------------
        cursor.execute("SELECT id, food_id, method_id FROM food_method")
        id_food_method = cursor.fetchall()
       
        # ---------------- SELECT FOOD METHODS ----------------------       
        methods_food = {}
        
        for row in id_food_method:

            id_food_methods = row['id']
            food_id = row['food_id'] 
            method_id = row['method_id']

            cursor.execute("SELECT id, name FROM method WHERE id = %s", (method_id,))
            methods_name = cursor.fetchone()

            if food_id not in methods_food:
                methods_food[food_id] = []

            methods_food[food_id].append(methods_name)

        return render_template("manager_meals.html", choice_meal=choice_meal, groups_subgroups=groups_subgroups, foods=foods, methods_food=methods_food ,saved=saved,error=error)

@app.route("/salvar_planejamento", methods=["GET", "POST"])
def salvar_planejamento():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = session.get("user_id")


    cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
    user_profile_id =cursor.fetchone()['id']

    select_foods = {}
    choice_list = {}
    temp_pair = {}
    for key, value in request.form.items():
        category = key.split("_")[0]
        if category == 'sub':
            continue
        elif category == "choice":
            choice_list[category]=value
            continue
        elif category not in temp_pair:
            temp_pair[category]=[]
            
        temp_pair[category].append(value)

        if len(temp_pair[category]) == 2:
            food_id = temp_pair[category][0]
            method_id = temp_pair[category][1]
            cursor.execute("SELECT id FROM food_method WHERE food_id = %s and method_id = %s", (food_id, method_id,))
            row = cursor.fetchone()

            if not row:
                continue

            row_id = row['id']

            if category not in select_foods:
                    select_foods[category] = []
            
            select_foods[category].append(row_id)
            temp_pair = {}
    number = 0
    
    choice = choice_list["choice"]

    # -------- CRIA SIGNATURE --------
    all_foods = []

    for foods in select_foods.values():
        all_foods.extend(foods)

    all_foods = [f for f in all_foods if f != 0]

    all_foods.sort()

    meal_signature = "|".join(map(str, all_foods))

    # ------ insert id_profile ---------
    try:
        cursor.execute("INSERT INTO history_meal (user_profile_id, choice,meal_signature) VALUES (%s, %s, %s)", (user_profile_id,choice,meal_signature))
        conn.commit()
        history_meal_id = cursor.lastrowid
    except IntegrityError:
        return redirect(url_for(
                "manager_meals",
                error="duplicate"
                ))
    for key, value in select_foods.items():
        if key == 'choice':
            continue
        else:
            for food_id in value:
                number += 1
                food_number = "food" + "_"+ str(number)

                query = f""" UPDATE history_meal SET {food_number} = %s WHERE id = %s"""

                cursor.execute(query, (food_id, history_meal_id))
        conn.commit()
    
    return redirect(url_for("manager_meals",saved=1))

@app.route("/planner_meals", methods=["GET", "POST"])
def planner_meals():
    conn = get_connection()
    user_id = session.get("user_id")
    cursor = conn.cursor(dictionary=True)

    saved = request.args.get("saved") == "1"

    cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
    user_profile_id =cursor.fetchone()["id"]

    #-------------- SELECT THE USER'S MEALS CHOICES ------------
    cursor.execute("SELECT meal.id, meal.meal_name " \
        "FROM user_profile_meal " \
        "INNER JOIN meal ON user_profile_meal.meal_id = meal.id "
        "WHERE user_profile_meal.profile_id = %s", (user_profile_id,))

    choice_meal = cursor.fetchall()     

    for meals in choice_meal:
        meals["meal_pt"] = meal_translations.get(meals["meal_name"],meals["meal_name"])

    
    # ---------- SELECT LINE OF THE USER ------------

    cursor.execute("""
        SELECT * FROM history_meal
        WHERE user_profile_id = %s """, (user_profile_id,))
    meal_history = cursor.fetchall()
    

    # ------------ DATABASE MANIPULATION ----------
    organize_meals = {}
    list_grocery = {}
    for row in meal_history:
        history_meal_id = row['id']
        choice_id = row['choice']

        #-------- if choice not yet in dictionary --------
        if choice_id not in organize_meals:
            organize_meals[choice_id]= []
        

        #------------ CREATE GROCERY LIST ----------
        grocery_list=[]
        
        for grocery, value in row.items():
            if grocery.startswith("food_") and value not in (None, 0):
                #--- TRANSLATE GROCERRY LIST FROM DATA TO WORDS -----
                cursor.execute("SELECT food_id, method_id FROM food_method WHERE id = %s", (value,))
                key = cursor.fetchone()
                key_food = key["food_id"]
                method_id = key["method_id"]
                cursor.execute("SELECT name FROM food WHERE id = %s",(key_food,))
                food_name = cursor.fetchone()["name"]
                cursor.execute("SELECT name FROM method WHERE id = %s", (method_id,))
                method_name = cursor.fetchone()["name"]
                grocery = food_name + " " + method_name
                grocery_list.append({    
                    "food_method_id": value,
                    "name": grocery})
                

                list_grocery[value] = food_name
        organize_meals[choice_id].append({ 
            "history_meal_id":history_meal_id,
            "foods":grocery_list
        })
    session["organize_meals"] = organize_meals
    session["list_grocery"] = list_grocery
    if request.method == "POST":
        selected_meals = request.form.getlist("selected_meals")
        action = request.form.get("action")
        session["selected_meals"] = selected_meals

        if action == "delete":
            placeholder = ",".join(["%s"] * len(selected_meals))
            query = f"""
                DELETE FROM history_meal WHERE id IN ({placeholder})
                AND user_profile_id = %s
            """
            value = selected_meals + [user_profile_id]
            cursor.execute(query,value)
            conn.commit()

            return redirect(url_for("planner_meals"))
        else:
            return redirect(url_for("temporary_choices"))
        
    return render_template("planner_meals.html", user_profile_id=user_profile_id, choice_meal=choice_meal, organize_meals=organize_meals)

def teste_contas(user_profile_id, foods_choice):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    #----------- VALUES NECESSARIE FROM USER PROFILE  ------------------
    cursor.execute("SELECT * FROM user_profile "\
        "WHERE id = %s ", (user_profile_id,))
    profile_row = cursor.fetchone()

    #------------------- AGE CALCULATION ---------------
    hoje = date.today()

    birth = profile_row["birthday"]
    if isinstance(birth, str):
        birth = datetime.strptime(birth, "%Y-%m-%d").date()

    age = hoje.year - birth.year - ((hoje.month, hoje.day) < (birth.month, birth.day))

    # --------- EXERCISE ACTIVY FACTOR --------
    exercise_id = profile_row["exercise_id"]
    cursor.execute(" SELECT activy_factor FROM exercise " \
    "WHERE id = %s", (exercise_id,))
    activy_exercise = cursor.fetchone()["activy_factor"]
    # ------------ GOAL_SPEED -------------
    goal_id = profile_row["goal_id"]
    goal_pace_id = profile_row["goal_pace_id"]
    cursor.execute(" SELECT reference_value FROM goal_speed " \
    "WHERE goal_id = %s AND goal_pace_id = %s", (goal_id, goal_pace_id))
    goal_value = cursor.fetchone()["reference_value"]    
    
    # ------------ GOAL_PROTEIN --------------
    cursor.execute(" SELECT goal_protein FROM protein " \
    "WHERE goal_id = %s AND exercise_id = %s", (goal_id, exercise_id))
    goal_protein = cursor.fetchone()["goal_protein"]

    #------------- MEALS PERCENTUAL --------------
    cursor.execute(" SELECT user_profile_meal.meal_id , meal.percentual FROM user_profile_meal JOIN meal ON meal.id = user_profile_meal.meal_id " \
    "WHERE user_profile_meal.profile_id = %s ", (user_profile_id,))
    meals = cursor.fetchall()

    # ------------- DATAS FROM HISTORY_MEAL ----------
    
    macro = {}
    basics = {}
    for food, value in foods_choice.items():
        if food == "choice_meal":
            continue
        cursor.execute(""" SELECT * FROM history_meal WHERE id = %s """, (food,))
        row = cursor.fetchone()
        history_meal_id = row["id"]
        choice = row["choice"]
        details_foods = []
        if choice not in basics:
            basics[choice]= {}
        basics[choice][food] = value
        
        number = 1
        for key, foods in row.items():
            name = "food_" + str(number)
            if name == key and foods != None:
                number += 1
                #---------- JOIN FOOD_METHOD AND SUBGROUP AND GROUP --------------
                cursor.execute("SELECT food_method.*, subgroup.group_name_id, subgroup.ideal_min, subgroup.ideal_max, group_name.name  " \
                "FROM food_method " \
                "INNER JOIN food ON food_method.food_id = food.id " \
                "INNER JOIN subgroup ON food.subgroup_id = subgroup.id " \
                "INNER JOIN group_name ON subgroup.group_name_id = group_name.id " \
                "WHERE food_method.id = %s", (foods,))
                join_table = cursor.fetchone()
                details_foods.append(join_table)

            macro[history_meal_id] = details_foods

    # ---------- PERCENTUAL PER GROUP_NAME --------
    cursor.execute("SELECT id, percentual FROM group_name")
    percentual_group = cursor.fetchall()

    # --------- CALCULATION IN CALCULOS.PY ----------
    return_tmb_tdee = calculos.TMB_TDEE(profile_row["weight"], profile_row["height"], age, activy_exercise, profile_row["gender"])
    return_goal = calculos.goal(return_tmb_tdee, goal_value)
    return_protein_daily = calculos.protein_daily(goal_protein, profile_row["weight"])
    return_meal_nutrients = calculos.meal_nutrients(return_goal, return_protein_daily, meals)
    return_teste, return_list_grocery = calculos.teste(basics, macro, return_meal_nutrients, percentual_group)
    session["show_meal"] = return_teste
    session["grocery_list"] = return_list_grocery
    print("\return_teste", return_teste)
    print("\return_list_grocery", return_list_grocery)
    session["basics"] = basics

@app.route("/temporary_choices", methods=["GET", "POST"])
def temporary_choices():
    conn = get_connection()
    user_id = session.get("user_id")
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM user_profile WHERE user_id = %s", (user_id,))
    user_profile_id =cursor.fetchone()["id"]

    #----------- SESSIONS ------------
    selected_meals = (session.get("selected_meals", []))
    organize_meals = session.get("organize_meals")

    #-------------- SELECT THE USER'S MEALS CHOICES ------------
    ordered = {}
    organize = {} 
    
    for choice_id, conjunto in organize_meals.items():
        print(f"choice_id {choice_id}, conjunto {conjunto}")
        for meal in conjunto:
            print(f"meal {meal}")
            if str(meal["history_meal_id"]) in selected_meals:
                history_id = meal["history_meal_id"]
                if choice_id not in organize:
                    organize[choice_id] = {}
                organize[choice_id][history_id] = meal
    ordered = {
        choice_id: meal_map.get(int(choice_id), int(choice_id))
        for choice_id in organize.keys()
    }
    session["ordered"] = ordered
    session["organize"] = organize
    if request.method == "POST":
        foods_choice = request.form
        teste_contas(user_profile_id, foods_choice)
        return redirect(url_for("show_meals", user_id=user_id))
    
    

    return render_template("temporary_choices.html", ordered=ordered, organize=organize)

@app.route("/show_meals", methods=["GET", "POST"])
def show_meals():
    conn = get_connection()
    user_id = session.get("user_id")
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM user_profile WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    if not row:
        return redirect("/perfil")

    user_profile_id = row["id"]
    name = row["name"]

    ordered = session.get("ordered")
    basics = session.get("basics")
    organize = session.get("organize")
    show_meal = session.get("show_meal")
    prep_list = session.get("grocery_list", {})

    if ordered is None or basics is None or organize is None or show_meal is None:
        cursor.execute("""
            SELECT meals_view
            FROM last_meal_build
            WHERE user_profile_id = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_profile_id,))

        row = cursor.fetchone()

        if row and row["meals_view"]:
            meals_view = json.loads(row["meals_view"])
            return render_template("show_meals.html", meals_view=meals_view, name=name)
        else:
            return redirect("/planner_meals")

    grocery_prep = {}
    meals_view = []

    for choice_id, meal_name in ordered.items():
        for history_meal_id, quantity in basics.get(choice_id, {}).items():
            foods = organize.get(choice_id, {}).get(history_meal_id, {}).get("foods", [])
            calculated = show_meal.get(history_meal_id, [])

            item = []
            total_kcal = 0

            for food, items in zip(foods, calculated):
                kcal = items.get("kcal_item", 0)
                total_kcal += kcal
                food_method_id = str(food["food_method_id"])

                item.append({
                    "food_name": food.get("name"),
                    "grama_pronto": items.get("grama_pronto", 0),
                    "kcal_item": kcal
                })

                if food_method_id in prep_list:
                    food_name = food.get("name")
                    value = prep_list.get(food_method_id)
                    grocery_prep[food_name] = value

            meals_view.append({
                "meal_name": meal_name,
                "quantity": quantity,
                "item": item,
                "total_kcal": total_kcal
            })

    session["grocery_prep"] = grocery_prep

    payload = json.dumps(meals_view, ensure_ascii=False)
    cursor.execute("""
        UPDATE last_meal_build
        SET meals_view = %s, updated_at = NOW()
        WHERE user_profile_id = %s
    """, (payload, user_profile_id))

    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO last_meal_build (user_profile_id, meals_view)
            VALUES (%s, %s)
        """, (user_profile_id, payload))

    conn.commit()

    return render_template("show_meals.html", meals_view=meals_view, name=name)


@app.route("/grocery_list", methods=["GET", "POST"])
def grocery_list():
    user_id = session.get("user_id")
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM user_profile WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    if not row:
        return redirect("/perfil")

    user_profile_id = row["id"]
    name = row["name"]

    prep_list = session.get("grocery_list")
    list_grocery = session.get("list_grocery", {})
    grocery_prep = session.get("grocery_prep", {})

    if prep_list is None:
        cursor.execute("""
            SELECT grocery_view
            FROM last_grocery_list
            WHERE user_profile_id = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_profile_id,))

        row = cursor.fetchone()

        if row and row["grocery_view"]:
            general = json.loads(row["grocery_view"])
            return render_template("grocery_list.html", name=name, general=general)
        else:
            return redirect("/planner_meals")

    dict_grocery = {}

    for food_id, grams in prep_list.items():
        food_id = str(food_id)
        if food_id in list_grocery:
            food_name = list_grocery[food_id]
            dict_grocery[food_name] = dict_grocery.get(food_name, 0) + grams

    general = {
        "Lista de Compras": dict_grocery,
        "Lista de Preparo": grocery_prep
    }


    payload = json.dumps(general, ensure_ascii=False)
    cursor.execute("""
        UPDATE last_grocery_list
        SET grocery_view = %s, updated_at = NOW()
        WHERE user_profile_id = %s
    """, (payload, user_profile_id))

    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO last_grocery_list (user_profile_id, grocery_view)
            VALUES (%s, %s)
        """, (user_profile_id, payload))

    conn.commit()

    return render_template("grocery_list.html", name=name, general=general)


if __name__ == "__main__":
    app.run(debug=True)
