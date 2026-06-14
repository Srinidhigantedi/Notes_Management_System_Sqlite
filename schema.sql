create table users (
    id integer primary key autoincrement,
    username text not null unique,
    email text not null unique,
    password text not null,
    profile_pic text
    
);

create table notes (
    id integer primary key autoincrement,
    title text not null,
    content text not null,
    created_at timestamp default current_timestamp,
    user_id integer not null,
    is_pinned boolean default false,
    foreign key (user_id) references users(id) 
);