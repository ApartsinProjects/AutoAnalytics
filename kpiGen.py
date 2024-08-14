from llmAgent import LLMAgent
from pydantic import BaseModel
import json
from mngDB import MngDB,sql_text
from schemePrompt import SchemePrompt
from collections import ChainMap

class ColumnSpecification(BaseModel):
    table_name: str
    column_name: str

class KPI(BaseModel):
    KPI: str
    kpi_utility_for_the_task: str
    
class TaskKPIs(BaseModel):
    KPIs:list[KPI]
    
class KPIImplementationRecipe(BaseModel):
    sql_implementation_recipe: str
    grouping_columns: list[ColumnSpecification]
    input_columns:list[ColumnSpecification]
    is_implementation_feasible:bool
             
class KPIGen:
    def __init__(self):
        self.mngDB=MngDB()
        self.llm=LLMAgent()
        
    def generate_user_kpis(self,user_uid):
        self.user_info,self.org_info,tasks=self.mngDB.describe_user(user_uid)
        self.schema_prompt=SchemePrompt().get_summary_prompt(self.user_info["user_org_uid"])
        sys_msg=f"You are a business analyst designing a dashboard for a'{self.user_info['user_role']}' at {self.org_info['org_descr']}\
            You receive the following description for the available data including the known data gaps:{self.schema_prompt}"
        all_kpis=ChainMap(*[self.generate_task_kpi(sys_msg,task['task_uid']) for task in tasks])
        self.mngDB.create_objs_batch("kpi",list(all_kpis.values()))
        
    def generate_task_kpi(self,sys_msg, task_uid):
        self.mngDB.delete_task_kpis(task_uid)
        task=self.mngDB.get_obj("task",task_uid)
        user_msg=f"Identify and list KPIs that can be computed from the described data that are useful for accomplishing the task:'{task['task_name']}'\
            Specify KPIs names and descriptions in the terms appearing in the data description above excluding data gaps, don't use other terms\
            Describe the utility of the KPI for accomplishing the task"
           
        task_kpis=self.llm.struct_query(sys_msg,user_msg,TaskKPIs)
        return {sql_text(kpi.KPI):{'kpi_name':sql_text(kpi.KPI), 
                                   'kpi_description':sql_text(kpi.kpi_utility_for_the_task),
                                   "kpi_task_uid":task_uid} for kpi in task_kpis.KPIs}     
        
    def generate_kpi_recipes(self,user_uid):
        org_uid=self.mngDB.get_obj("user",user_uid)['user_org_uid']
        kpis=self.mngDB.store.fetchall(f"select kpis.* from kpis join tasks on kpis.kpi_task_uid=tasks.task_uid where tasks.task_user_uid='{user_uid}'") 
        sys_msg=f"you are a senior database developer responsible for implementing SQL queries for computing KPIs based on KPIs specification and\
            the following description of the available database tables and columns:{SchemePrompt().get_rich_schema_prompt(org_uid)}"
        recipes=[self.get_kpi_recipe(sys_msg,kpi) for kpi in kpis]
        return self.mngDB.update_objs("kpi", recipes)
    
    def get_kpi_recipe(self,sys_msg,kpi):
        user_msg=f"based on the database description and a KPI specification:'{kpi['kpi_name']}',identify all relevant input columns required for computing the KPI.\
            Identify all relevant grouping columns or column combination in the database and provide a detailed recipe for a junior developer for implementing teh query.\
            Finally, compare the recipe , identified columns and provided database description for verifying the feasibility of the implementation provided available data."
        recipe=self.llm.struct_query(sys_msg,user_msg,KPIImplementationRecipe)
        return {'kpi_uid':kpi['kpi_uid'],
                "kpi_calc_instructions":sql_text(recipe.sql_implementation_recipe),
                "kpi_group_cols":sql_text(json.dumps([c.json() for c in recipe.grouping_columns])),
                "kpi_cols":sql_text(json.dumps([c.json() for c in recipe.input_columns])),
                "is_data_available":"true" if recipe.is_implementation_feasible else "false"}        
                