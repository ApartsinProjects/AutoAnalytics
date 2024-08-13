from llmAgent import LLMAgent
from pydantic import BaseModel
from mngDB import MngDB,sql_text
from schemePrompt import SchemePrompt
from collections import ChainMap

class KPI(BaseModel):
    KPI: str
    effect_on_decisions: str
    
class TaskKPIs(BaseModel):
    KPIs:list[KPI]
             
class KPIGen:
    def __init__(self):
        self.mngDB=MngDB()
        self.llm=LLMAgent()
        
    def generate_user_kpis(self,user_uid):
        self.user_info,self.org_info,tasks_ids=self.mngDB.describe_user(user_uid)
        self.schema_prompt=SchemePrompt().get_schema_prompt(self.user_info["user_org_uid"])
        all_kpis=ChainMap(*[self.generate_task_kpi(task_uid) for task_uid in tasks_ids])
        self.mngDB.create_objs_batch("kpi",list(all_kpis.values()))
        
    def generate_task_kpi(self,task_uid):
        self.mngDB.delete_task_kpis(task_uid)
        task=self.mngDB.get_obj("task",task_uid)
        sys_msg=f"You are a  business intelligence analyst analyzing job role:'{self.user_info['user_role']}' at {self.org_info['org_descr']}"
        user_msg=f"you need to determine the data-driven KPIs that help a person at this job role to perform task:'{task['task_name']}'. \
            List only KPIs that can be computed from the data described by the following tables and columns:{self.schema_prompt}"
        task_kpis=self.llm.struct_query(sys_msg,user_msg,TaskKPIs)
        return {sql_text(kpi.KPI):{'kpi_name':sql_text(kpi.KPI), 'kpi_description':sql_text(kpi.effect_on_decisions),"kpi_task_uid":task_uid} for kpi in task_kpis.KPIs}         
                
                