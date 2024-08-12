from sqlStore import SQLStore
from baseAgent import BaseAgent
from pydantic import BaseModel
import copy,logging


#example use case fro synthetic data generation
use_cases={
    "eduction":{"dbname":"acmeCollege", "org":"college in US", "application":"Student Information System","platform":"PostgreSQL"},
    "transportation":{"dbname":"acmeBus", "org":"public transportation bus company", "application":"telematics solution","platform":"PostgreSQL"},
    "ecommerce": {"dbname":"acmePharm", "org":"online pharmacy", "application":"CRM and inventory management system","platform":"PostgreSQL"}       
}

from schema import DataScheme

class DBGen:
    def __init__(self,db_info):
        self.store=SQLStore().connect()
        self.llm=BaseAgent()
        self.db_info=copy.deepcopy(db_info)
        
    def generate_db(self,overwrite=True):
        self.store.create_db(self.db_info['dbname'],overwrite=overwrite)
        sys_msg=f"You are a software architect designing a data store of application:'{self. db_info['application']}' \
            for customer:{self.db_info['org']} on  platform:{self.db_info['platform']}"
        user_msg=f"Describe the data scheme including tables names and metadata and table columns and metadata \
            for the data that you system will need to store for enabling various business applications"
        self.ds_scheme=self.llm.struct_query(sys_msg,user_msg,DataScheme)
        logging.info(f"scheme={self.ds_scheme}")
        return self.create_tables()
        
    def create_tables(self):
        self.store.connect(self.db_info['dbname'])
        for  t in self.ds_scheme.tables: self.store.execute(self.create_table_ddl(t))
        
    def create_table_ddl(self,t):
        logging.info(f"creating ddl for table {t}")
        return f"create table {t.table_name} ({','.join([c.ddl() for c in t.table_columns])})"
        