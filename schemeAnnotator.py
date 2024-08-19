from pydantic import BaseModel # type: ignore
import logging,json
from dataSource import DataSource,db_name
from llmAgent import LLMAgent
from mngDB import MngDB,sql_text
from schemePrompt import SchemePrompt

class ColumnMetadata(BaseModel):
    original_column_name: str #make it a key so there is no choice
    column_type: str
    column_units: str
    column_description: str
    column_alias: str
    column_annotation_justification:str
    def ddl(self): return f"{self.original_column_name} {self.column_type}"
    def display(self): print(f"\t{self.original_column_name:20}\t{self.column_type:10}\t{self.column_units:10}\t{self.column_description}")
    
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
            
class DBContentSummary(BaseModel):
    db_summary: str
    db_entities: list[str]
    db_relations: list[str]
    db_data_gaps:str
            
    
def collect_key(dict_list, key): return [v[key] for v in dict_list] if dict_list else []
def samples_str(dict_list,key): return ",".join([str(v) for v in collect_key(dict_list,key)]) if dict_list else None
def alias_col_wrap(col_name): return col_name.replace(" ","_")
                  
class SchemeAnnotator:
    def __init__(self):
         self.mngDB=MngDB()
         self.llm=LLMAgent()
         self.remote_ds=DataSource()
    
    def prepare_schema(self,org_uid, num_col_samples=3):
        self.fetch_schema(org_uid,num_col_samples)
        self.enrich_schema(org_uid)
        self.summarize_scheme(org_uid)
         
    def fetch_schema(self, org_uid,num_cols_samples=3):
        self.mngDB.del_org_scheme(org_uid)
        self.remote_ds.connect_str(self.mngDB.get_org_conn_str(org_uid))
        tables_info=self.fetch_save_tables(org_uid)
        for table in tables_info: self.fetch_save_cols(table,num_cols_samples)
            
    def fetch_save_tables(self,org_uid):
        return self.mngDB.insert_org_tables(org_uid,
            [{'table_name':db_name(table),
              "table_pkeys":self.remote_ds.fetch_table_pkeys(table),
              "table_fkeys":self.remote_ds.fetch_table_fkeys(table)} 
            for table in self.remote_ds.fetch_tables()])
        
    def fetch_save_cols(self,table,num_col_samples=3):
        samples=self.remote_ds.fetch_col_samples(table['table_name'],num_samples=num_col_samples)
        return self.mngDB.insert_table_cols(table['table_uid'],
            [{'col_name':db_name(c['name']),
              'col_type':str(c['type']),
              "col_comment":c['comment'],
              "col_sample_vals":samples_str(samples,c['name'])} 
            for c in self.remote_ds.fetch_table_cols(table['table_name'])])
    
    def summarize_scheme(self,org_uid):
        org_info=self.mngDB.get_org(org_uid)
        scheme_prompt=SchemePrompt().get_rich_schema_prompt(org_uid)
        sys_msg=f"you are investigating the content of the database in organization:'{org_info['org_descr']}' produced by the system:'{org_info['org_data_app']}'"
        user_msg=f"You have received the following description of the database's tables and columns:[{scheme_prompt}]. Summarize the content of the database in plain English\
            while mentioning major entities, relations and entity attributes represented by the database. Also describe data gaps- content that is not present in the database but might be helpful for the organization"
        data_summary=self.llm.struct_query(sys_msg,user_msg,DBContentSummary)
        self.mngDB.update_org(org_uid,
            { "data_summary":data_summary.db_summary, 
            "data_relations":data_summary.db_relations,
            "data_entities":data_summary.db_entities, 
            "data_gaps":data_summary.db_data_gaps})

    def enrich_schema(self,org_uid):
        org_info=self.mngDB.get_org(org_uid)
        scheme_prompt=SchemePrompt().get_schema_prompt(org_uid)
        sys_msg=f"You are database developer trying to guess semantics of the data store based on column and table names.\
            You know that the database belong to organization:'{org_info['org_descr']}' and its collected by '{org_info['org_data_app']}'"
        user_msg=f"try to guess useful information about the semantics of tables and columns based on\
            the following basic list fo tables and columns and their types:{scheme_prompt}.\
                Generate descriptions and longer meaningful English alias names for the original table and column names.\
                    Separate descriptive annotation and reasoning on why your guesses are reasonable"
        data_scheme=self.llm.struct_query(sys_msg,user_msg,DataScheme)
        for table in data_scheme.tables: self.update_table_scheme(table,org_uid)
    
    def update_table_scheme(self,table,org_uid):
        table_info=self.mngDB.update_org_table_by_name(org_uid, 
            {"table_name":db_name(table.table_name),
            "table_alias":table.table_alias,
            "table_desc":table.table_description,
            "table_desc_justification":table.table_annotation_justification})
    
        for col in table.table_columns:
            self.mngDB.update_table_col_by_name(table_info['table_uid'],
                {"col_name":db_name(col.original_column_name),
                "col_units":col.column_units,
                "col_desc":col.column_description,
                "col_alias":col.column_alias,
                "col_desc_justification":col.column_annotation_justification})