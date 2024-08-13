from dataSource import DataSource
from llmAgent import LLMAgent
import copy,logging
from schemeAnnotator import DataScheme

#example use case fro synthetic data generation
use_cases={
    "eduction":{"dbname":"acmecollege", "org":"college in US", "application":"Student Information System","platform":"MySQL"},
    "transportation":{"dbname":"acmebus", "org":"public transportation bus company", "application":"telematics solution","platform":"MySQL"},
    "ecommerce": {"dbname":"acmepharm", "org":"online pharmacy", "application":"CRM and inventory management system","platform":"MySQL"}       
}

class DBGen:
    def __init__(self,db_info=use_cases["ecommerce"]):
        self.store=DataSource().connect()
        self.llm=LLMAgent()
        self.db_info=copy.deepcopy(db_info)
        
    def generate_db(self,overwrite=True):
        self.store.create_db(self.db_info['dbname'],overwrite=overwrite)
        sys_msg=f"You are a software architect designing a data store of application:'{self. db_info['application']}' \
            for customer:{self.db_info['org']} on  platform:{self.db_info['platform']}"
        user_msg=f"Describe the data scheme including tables names and metadata and table columns and metadata \
            for the data that you system will need to store for enabling various business applications"
        self.ds_scheme=self.llm.struct_query(sys_msg,user_msg,DataScheme)
        return self.create_tables().store.close()
        
    def create_tables(self):
        self.store.connect(self.db_info['dbname'])
        for  t in self.ds_scheme.tables: 
            ddl=f"create table {t.table_name} ({','.join([c.ddl() for c in t.table_columns])})"
            self.store.execute(ddl)
        return self
        