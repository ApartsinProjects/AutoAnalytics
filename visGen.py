from llmAgent import LLMAgent
from mngDB import MngDB,sql_text
from pydantic import BaseModel
from pprint import pprint

class D3Visualization(BaseModel):
    DIV_HTML_CODE: str
    visualization_type: str
    

class VisGen:
    def __init__(self): 
        self.llm=LLMAgent()
        self.mngDB=MngDB()
    
    def generate_user_visuals(self,user_uid):
        user_kpis=self.mngDB.get_user_kpis_ids(user_uid)
        sys_msg=f"you are visualization expert designing visualizations and figures using D3 javascript library. You will be given a dataset in json format \
        and you will need to choose a type of visualization or figure and produce a DIV element containing self-containing HTML code for visualization and data."
        for kpi_uid in user_kpis: self.generate_kpi_visual(sys_msg,kpi_uid)
        
    def generate_kpi_visual(self,sys_msg,kpi_uid):
        kpi=self.mngDB.get_obj("kpi",kpi_uid)
        user_msg=f"the visualization is for {kpi['kpi_name']} and the data is {kpi['sql_results_raw']}.Generate HTML DIV element. \
            Make sure legend and axis labels are visible, enlarge or change orientation if necessary. Include actual values mouse over tooltips. Visualize as a table if a single number."
        d3_vis=self.llm.struct_query(sys_msg,user_msg,D3Visualization)
        self.mngDB.store.update_obj("kpis","kpi_uid",{"kpi_uid":kpi_uid,"sql_vis":sql_text(d3_vis.DIV_HTML_CODE)})