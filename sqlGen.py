from llmAgent import LLMAgent
from mngDB import MngDB,sql_text
from pydantic import BaseModel
from schemeAnnotator import TableMetadata
from schemePrompt import SchemePrompt
import json

class SQLStatement(BaseModel):
    sql_text: str
    
class SQLGen:
    def __init__(self):
        self.llm=LLMAgent()
        self.mngDB=MngDB()
        
    def generate_kpis_sql(self,user_uid):
        self.user_info,self.org_info,tasks=self.mngDB.describe_user(user_uid)
        self.schema_prompt=SchemePrompt().get_annotated_schema_prompt(self.user_info["user_org_uid"])
        user_kpis=self.mngDB.get_user_kpis_ids(user_uid)
        #for kpi_uid in user_kpis: self.generate_kpi_sql(kpi_uid)
        for kpi_uid in user_kpis[1:10]: self.generate_kpi_sql(kpi_uid)
            
    def generate_kpi_sql(self,kpi_uid):
        kpi=self.mngDB.get_obj("kpi", kpi_uid)
        sys_msg=f"you are a MySQL DB designer that need to verify that KPIs can be computed and if yes, prepare an SQL statement for computing \
            and visualizing KPI:'{kpi['kpi_name']} based on the following tables and columns: {self.schema_prompt}"
        user_msg=f"If feasible given available data, \
            generate SQL query while using @periodStart and @periodEnd placeholders for parameters of type 'timestamp' for computing KPI for specific period."
        sql_stmt=self.llm.struct_query(sys_msg,user_msg,SQLStatement)
        sql_decoded_stmt=self.decode_aliases(sql_stmt.sql_text,self.org_info['org_uid'])
        self.mngDB.create_or_update_obj("kpi",
                              {"kpi_uid":kpi_uid,
                               "sql_alias_text":sql_text(sql_stmt.sql_text),
                               "sql_text":sql_text(sql_decoded_stmt),
                               #"sql_group_columns":sql_text(json.dumps(sql_stmt.recommended_grouping_columns)),
                               #"sql_assumptions":sql_text(json.dumps(sql_stmt.data_assumptions)),
                               })    
           
    def decode_aliases(self,sql_text,org_uid):
        sql_text=sql_text.replace("\n"," " ).lower()
        tables=self.mngDB.get_org_tables(org_uid)
        for table in tables:
            sql_text=sql_text.replace(table['table_alias'].lower(),table['table_name'].lower())
            cols=self.mngDB.get_table_columns(table['table_uid'])
            for c in cols:sql_text=sql_text.replace(c['col_alias'].lower(),c['col_name'].lower())
        return  sql_text

        
  