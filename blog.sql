CREATE  user 'Blog'@'localhost' identified by 'Blog';
in case of alterations use 
ALTER USER 'Blog'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL privileges on TestCompanion.* to 'Blog'@'localhost';
FLUSH privileges;
