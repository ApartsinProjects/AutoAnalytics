from llmAgent import LLMAgent
from mngDB import MngDB,sql_text
from pydantic import BaseModel
from schemeAnnotator import TableMetadata
from schemePrompt import SchemePrompt
import json,re

def replace_vars(bs,src_var, dst_var):
    m= re.search(f"(\W|^){src_var}(\W|$)",bs )
    while m is not None:
        prefix=bs[:m.span()[0]] if m.span()[0] else ""
        suffix=bs[m.span()[1]:] if m.span()[1]<len(bs) else ""
        bs=prefix+bs[m.span()[0]:m.span()[1]].replace(src_var,dst_var)+suffix
        m= re.search(f"(\W|^){src_var}(\W|$)",bs )
    return bs

class ColumnSpecification(BaseModel):
    table_name: str
    column_name: str
    
class SQLImplementation(BaseModel):
    sql_statement: str
    grouping_columns: list[ColumnSpecification]
    input_columns:list[ColumnSpecification]
    is_implementation_feasible:bool
    
class SQLGen:
    def __init__(self):
        self.llm=LLMAgent()
        self.mngDB=MngDB()
        self.tables=None
        self.cols=None
        
    def generate_kpis_sql(self,user_uid):
        self.user_info,self.org_info,tasks=self.mngDB.describe_user(user_uid)
        user_kpis=self.mngDB.get_user_kpis_ids(user_uid)
        
        self.tables=self.mngDB.get_org_tables(self.user_info['user_org_uid'])
        self.cols={table['table_uid']:self.mngDB.get_table_columns(table['table_uid']) for table in self.tables}
             
        sys_msg= sys_msg=f"you are a senior MySQL  developer responsible for implementing SQL statements for computing KPIs based on KPI's specification and\
            the following description of the available database tables and columns:{SchemePrompt().get_rich_schema_prompt(self.user_info['user_org_uid'])}"
       
        for kpi_uid in user_kpis: self.generate_kpi_sql(sys_msg,kpi_uid)
            
    def generate_kpi_sql(self,sys_msg,kpi_uid):
        kpi=self.mngDB.get_obj("kpi", kpi_uid)
       
        user_msg=f"Based on the database description above and the following KPI specification:'{kpi['kpi_name']}',identify all relevant input columns required for computing the KPI.\
            Identify all relevant grouping columns or a grouping column combination in the database for computing the KPI.\
                Decide if it's feasible to implement SQL statement given the described data data.\
                    If feasible, generate the required SQL query for the KPI. \
                        Use @periodStart and @periodEnd as user-defined variables in the statement for defining the aggregation period"
            
        sql_impl=self.llm.struct_query(sys_msg,user_msg,SQLImplementation)
        sql_decoded_stmt=self.decode_sql_aliases(sql_impl.sql_statement)
        self.mngDB.create_or_update_obj("kpi",
                              {"kpi_uid":kpi_uid,
                               "sql_alias_stmt":sql_text(sql_impl.sql_statement),
                               "sql_stmt":sql_text(sql_decoded_stmt),
                               "sql_group_columns":sql_text(json.dumps([c.json() for c in sql_impl.grouping_columns])),
                               "sql_cols":sql_text(json.dumps([c.json() for c in sql_impl.input_columns])),
                               "sql_is_feasible": "true" if sql_impl.is_implementation_feasible else "false"
                               })    
           
    def decode_sql_aliases(self,sql_stmt):
        sql_stmt=sql_stmt.replace("\n"," " )
        for table in self.tables:
            sql_stmt=replace_vars(sql_stmt,table['table_alias'],table['table_name'])
            for c in self.cols[table['table_uid']]:sql_stmt=replace_vars(sql_stmt,c['col_alias'],c['col_name'])
        return  sql_stmt
    
   

        
  