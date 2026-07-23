create database ecom029;
use ecom029;
create table admindata(adminid binary(16) primary key,adminname varchar(50) not null,adminemail varchar(50) unique key not null,adminphone_no varchar(10),adminpassword varbinary(255) not null,adminaddress varchar(255) not null,adminfilename varchar(15),adminagree enum('on','off'));
create table items(itemid binary(16) primary key,itemname longtext not null, itemdescription longtext,itemAbout longtext,itemprice decimal(10,2),itemquantity int unsigned,category enum('home_appliances','grocery','electronics','sports','toys','fashion'),added_by binary(16),itemfilename varchar(20),created_at datetime default now(),foreign key(added_by) references admindata(adminid));
desc items;