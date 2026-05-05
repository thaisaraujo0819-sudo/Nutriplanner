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


select * from user_profile;
select * from user_login;
select * from goal;
select * from goal_pace;
select * from meal;
select * from user_profile_meal;
select * from group_name;
select * from subgroup;
select * from food;
select * from food_method;
select * from method;

-- alter table user_profile_meal drop column id;
-- FOREIGN KEY (exercise_id) REFERENCES exercise(id);
-- alter table user_profile modify column birthday int not null;
-- DESCRIBE user_profile;