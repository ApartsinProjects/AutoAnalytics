from pydantic import BaseModel # type: ignore
import logging
from dataSource import DataSource
from llmAgent import LLMAgent
from mngDB import MngDB
from schemePrompt import SchemePrompt

class ColumnMetadata(BaseModel):
    column_name: str 
    column_type: str
    column_units: str
    column_description: str
    column_alias: str
    column_annotation_justification:str
    def ddl(self): return f"{self.column_name} {self.column_type}"
    def display(self): print(f"\t{self.column_name:20}\t{self.column_type:10}\t{self.column_units:10}\t{self.column_description}")
    
class TableMetadata(BaseModel):
    table_name: str
    table_alias: str
    table_description: str
    table_columns: list[ColumnMetadata]
    table_annotation_justification:str
    
class DataScheme(BaseModel):
    tables:list[TableMetadata]
    def display(self):
        for t in self.tables:
            print(f"\n>>>> Table name: {t.table_name} , Description:{t.table_description}")
            print(f"\t{'name':20}\t{'type':10}\t{'units':10}\tdescription")
            for c in t.table_columns: c.display()
            
    
def collect_key(dict_list, key): return [v[key] for v in dict_list]
def samples_str(dict_list,key): return ",".join([str(v) for v in collect_key(dict_list,key)])
                  
class SchemeAnnotator:
    def __init__(self):
         self.mngDB=MngDB()
         self.llm=LLMAgent()
         self.remote_ds=DataSource()
         
    def fetch_schema(self, org_uid):
        self.mngDB.delete_org_scheme(org_uid)
        org_info=self.mngDB.get_obj("org",org_uid)
        self.remote_ds.connect_str(org_info["org_conn_str"])
        tables=self.remote_ds.fetch_tables()
        tables_info=self.mngDB.create_objs_batch("table",[{'table_name':table,"table_org_uid":org_uid} for table in tables])
        for table in tables_info: self.insert_cols(table,self.remote_ds.fetch_columns(table['table_name']),self.remote_ds.fetch_samples(table['table_name']),org_uid)
            
    def insert_cols(self,table,cols,samples,org_uid):
        col_dict=[{'col_name':c['name'],'col_type':c['type'],"col_table_uid":table['table_uid'],
                   "col_comment":c['comment'],'col_default':c['default'],
                   "col_sample_vals":samples_str(samples,c['name'])} for c in cols]
        return self.mngDB.create_objs_batch("col",col_dict)
    
    def enrich_schema(self,org_uid):
        org_info=self.mngDB.get_obj("org",org_uid)
        scheme_prompt=SchemePrompt().get_schema_prompt(org_info['org_uid'])
        sys_msg=f"You are database developer trying to guess semantics of the data store based on column and table names.\
            You know that the database belong to organization:'{org_info['org_descr']}' and its collected by '{org_info['org_data_app']}'"
        user_msg=f"try to guess useful information about the semantics of tables and columns based on\
            the following basic list fo tables and columns and their types:{scheme_prompt}.\
            Generate descriptions, and meaningful aliases for table and column names based on possible abbreviations and non-English words in their names.\
            Separate descriptive annotation and reasoning on why your guesses are reasonable"
        data_scheme=self.llm.struct_query(sys_msg,user_msg,DataScheme)
        for table in data_scheme.tables: self.update_scheme(table,org_uid)
    
    def update_scheme(self,table,org_uid):
        table_info={"table_org_uid":org_uid, "table_name":table.table_name,"table_alias":table.table_alias,
                    "table_desc":table.table_description,"table_desc_justification":table.table_annotation_justification}
        table_info=self.mngDB.find_update_obj("table",f"table_name='{table.table_name}' and table_org_uid='{org_uid}'",table_info)
        for col in table.table_columns:
            col_info={"col_name":col.column_name,"col_units":col.column_units,"col_descr":col.column_description,
                      "col_alias":col.column_alias,"col_descr_justification":col.column_annotation_justification,"col_table_uid":table_info['table_uid']}
            col_info=self.mngDB.find_update_obj("col",f"col_name='{col.column_name}' and col_table_uid='{table['table_uid']}'",col_info)