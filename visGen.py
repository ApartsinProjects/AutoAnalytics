from llmAgent import LLMAgent
from mngDB import MngDB

class VegaVisualization(BaseModel):
    vega_json: str
    visualization_type: str

class VisGen:
    def __init__(self): 
        self.llm=LLMAgent()
        self.mngDB=MngDB()
    
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