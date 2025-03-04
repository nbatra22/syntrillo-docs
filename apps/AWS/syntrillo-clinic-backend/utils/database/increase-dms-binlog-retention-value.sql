-- This is necessary to avoid a synchronization failure

call mysql.rds_show_configuration;
call mysql.rds_set_configuration('binlog retention hours', 24);

