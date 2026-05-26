from collections import Counter
def TMB_TDEE(weight, height, age, exercise, gender):
    if gender == "F":
        tmb = (10 * weight) + (6.25 * height) - (5 * age) - 161
    if gender == "M":
        tmb = (10 * weight) + (6.25 * height) - (5 * age) + 5       
    
    tdee = tmb * exercise
    return tdee

def goal(calories, goal):

    calorie = calories + (goal)
    return calorie

def protein_daily(goal_protein, weight):
    #--------- PROTEIN -----------
    protein = weight * goal_protein
    return protein

def meal_nutrients(kcal, protein, meals):
    result = {}
    for food in meals:
        percentual = food["percentual"]
        meal = food["meal_id"]
        kcal_meal = kcal * percentual
        protein_meal = protein * percentual
        result[meal]= {
            "kcal_meal" : kcal_meal,
            "protein_meal" : protein_meal,
        }
    return result


def distribuition_kcal(group_name_id,percentual_group, kcal_result):

    percentual = {item["id"]:item["percentual"] for item in percentual_group}
    soma = 0
    for key, value in group_name_id.items():
        if key in percentual:
            soma+= percentual[key]
    
    proportion_kcal = {}
    for key, values in group_name_id.items():
        value = percentual[key]
        proportion = value / soma
        kcal_grupo = kcal_result * proportion
        proportion_kcal[key]= kcal_grupo

    return proportion_kcal



def teste(bascis, macro, result, percentual_group):
    mostruario = {}
    list_grocery = {}
    for key, value in bascis.items():
        kcal_result = result[key]['kcal_meal']
        protein = result[key]['protein_meal']
        for meal, mult in value.items():
            mostruario[meal] = []
            mult = float(mult) 
            if int(meal) in macro:
                foods = macro[int(meal)]
                counts = Counter(
                    item["group_name_id"]
                    for item in foods
                    if item and "group_name_id" in item
                    )
               
                group_name_id = {}
                
                for itens in foods:
                    if itens is None:
                        continue
                    caloria = 0
                    if itens["group_name_id"] == 1:
                        iden = itens["id"]
                        cooking_factor = itens["cooking_factor"]
                        #------- much proteins
                        percentual_protein = 1/counts[1]
                        protein_for_item = protein * percentual_protein

                        #---------- gramas -------------
                        protein_100g = itens["protein_100g"]
                        grama = (protein_for_item * 100)/ protein_100g
                        ideal_max = itens["ideal_max"]

                        if ideal_max is not None and grama > ideal_max:
                            grama = float(ideal_max)

                        #----------- result calorie
                        caloria = (grama * itens["calories_100g"]) / 100

                        #------ cooking factor ---------
                        kcal_result -= caloria 
                        grama_cru =( grama * cooking_factor) * mult
                        # ---------- list --------
                        dictionary = {
                            "id": itens["id"],
                            "grama_pronto": grama,
                            "kcal_item": caloria,
                            "grama_cru": grama_cru
                        }
                        mostruario[meal].append(dictionary)
                        food_id = itens["food_id"]
                        list_grocery[iden] = list_grocery.get(iden, 0) + grama_cru
                    else:
                        if itens["group_name_id"] not in group_name_id:
                            group_name_id[itens["group_name_id"]]= 0
                        
                        group_name_id[itens["group_name_id"]] += 1

                    ideal_min = itens["ideal_min"]

                    if ideal_min is not None:

                        if grama < ideal_min:
                            dictionary["warning"] = "baixo"
                proportion_kcal = distribuition_kcal(group_name_id,percentual_group,kcal_result)
                
                for itens in foods:
                    if itens is None:
                        continue
                    #print("ITENS", itens, f"\n foods {foods}")
                    if itens["group_name_id"] == 1:
                        continue
                    # ------------ GLOBAL VARIVEL -----------
                    value_group = itens["group_name_id" ]
                    calorie = itens["calories_100g"]
                    kcal_proportion = proportion_kcal[value_group]
                    qnt_iten_group = group_name_id[value_group]
                    iden = itens["id"]
                    cooking_factor = itens["cooking_factor"]

                    #------------ CALCULATION -------
                    kcal_item = (kcal_proportion)/qnt_iten_group
                    if calorie == 0:
                        grama = None
                    else:
                        grama = (100 * kcal_item) / calorie
                        ideal_max = itens["ideal_max"]
                        
                        if ideal_max is not None and grama > ideal_max:
                            grama = float(ideal_max)
                            kcal_item = (grama * calorie) / 100
                        #--------------- cooking factor ---------
                        grama_cru = (grama * cooking_factor) * mult

                    # ---------- list --------
                    dictionary = {
                        "id": iden,
                        "grama_pronto": grama,
                        "kcal_item" : kcal_item,
                        "grama_cru": grama_cru,
                        "warning": None
                    }
                    ideal_min = itens["ideal_min"]
                    if ideal_min is not None and grama is not None:
                        if grama < ideal_min:
                            dictionary["warning"] = "baixo"                    
                    mostruario[meal].append(dictionary)
                    food_id = itens["food_id"]
                    list_grocery[iden] = list_grocery.get(food_id, 0) + grama_cru
    return mostruario, list_grocery               
