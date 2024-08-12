
from baseAgent import BaseAgent
from sqlStore import SQLStore
from pydantic import BaseModel
import uuid,json

def sql_text(s): return s.replace("'","''")

class KPI(BaseModel):
    KPI: str
    effect_on_decisions: str
    
class TaskKPIs(BaseModel):
    KPIs:list[KPI]
    
    
from schema import TableMetadata

class SQLStatement(BaseModel):
    sql_text: str
    grouping_columns: list[str]
    resulting_table:TableMetadata
    data_assumptions: list[str]
    sample_output:list[dict]
    
class VegaVisualization(BaseModel):
    vega_json: str
    visualization_type: str
     
class KPIGen:
    def __init__(self):
        self.store=SQLStore().connect(db_name="taskanalytics")
        self.llm=BaseAgent()
        
    def generate_user_kpis(self,user_uid):
        self.user_info=self.store.fetch_obj("users","user_uid",user_uid)
        self.org_info=self.store.fetch_obj("orgs","org_uid",self.user_info["user_org_uid"])
        self.schema_prompt=self.get_schema_prompt(self.user_info["user_org_uid"])
        tasks_ids=self.store.fetch_refs("tasks","task_uid","task_user_uid",user_uid)
        all_kpis={}
        for task_uid in tasks_ids: all_kpis.update(self.generate_task_kpi(task_uid)) #overwrite duplicates
        self.store_kpis(all_kpis)
        
    def get_schema_prompt(self, org_uid):
        tables=self.store.fetchall(f"select  distinct table_name from cols where table_org_uid='{org_uid}'")
        return ";".join([self.get_table_prompt(table['table_name'],org_uid) for table in tables])
    
    def get_table_prompt(self, table_name,org_uid):
        cols=self.store.fetchall(f"select * from cols where table_org_uid='{org_uid}' and table_name='{table_name}'")
        column_prompt=",".join([f"{c['col_name']} of type {c['col_type']}" for c in cols])
        return f"table:'{table_name}' with columns:[{column_prompt}]"
        
    def generate_task_kpi(self,task_uid):
        self.store.del_refs("kpis","kpi_uid","kpi_task_uid",task_uid)
        task=self.store.fetch_obj("tasks","task_uid",task_uid)
        sys_msg=f"You are a  business intelligence analyst analyzing job role:'{self.user_info['user_role']}' at {self.org_info['org_descr']}"
        user_msg=f"you need to determine the data-driven KPIs that help a person at this job role to perform task:'{task['task_name']}'. \
            List only KPIs that can be computed from the data described by the following tables and columns:{self.schema_prompt}"
        task_kpis=self.llm.struct_query(sys_msg,user_msg,TaskKPIs)
        return {sql_text(kpi.KPI):{'kpi_name':sql_text(kpi.KPI), 'kpi_description':sql_text(kpi.effect_on_decisions),"kpi_task_uid":task_uid} for kpi in task_kpis.KPIs}
    
    def store_kpis(self,all_kpis):
        for v in all_kpis.values():self.store.insert_obj("kpis","kpi_uid",v)
        
    def get_user_kpis(self, user_uid):
        res=self.store.fetchall(f"select kpis.kpi_uid from kpis join tasks on kpis.kpi_task_uid=tasks.task_uid where tasks.task_user_uid='{user_uid}'")
        return [r["kpi_uid"] for r in res]
        
    def generate_kpis_sql(self,user_uid):
        self.user_info=self.store.fetch_obj("users","user_uid",user_uid)
        self.org_info=self.store.fetch_obj("orgs","org_uid",self.user_info["user_org_uid"])
        self.schema_prompt=self.get_schema_prompt(self.user_info["user_org_uid"])
        user_kpis=self.get_user_kpis(user_uid)
        for kpi_uid in user_kpis: self.generate_kpi_sql(kpi_uid)
            
    def generate_kpi_sql(self, kpi_uid):
        kpi=self.store.fetch_obj("kpis","kpi_uid", kpi_uid)
        sys_msg=f"you are a DB designer that need to prepare an SQL statement for computing \
            and visualizing KPI:'{kpi['kpi_name']} based on the following tables and columns: {self.schema_prompt}"
        user_msg=f"generate SQL query while using @periodStart and @periodEnd placeholders for parameters of type 'timestamp'.\
            Describe the columns of the resulting table. If it makes sense to compute KPI based on some grouping column,\
                use @groupColumn placeholder for the name of the grouping column with value 'all' for no grouping.\
                    Generate a table of sample output as list of row dictionaries. Additionally, list all assumptions about input data formats and content. "
        sql_stmt=self.llm.struct_query(sys_msg,user_msg,SQLStatement)
        self.store.update_obj("kpis","kpi_uid",
                              {"kpi_uid":kpi_uid,
                               "sql_text":sql_text(sql_stmt.sql_text),
                               "sql_output_scheme":sql_text(json.dumps(sql_stmt.resulting_table.model_dump(mode="json"))),
                               "sql_group_columns":sql_text(json.dumps(sql_stmt.grouping_columns)),
                               "sql_assumptions":sql_text(json.dumps(sql_stmt.data_assumptions)),
                               "sql_sample_output":sql_text(json.dumps(sql_stmt.sample_output)),
                               })

        
    def generate_user_visuals(self,user_uid):
        self.user_info=self.store.fetch_obj("users","user_uid",user_uid)
        self.org_info=self.store.fetch_obj("orgs","org_uid",self.user_info["user_org_uid"])
        self.schema_prompt=self.get_schema_prompt(self.user_info["user_org_uid"])
        user_kpis=self.get_user_kpis(user_uid)
        for kpi_uid in user_kpis: self.generate_kpi_visual(kpi_uid)
        
    def generate_kpi_visual(self,kpi_uid):
        kpi=self.store.fetch_obj("kpis","kpi_uid", kpi_uid)
        sys_msg=f"you are visualization expert designing visualization in vega grammar"
        user_msg=f"you design a visualization for {kpi['kpi_name']} user-controlled by signals @periodStart and @PeriodEnd that are also provided as part of the data URL\
                   There is also user-selected categorical signals for grouping the data {kpi['sql_group_columns']}. The 'all' value means no grouping\
                       The data is received as a csv with the following columns {kpi['sql_output_scheme']}"
        vega_vis=self.llm.struct_query(sys_msg,user_msg,VegaVisualization)
        print(vega_vis)
        
        
          
                
                