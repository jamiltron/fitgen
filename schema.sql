drop table if exists users;
create table users (
       id integer primary key autoincrement,
       login_name string not null,
       email string not null,
       password string not null,
       user_role string not null,
       barbell integer,
       dumbell integer,
       kettlebell integer,
       bench integer,
       rack integer,
       pullup integer,
       box integer,
       jumprope integer,
       bike integer,
       rower integer,
       elliptical integer,
       climber integer,
       pool integer,
       exercise_ball integer,
       medicine_ball integer,
       leg_press integer,
       leg_extension integer,
       glute_ham_chair integer,
       smith_machine integer,
       secret_question string not null,
       secret_answer string not null
);

drop table if exists workouts;
create table workouts (
       id integer primary key autoincrement,
       user_saved string not null,
       exercises string not null
);

drop table if exists exercises;
create table exercises (
       id integer primary key autoincrement,
       workout_name string not null,
       muscles string not null,
       workout_type string not null,
       force string,
       workout_like string,
       barbell integer,
       dumbell integer,
       kettlebell integer,
       bench integer,
       rack integer,
       pullup integer,
       box integer,
       jumprope integer,
       bike integer,
       rower integer,
       elliptical integer,
       climber integer,
       pool integer,
       exercise_ball integer,
       medicine_ball integer,
       leg_press integer,
       leg_extension integer,
       glute_ham_chair integer,
       smith_machine integer       
);