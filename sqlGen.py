from llmAgent import LLMAgent
from mngDB import MngDB,sql_text
from pydantic import BaseModel
from schemePrompt import SchemePrompt
from sqlChecker import SQLChecker
import json,re,logging
from datetime import datetime

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
    
class SQLFixedQuery(BaseModel):
    fixed_sql_statement: str
    identified_bug:str
    suggested_fix_description: str
    
    
class SQLGen:
    def __init__(self):
        self.llm=LLMAgent()
        self.mngDB=MngDB()
        self.tables=None
        self.cols=None
        
    def prepare_source(self,org_id):
        self.tables=self.mngDB.get_org_tables(org_id)
        self.cols={table['table_uid']:self.mngDB.get_table_columns(table['table_uid']) for table in self.tables}
        
    def generate_kpis_sql(self,user_uid):
        self.user_info,self.org_info,tasks=self.mngDB.describe_user(user_uid)
        self.prepare_source(self.user_info['user_org_uid'])
        
        sys_msg= sys_msg=f"you are a senior MySQL developer responsible for implementing SQL statements for computing KPIs based on KPI's specification and\
            the following description of the available database tables and columns:{SchemePrompt().get_rich_schema_prompt(self.user_info['user_org_uid'])}"
       
        user_kpis=self.mngDB.get_user_kpis_ids(user_uid)
        for kpi_uid in user_kpis: self.generate_kpi_sql(sys_msg,kpi_uid)
        
    def generate_kpis_sql_raw(self,user_uid):
        self.user_info,self.org_info,tasks=self.mngDB.describe_user(user_uid)
        self.prepare_source(self.user_info['user_org_uid'])
        
        sys_msg= sys_msg=f"you are a senior MySQL developer responsible for implementing SQL statements for computing KPIs based on KPI's specification and\
            the following description of the available database tables and columns:{SchemePrompt().get_annotated_schema_prompt(self.user_info['user_org_uid'])}"
       
        user_kpis=self.mngDB.get_user_kpis_ids(user_uid)
        for kpi_uid in user_kpis: self.generate_kpi_sql_raw(sys_msg,kpi_uid)
            
    def generate_kpi_sql_raw(self,sys_msg,kpi_uid): #no alias statement
        kpi=self.mngDB.get_obj("kpi", kpi_uid)
       
        user_msg=f"Based on the database description above and the following KPI specification:'{kpi['kpi_name']}',identify all relevant input columns required for computing the KPI.\
            Identify all relevant grouping columns or a grouping column combination in the database for computing the KPI.\
                Decide if it's feasible to implement SQL statement given the described data data.\
                    If feasible, generate the required SQL query for the KPI. \
                        Use @periodStart and @periodEnd as user-defined variables in the statement for defining the aggregation period."
            
        sql_impl=self.llm.struct_query(sys_msg,user_msg,SQLImplementation)
        self.mngDB.create_or_update_obj("kpi",
                              {"kpi_uid":kpi_uid,
                               #"sql_alias_stmt":sql_text(sql_impl.sql_statement),
                               "sql_stmt":sql_text(sql_impl.sql_statement),
                               "sql_group_columns":sql_text(json.dumps([c.json() for c in sql_impl.grouping_columns])),
                               "sql_cols":sql_text(json.dumps([c.json() for c in sql_impl.input_columns])),
                               "sql_is_feasible": "true" if sql_impl.is_implementation_feasible else "false"
                               })    
        
    def generate_kpi_sql(self,sys_msg,kpi_uid):
        kpi=self.mngDB.get_obj("kpi", kpi_uid)
       
        user_msg=f"Based on the database description above and the following KPI specification:'{kpi['kpi_name']}',identify all relevant input columns required for computing the KPI.\
            Identify all relevant grouping columns or a grouping column combination in the database for computing the KPI.\
                Decide if it's feasible to implement SQL statement given the described data data.\
                    If feasible, generate the required SQL query for the KPI. \
                        Use @periodStart and @periodEnd as user-defined variables in the statement for defining the aggregation period."
            
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
            sql_stmt=replace_vars(sql_stmt,table['table_alias'],f"`{table['table_name']}`")
            for c in self.cols[table['table_uid']]:sql_stmt=replace_vars(sql_stmt,c['col_alias'],f"`{c['col_name']}`")
        return  sql_stmt
    
    def attempt_fix_sqls(self,user_uid):
        self.user_info=self.mngDB.get_obj("user",user_uid)
        self.prepare_source(self.user_info['user_org_uid'])
        sys_msg=f"You are experienced MySQL developer that need to debug SQL queries for the database defined by the following columns and tables:[{SchemePrompt().get_annotated_schema_prompt(self.user_info['user_org_uid'])}]"
        error_kpis=self.mngDB.store.fetchall(f"select kpis.* from kpis join tasks on kpis.kpi_task_uid=tasks.task_uid where tasks.task_user_uid='{user_uid}' and kpis.sql_passed=False")
        sqlChecker=SQLChecker().prepare_test_round(user_uid)
        for kpi in error_kpis: self.debug_sql(sys_msg,kpi,sqlChecker)
        
    def update_fixed_sql(self, kpi_uid, new_stmt,new_test_stmt,new_res):
        logging.info(f"fixed SQL statement for kpi={kpi_uid}")
        if len(new_res)>10: new_res=new_res[:10]
        self.mngDB.update_obj("kpi",{   "kpi_uid":kpi_uid,"sql_error":"OK","sql_passed":"true","sql_fixed":"true",
                                        "sql_stmt":sql_text(new_stmt),
                                        "sql_test_stmt":sql_text(new_test_stmt),
                                        "sql_test_time":f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                        "sql_results_raw":sql_text(json.dumps(new_res,default=str))})
        
    def debug_sql(self,sys_msg,kpi,checker,max_attempts=3):
        last_stmt,last_error=kpi['sql_stmt'],kpi['sql_error']
        last_test_stmt,last_res=None,None    
        left_attempts=max_attempts
        while (last_error is not None) and (left_attempts>0):
            left_attempts-=1
            user_msg=f"Identify a bug in the sql statement:{last_stmt} for computing:'{kpi['kpi_name']}' that resulted in error:'{last_error}'\
            Identify a bug, describe a fix and generate a fixed version of the sql statement above.\
                        Use @periodStart and @periodEnd as user-defined variables in the statement for defining the aggregation period."
            last_stmt=self.llm.struct_query(sys_msg,user_msg,SQLFixedQuery).fixed_sql_statement
            last_test_stmt, last_res, last_error=checker.test_kpi_info({**kpi,**{'sql_stmt':last_stmt}})
            if last_error is None: 
                logging.info(f"after {max_attempts-left_attempts} fixed sql for kpi:{kpi['kpi_uid']} with original error {kpi['sql_error']}")
                self.update_fixed_sql(kpi['kpi_uid'],last_stmt, last_test_stmt,last_res)
                break
            
        if last_error: logging.info(f"after {max_attempts-left_attempts} for kpi:{kpi['kpi_uid']} error remains {kpi['sql_error']}")
        return last_error==None
                                    
           
            
                
        
                                                   
        
        
        
        
        
    
   

        
  