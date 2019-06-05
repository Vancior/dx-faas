create table users
(
	id int auto_increment,
	email varchar(255) not null,
	nickname varchar(255) null,
	constraint user_pk
		primary key (id)
);

create unique index user_email_uindex
	on user (email);

create table functions
(
	id int auto_increment,
	uid int not null,
	name varchar(255) not null,
	uri text not null,
	memory_limit int not null,
    max_idle_time int default 1440 not null,
	environment varchar(255) not null,
	entrypoint text not null,
	code_url text null,
	status char(25) default created not null,
	constraint function_pk
		primary key (id)
);

create table workflows
(
	id int auto_increment,
	uid int not null,
	name varchar(255) not null,
	uri text not null,
    max_idle_time int default 1440 not null,
	definition text not null,
	status char(25) default 'created' not null,
	constraint workflows_pk
		primary key (id)
);

create table function_instances
(
	id int auto_increment,
	fid int not null,
    guid char(255) not null,
	status char(25) default 'deploying' not null,
	start_time timestamp default CURRENT_TIMESTAMP not null,
	destroy_time timestamp null,
	node_ip char(25) null,
	wi_id int null comment 'id of the workflow instance that contains this function instance',
	name_in_w varchar(255) null comment 'name of the state whose function is this instance in a workflow',
	constraint function_instances_pk
		primary key (id)
);

create index function_instances_fid_index
	on function_instances (fid);
create index function_instances_wi_id_index
	on function_instances (wi_id);

create table workflow_instances
(
	id int auto_increment,
	wid int not null,
	guid varchar(255) not null,
	status char(25) default 'deploying' not null,
	start_time timestamp default CURRENT_TIMESTAMP not null,
	destroy_time timestamp null,
	constraint workflow_instances_pk
		primary key (id)
);

create index workflow_instances_wid_index
	on workflow_instances (wid);



/*

generated

*/

create schema dx_web2 collate utf8mb4_0900_ai_ci;

create table function_instances
(
	id int auto_increment
		primary key,
	fid int not null,
	guid char(255) not null,
	status char(25) default 'deploying' not null,
	start_time timestamp default CURRENT_TIMESTAMP not null,
	destroy_time timestamp null,
	node_ip char(25) null,
	wi_id int null comment 'id of the workflow instance that contains this function instance',
	name_in_w varchar(255) null comment 'name of the state whose function is this instance in a workflow'
);

create index function_instances_fid_index
	on function_instances (fid);

create index function_instances_wi_id_index
	on function_instances (wi_id);

create table functions
(
	id int auto_increment
		primary key,
	uid int not null,
	name varchar(255) not null,
	uri text null,
	memory_limit int not null,
	max_idle_time int default 1440 not null,
	environment varchar(255) not null,
	entrypoint text not null,
	code_url text null,
	status char(25) null
);

create table users
(
	id int auto_increment
		primary key,
	email varchar(255) not null,
	nickname nvarchar(255) null,
    password char(255) not null,
	constraint user_email_uindex
		unique (email)
);

create table workflow_instances
(
	id int auto_increment
		primary key,
	wid int not null,
	guid varchar(255) not null,
	status char(25) default 'deploying' not null,
	start_time timestamp default CURRENT_TIMESTAMP not null,
	destroy_time timestamp null
);

create index workflow_instances_wid_index
	on workflow_instances (wid);

create table workflows
(
	id int auto_increment
		primary key,
	uid int not null,
	name varchar(255) not null,
	uri text not null,
	max_idle_time int default 1440 not null,
	definition text not null,
	status char(25) default 'created' not null
);

/* 

with foreign key

*/

create schema if not exists dx_web2 collate utf8mb4_0900_ai_ci;

create table if not exists users
(
	id int auto_increment
		primary key,
	email varchar(255) not null,
	nickname nvarchar(255) null,
    password char(255) not null,
	constraint user_email_uindex
		unique (email)
);

create table if not exists functions
(
	id int auto_increment
		primary key,
	uid int not null,
	name varchar(255) not null,
	uri text null,
	memory_limit int not null,
	max_idle_time int default 1440 not null,
	environment varchar(255) not null,
	entrypoint text not null,
	code_url text null,
	status char(25) null,
	constraint functions_users_id_fk
		foreign key (uid) references users (id)
);

create table if not exists workflows
(
	id int auto_increment
		primary key,
	uid int not null,
	name varchar(255) not null,
	uri text not null,
	max_idle_time int default 1440 not null,
	definition text not null,
	status char(25) default 'created' not null,
	constraint workflows_users_id_fk
		foreign key (uid) references users (id)
);

create table if not exists workflow_contain_function
(
	fid int not null,
	wid int not null
		primary key,
	constraint workflow_contain_function_functions_id_fk
		foreign key (fid) references functions (id),
	constraint workflow_contain_function_workflows_id_fk
		foreign key (wid) references workflows (id)
);

create table if not exists workflow_instances
(
	id int auto_increment
		primary key,
	wid int not null,
	guid varchar(255) not null,
	status char(25) default 'deploying' not null,
	start_time timestamp default CURRENT_TIMESTAMP not null,
	destroy_time timestamp null,
	constraint workflow_instances_workflows_id_fk
		foreign key (wid) references workflows (id)
);

create table if not exists function_instances
(
	id int auto_increment
		primary key,
	fid int not null,
	guid char(255) not null,
	status char(25) default 'deploying' not null,
	start_time timestamp default CURRENT_TIMESTAMP not null,
	destroy_time timestamp null,
	node_ip char(25) null,
	wi_id int null comment 'id of the workflow instance that contains this function instance',
	name_in_w varchar(255) null comment 'name of the state whose function is this instance in a workflow',
	constraint function_instances_functions_id_fk
		foreign key (fid) references functions (id),
	constraint function_instances_workflow_instances_id_fk
		foreign key (wi_id) references workflow_instances (id)
);

create index function_instances_fid_index
	on function_instances (fid);

create index function_instances_wi_id_index
	on function_instances (wi_id);

create index workflow_instances_wid_index
	on workflow_instances (wid);


