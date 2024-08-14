from llmAgent import LLMAgent
from pydantic import BaseModel
import json
from mngDB import MngDB,sql_text
from schemePrompt import SchemePrompt
from collections import ChainMap



class KPI(BaseModel):
    KPI: str
    kpi_utility_for_the_task: str
    
class TaskKPIs(BaseModel):
    KPIs:list[KPI]
                 
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
        Specify KPIs names and descriptions in the terms appearing in the data description above excluding data gaps, don't use other terms.\
            Describe the utility of the KPI for accomplishing the task"
           
        task_kpis=self.llm.struct_query(sys_msg,user_msg,TaskKPIs)
        return {sql_text(kpi.KPI):{'kpi_name':sql_text(kpi.KPI), 
                                   'kpi_description':sql_text(kpi.kpi_utility_for_the_task),
                                   "kpi_task_uid":task_uid} for kpi in task_kpis.KPIs}           