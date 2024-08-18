from llmAgent import LLMAgent
from mngDB import MngDB,sql_text
from pydantic import BaseModel

class DataKPIInsight(BaseModel):
    insight_or_trend_or_pattern: str
    explanation: str

class InsightGen:
    def __init__(self):
        self.mngDB=MngDB()
        self.llm=LLMAgent()
        
    def derive_insights(self, user_uid):
        kpis_uids=self.mngDB.get_user_kpis_ids(user_uid)
        for kpi_uid in kpis_uids: self.derive_kpi_insights(user_uid,kpi_uid)
        
    def derive_kpi_insights(self,user_uid,kpi_uid):
        user_info, org_info, tasks=kpi=self.mngDB.describe_user(user_uid)
        kpi=self.mngDB.get_obj("kpi",kpi_uid)
        sys_msg=f"you are a business consultant advising to a {user_info['user_role']} at {org_info['org_descr']} based on data-driven KPIs"
        user_msg=f"You have received the data for KPI {kpi['kpi_name']} and you are analyzing it for {kpi['kpi_description']}.\
            The data in json format is {kpi['sql_results']}.\
                Summarize the most interesting possible pattern,trend or insight that can be derived from the data.\
                    Explain how the teh conclusion is reached."
                    
        insights=self.llm.struct_query(sys_msg,user_msg,DataKPIInsight)
        self.mngDB.update_obj("kpi",{"kpi_uid":kpi_uid,
                              "kpi_insight":sql_text(insights.insight_or_trend_or_pattern),
                              "kpi_insight_justification":sql_text(insights.explanation)})
                