from llmAgent import LLMAgent
from mngDB import MngDB,sql_text
from pydantic import BaseModel # type: ignore

#generate job role responsibilities and tasks for each generated responsibility
class RoleResponsibility(BaseModel):
    job_responsibility: str 
    responsibility_tasks: list[str]
    
class RoleResponsibilities(BaseModel):
    job_responsibilities: list[RoleResponsibility]

class TaskGen:
    def __init__(self):
        self.llm=LLMAgent()
        self.mngDB=MngDB()
        
    def generate_user_tasks(self,user_uid):
        self.mngDB.del_user_tasks(user_uid)
        user_info,org_info,tasks=self.mngDB.describe_user(user_uid)
        sys_msg="You are a helpful business analyst"
        user_msg=f"Describe job responsibilities and tasks for each responsibility for job role:'{user_info['user_role']}' at {org_info['org_descr']}"
        role_responsibilities=self.llm.struct_query(sys_msg, user_msg,RoleResponsibilities)
        return self.insert_tasks(role_responsibilities.job_responsibilities,user_info['user_uid'])
        
    def insert_tasks(self, responsibilities, user_uid):
        for responsibility in responsibilities:
            for task in responsibility.responsibility_tasks:
                task_info={"task_name":task,"task_responsibility": responsibility.job_responsibility, "task_user_uid":user_uid}
                self.mngDB.insert_or_update_task(task_info)
    