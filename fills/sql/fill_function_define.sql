/* 可用填充函数的初始化文件 */

INSERT INTO public.fills_generaterule (id,created_at,updated_at,rule_name,function_name,fill_order,description) VALUES
	 (4882843648000,'2023-06-28 21:34:10.250237+08','2023-06-28 21:34:10.250237+08','time_serial_iter','time_serial_iter',1,'日期时间字符串'),
	 (4883453444096,'2023-06-28 21:35:24.688104+08','2023-06-28 21:35:24.688104+08','value_list_iter','value_list_iter',2,'字符串数组'),
	 (4884580073472,'2023-06-28 21:37:42.216547+08','2023-06-28 21:41:00.693467+08','associated_fill','associated_fill',2,'特定数据集'),
	 (4878393573376,'2023-06-28 21:25:07.029875+08','2023-06-28 21:41:14.549457+08','fixed_value_iter','fixed_value_iter',1,'单个固定数据'),
	 (4880372080640,'2023-06-28 21:29:08.54572+08','2023-06-28 21:41:25.183687+08','random_number_iter','random_number_iter',1,'范围随机数值'),
	 (4897600479232,'2023-06-28 22:04:11.622607+08','2023-06-28 22:04:11.622607+08','calculate_expressions','calculate_expressions',3,'数值计算'),
	 (4898068365312,'2023-06-28 22:05:08.737051+08','2023-06-28 22:05:08.737051+08','join_string','join_string',4,'固定字符拼接多个值');

INSERT INTO public.fills_generateruleparameter (id,created_at,updated_at,"name",data_type,description,required,default_value,need_outside_data,rule_id) VALUES
	 (4880863305728,'2023-06-28 21:30:08.539895+08','2023-06-28 21:30:08.539895+08','start','number','起始值',false,'1',false,4880372080640),
	 (4881075896320,'2023-06-28 21:30:34.488701+08','2023-06-28 21:30:34.488701+08','stop','number','结束值',false,'42',false,4880372080640),
	 (4881783652352,'2023-06-28 21:32:00.881345+08','2023-06-28 21:32:00.881345+08','is_decimal','boolean','是否包含小数',false,'false',false,4880372080640),
	 (4881930936320,'2023-06-28 21:32:18.860503+08','2023-06-28 21:33:01.482113+08','ndigits','number','小数位数',false,'2',false,4880372080640),
	 (4883106578432,'2023-06-28 21:34:42.3718+08','2023-06-28 21:34:42.3718+08','repeat','number','每个时间字符串的重复次数',false,'1',false,4882843648000),
	 (4878639841280,'2023-06-28 21:25:37.114913+08','2023-07-01 08:53:07.131696+08','value','string','固定值',true,'',false,4878393573376),
	 (6899782516736,'2023-07-01 17:57:38.635218+08','2023-07-01 17:57:53.410836+08','data_set_id','number','数据集ID',true,'',true,4883453444096);

/* 填充数据定义 */

INSERT INTO public.fills_dataset (id,created_at,updated_at,description,data_type) VALUES
	 (6898361286656,'2023-07-01 17:54:45.119367+08','2023-07-01 17:54:45.119367+08','基本数组值','string');

INSERT INTO public.fills_datasetvalue (id,created_at,updated_at,item,data_set_id) VALUES
	 (6899205513216,'2023-07-01 17:56:28.199708+08','2023-07-01 17:56:28.199708+08','["地狱", "Are you okay?", "秀", "666"]',6898361286656);

/* 填充要求数据 */

INSERT INTO public.fills_fillingrequirement (id,created_at,updated_at,username,remark,file_id,original_filename,start_line,line_number) VALUES
	 (5317329305600,'2023-06-29 12:18:08.051478+08','2023-07-01 00:14:20.866807+08','jack','哈哈哈','1','abc.xlsx',2,100);

INSERT INTO public.fills_columnrule (id,created_at,updated_at,column_name,column_type,associated_of,requirement_id,rule_id) VALUES
	 (5615939674112,'2023-06-29 22:25:39.560192+08','2023-06-29 22:25:39.561192+08','A','string',false,5317329305600,4878393573376),
	 (6290629640192,'2023-06-30 21:18:19.175045+08','2023-06-30 21:18:19.175045+08','C','string',false,5317329305600,4882843648000),
	 (6293361188864,'2023-06-30 21:23:52.616814+08','2023-07-01 08:36:40.756242+08','B','number',false,5317329305600,4880372080640),
	 (6633977036800,'2023-07-01 08:56:51.694136+08','2023-07-01 08:56:51.694136+08','D','string',true,5317329305600,4883453444096);

INSERT INTO public.fills_dataparameter (id,created_at,updated_at,"name",value,expressions,data_set_id,column_rule_id,param_rule_id) VALUES
	 (5616271892480,'2023-06-29 22:26:20.107899+08','2023-06-29 22:26:20.107899+08','value','哈哈哈','',NULL,5615939674112,4878639841280),
	 (6291305594880,'2023-06-30 21:19:41.689483+08','2023-06-30 21:22:41.351998+08','repeat','2','',NULL,6290629640192,4883106578432),
	 (6293501829120,'2023-06-30 21:24:09.781263+08','2023-06-30 21:24:09.781263+08','start','10','',NULL,6293361188864,4880863305728),
	 (6293624799232,'2023-06-30 21:24:24.79127+08','2023-06-30 21:24:24.79127+08','stop','300','',NULL,6293361188864,4881075896320),
	 (6624395280384,'2023-07-01 08:37:22.047362+08','2023-07-01 08:37:22.047362+08','is_decimal','True','',NULL,6293361188864,4881783652352),
	 (6900890017792,'2023-07-01 17:59:53.853616+08','2023-07-01 17:59:53.853616+08','data_set_id','','',6898361286656,6633977036800,6899782516736);
