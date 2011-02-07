drop table if exists users;
create table users (
       id integer primary key autoincrement,
       login_name string not null,
       email string not null,
       password string not null,
       user_role string not null,
       barbell integer,
       dumbell integer,
       ketllebell integer,
       bench integer,
       rack integer,
       pullup integer,
       box integer,
       jumprope integer,
       bike integer,
       rower integer,
       elliptical integer,
       climber integer,
       pool integer
);
drop table if exists exercises;
create table exercises (
       id integer primary key autoincrement,
       workout_name string not null,
       muscles string not null,
       workout_type string not null,
       force string not null,
       barbell integer,
       dumbell integer,
       ketllebell integer,
       bench integer,
       rack integer,
       pullup integer,
       box integer,
       jumprope integer,
       bike integer,
       rower integer,
       elliptical integer,
       climber integer,
       pool integer
);