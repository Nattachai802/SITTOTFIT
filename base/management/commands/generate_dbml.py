from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models


class Command(BaseCommand):
   help = 'Generate DBML file from Django models'


   def handle(self, *args, **kwargs):
       # สร้างตัวแปรสำหรับไฟล์ DBML
       dbml_content = ""


       # ดึงโมเดลทั้งหมดจากทุกแอปในโปรเจกต์
       models_list = []
       for app_config in apps.get_app_configs():
           models_list.extend(app_config.get_models())


       # สร้าง DBML content สำหรับแต่ละตาราง
       for model in models_list:
           table_name = model._meta.model_name
           dbml_content += f"Table {table_name} {{\n"


           # สร้างคอลัมน์ตามฟิลด์ในโมเดล
           for field in model._meta.fields:
               field_name = field.name
               field_type = field.get_internal_type().lower()
               if isinstance(field, models.CharField):
                   dbml_content += f"  {field_name} varchar\n"
               elif isinstance(field, models.TextField):
                   dbml_content += f"  {field_name} text\n"
               elif isinstance(field, models.IntegerField):
                   dbml_content += f"  {field_name} integer\n"
               elif isinstance(field, models.DateTimeField):
                   dbml_content += f"  {field_name} timestamp\n"
               elif isinstance(field, models.ForeignKey):
                   related_model = field.related_model
                   dbml_content += f"  {field_name}_id integer [note: 'foreign key to {related_model._meta.model_name}']\n"


           dbml_content += "}\n\n"


       # สร้างความสัมพันธ์ระหว่างตาราง
       for model in models_list:
           for field in model._meta.fields:
               if isinstance(field, models.ForeignKey):
                   from_table = model._meta.model_name
                   to_table = field.related_model._meta.model_name
                   dbml_content += f"Ref: {from_table}.{field.name}_id > {to_table}.id // many-to-one\n"


       # เขียนข้อมูล DBML ลงไฟล์
       with open('generated_schema.dbml', 'w') as file:
           file.write(dbml_content)


       self.stdout.write(self.style.SUCCESS('Successfully generated DBML file'))