show databases;
create database nutriplanner;
use nutriplanner;
select database();
show tables;

create table user_login(
	id int not null auto_increment,
    email varchar(200) unique,
    pass_hash varchar(100) not null,
    primary key (id)
);

create table goal(
	id int not null auto_increment,
    goals varchar(25) not null,
    primary key(id)
);

create table goal_pace(
	id int not null auto_increment,
    pace float not null,
    primary key(id)
);

create table meal(
	id int not null auto_increment,
    meal_name varchar(50) not null,
	primary key (id)
);

create table user_profile(
	id int not null auto_increment,
    user_id int not null unique,
    name varchar(255) not null,
    birthday int not null,
    gender char(1) check(gender in ('F', 'M')),
    height int not null,
    weight float not null,
    goal_id int not null,
    goal_pace_id int not null,
    exercise_id int not null,
    principal_meal_id int not null,
    eats_sweet_daily varchar(4) check(eats_sweet_daily in ('yes','no')),
    vegetable int  null default 30,
    legumes int  null default 100,    
    primary key (id),
    foreign key (goal_id) references goal(id),
    foreign key (goal_pace_id) references goal_pace(id),
    foreign key (principal_meal_id) references meal(id),
    foreign key (exercise_id) references exercise(id)
);

create table user_profile_meal(
	profile_id int not null,
    meal_id int not null,
    primary key(profile_id, meal_id),
    foreign key(profile_id) references user_profile(id),
    foreign key(meal_id) references meal(id)
);

create table group_name(
	id int not null auto_increment,
    name varchar(100) unique,
    primary key(id)
);

create table subgroup(
	id int not null auto_increment,
    name varchar(100) unique,
    group_name_id  int not null,
    primary key(id),
    foreign key(group_name_id) references	group_name(id)
    on delete no action on update no action
);

create table exercise(
	id int not null auto_increment,
    exercise_level varchar(50) not null,
    primary key (id)
);

create table food(
	id int not null auto_increment,
    name varchar(150) not null,
    subgroup_id  int null,
    primary key(id),
    foreign key(subgroup_id) references subgroup(id)
);

create table method(
	id int not null auto_increment,
    name varchar(100) not null unique,
    primary key(id)
);

create table food_Method(
	id int not null auto_increment,
    food_id int not null,
    method_id int not null,
    cooking_factor float not null check(cooking_factor >= 0),
    calories_100g float not null check(calories_100g >= 0),
    protein_100g float not NULL check(protein_100g >= 0),
	carbs_100g float not NULL check(carbs_100g >= 0),
	fat_100g float not NULL check(fat_100g >=0),
    primary key (id),
    foreign key (food_id) references food(id),
    foreign key (method_id) references method(id),
    unique key unique_food_method(food_id, method_id)
);

create table history_meal(
	id int not null auto_increment,
    user_profile_id int not null,
    choice int not null,
    
    food_1 int null,
    food_2 int null,
    
    food_3 int null,
    food_4 int null,
    
    food_5 int null,
	food_6 int null,

	food_7 int null,
	food_8 int null,

	food_9 int null,
	food_10 int null,

	food_11 int null,
	food_12 int null,

	food_13 int null,
	food_14 int null,

	food_15 int null,
	food_16 int null,

	food_17 int null,
	food_18 int null,
    
    primary key(id),
    foreign key (user_profile_id) references user_profile(id)
);

create table goal_speed(
	id int not null auto_increment,
    goal_id int not null,
    goal_pace_id int not null,
    reference_value int not null,
    primary key (id),
    foreign key (goal_id) references goal(id),
    foreign key (goal_pace_id) references goal_pace(id)
);

create table protein(
	id int not null auto_increment,
    goal_id int not null,
    exercise_id int not null,
    goal_protein int not null,
    primary key (id),
    foreign key (goal_id) references goal(id),
    foreign key (exercise_id) references exercise(id)
);

CREATE TABLE last_meal_build (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_profile_id INT NOT NULL,
    meals_view JSON NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);


select * from last_meal_build;
select * from user_login;
select * from user_profile;
select * from exercise;
select * from goal;
select * from goal_pace;
select * from meal;
select * from user_profile_meal;
select * from group_name;
select * from subgroup;
select * from food;
select * from food_method;
select * from history_meal;
select * from method;
select * from goal_speed;
select * from protein;



SHOW CREATE TABLE history_meal;
truncate table protein;
ALTER TABLE group_name add column percentual float; 
update group_name set percentual = 0.0 where id = 1;
update group_name set percentual = 1.0 where id = 2;
update group_name set percentual = 0.5 where id = 3;
update group_name set percentual = 0.0 where id = 4;
update group_name set percentual = 0.4 where id = 5;
update group_name set percentual = 0.5 where id = 6;
update group_name set percentual = 0.3 where id = 7;
update group_name set percentual = 0.4 where id = 8;
update group_name set percentual = 0.7 where id = 9;

ALTER TABLE history_meal
ADD COLUMN meal_signature VARCHAR(255) NOT NULL;

SET SQL_SAFE_UPDATES = 0;
TRUNCATE TABLE history_meal;
SET SQL_SAFE_UPDATES = 1;


ALTER TABLE history_meal
ADD CONSTRAINT unique_history_meal
UNIQUE (user_profile_id, choice, meal_signature);

ALTER TABLE history_meal RENAME COLUMN protein_2 TO food_2;   
-- FOREIGN KEY (exercise_id) REFERENCES exercise(id);
-- DESCRIBE user_profile;

insert into meal (goal_id, exercise_id, goal_protein) values (1,1,1.2);
insert into meal (goal_id, exercise_id, goal_protein) values (2,1,1.2);
insert into meal (goal_id, exercise_id, goal_protein) values (3,1,0.8);
insert into meal (goal_id, exercise_id, goal_protein) values (1,2,1.4);
insert into meal (goal_id, exercise_id, goal_protein) values (2,2,1.4);
insert into meal (goal_id, exercise_id, goal_protein) values (3,2,1.0);