from llmAgent import LLMAgent
from mngDB import MngDB,sql_text
from pydantic import BaseModel
from schemeAnnotator import TableMetadata
import json

class SQLStatement(BaseModel):
    sql_text: str
    grouping_columns: list[str]
    resulting_table:TableMetadata
    data_assumptions: list[str]
    sample_output:list[dict]
    
class SQlGen:
    def __init__(self):
        self.llm=LLMAgent()
        self.mngDB=MngDB()
        
    def generate_kpis_sql(self,user_uid):
        self.user_info,self.org_info,=self.mngDB.describe_user(user_uid)
        self.schema_prompt=self.get_schema_prompt(self.user_info["user_org_uid"])
        user_kpis=self.mngDB.get_user_kpis(user_uid)
        for kpi_uid in user_kpis: self.generate_kpi_sql(kpi_uid)
            
    def generate_kpi_sql(self, kpi_uid):
        kpi=self.mngDB.get_obj("kpi", kpi_uid)
        sys_msg=f"you are a DB designer that need to prepare an SQL statement for computing \
            and visualizing KPI:'{kpi['kpi_name']} based on the following tables and columns: {self.schema_prompt}"
        user_msg=f"generate SQL query while using @periodStart and @periodEnd placeholders for parameters of type 'timestamp'.\
            Describe the columns of the resulting table. If it makes sense to compute KPI based on some grouping column,\
                use @groupColumn placeholder for the name of the grouping column with value 'all' for no grouping.\
                    Generate a table of sample output as list of row dictionaries. Additionally, list all assumptions about input data formats and content. "
        sql_stmt=self.llm.struct_query(sys_msg,user_msg,SQLStatement)
        self.mngDB.create_or_update_obj("kpi",
                              {"kpi_uid":kpi_uid,
                               "sql_text":sql_text(sql_stmt.sql_text),
                               "sql_output_scheme":sql_text(json.dumps(sql_stmt.resulting_table.model_dump(mode="json"))),
                               "sql_group_columns":sql_text(json.dumps(sql_stmt.grouping_columns)),
                               "sql_assumptions":sql_text(json.dumps(sql_stmt.data_assumptions)),
                               "sql_sample_output":sql_text(json.dumps(sql_stmt.sample_output)),
                               })

        
  